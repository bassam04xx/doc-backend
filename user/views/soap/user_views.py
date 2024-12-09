from spyne import Application, rpc, ServiceBase, Unicode, Fault, Integer
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import  ObjectDoesNotExist
from django.db import IntegrityError
from user.complexTypes import User as ComplexUser
from user.services.user_services import UserService
from spyne.model.primitive import AnyDict  
from user.validators import validate_user, validate_credentials

VALID_ROLES = ["manager", "employee"]  

User = get_user_model()

user_service = UserService()


class UserSOAPService(ServiceBase):
    @rpc(ComplexUser, _returns=Unicode)
    def register_user(self, user: ComplexUser):
        try:
            validate_user(user)  
            new_user = user_service.create_user(user)
            return f"User {user.username} registered successfully with role {user.role}!"
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))
        

    @rpc(ComplexUser, _returns=Unicode)
    def register_admin(self, user: ComplexUser):
        try:
            validate_credentials(user)
            user.role = "admin"
            new_user = user_service.create_user(user)
            return f"Admin {user.username} registered successfully!"
        except IntegrityError:
            raise Fault(faultcode="Client", faultstring="Username or email already exists.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring="An unexpected error occurred.")


    @rpc(Unicode,Unicode, _returns=ComplexUser)
    def login_user(self, username, password):
        """Login user and return role-specific redirect path."""
        user_obj = authenticate(username=username, password=password)
        if user_obj:
            # Define redirect paths for different roles
            redirect_paths = {
                "employee": "/dashboard/employee",
                "manager": "/dashboard/manager",
                "admin": "/dashboard/admin",
            }
            redirect_path = redirect_paths.get(user_obj.role, "/dashboard")

            return ComplexUser(username=user_obj.username, email=user_obj.email, role=user_obj.role, redirect_path=redirect_path)
        raise Fault(faultcode="Client", faultstring="Invalid credentials")

    @rpc(ComplexUser, _returns=ComplexUser)
    def update_user(self, user: ComplexUser):
        """Update user details."""
        try:
            validate_user(user)  # Validate user input
            updated_user = user_service.update_user(user)
            return updated_user
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User {user.username} does not exist.")

    @rpc(ComplexUser, _returns=ComplexUser)
    def update_admin(self, user: ComplexUser):
        try:
            validate_credentials(user)
            updated_user = user_service.update_user(user)
            return updated_user
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User {user.username} does not exist.")

    @rpc(Integer, AnyDict, _returns=ComplexUser)  # Specify the types
    def patch_user(self, userId: int, updated_data: dict):
        try:
            updated_user = user_service.patch_user(userId, updated_data)
            return updated_user
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User with ID {userId} does not exist.")
    # Todo validate userId is admin
    @rpc(int, _returns=None)
    def delete_user(self, userId: int):
        try:
            user_service.delete_user(userId)
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User with ID {userId} does not exist.")
        
    

# SOAP Application Setup
soap_app = Application(
    [UserSOAPService],
    tns="project.user",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

# Django Soap App with CSRF exemption
django_soap_app = csrf_exempt(DjangoApplication(soap_app))
