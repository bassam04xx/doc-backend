from spyne import Application, rpc, ServiceBase, Unicode, Fault, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from .complexTypes import User as ComplexUser
from django.db import IntegrityError

from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

class UserService(ServiceBase):
    @rpc(ComplexUser, _returns=Unicode)
    def register_user(self, user: ComplexUser):
        try:
            if user.role not in dict(User.ROLE_CHOICES):
                raise ValueError(f"Invalid role. Valid roles: {', '.join(dict(User.ROLE_CHOICES))}")
            usr = User.objects.create(
                username= user.username,
                email=user.email,
                password=make_password(user.password),
                role=user.role,
            )
            usr.save()
            return f"User {usr.username} registered successfully with role {user.role}!"
        except IntegrityError:
            return "Error: Username or email already exists."
        except Exception as e:
            return f"Error: {str(e)}"

    @rpc(Unicode, Unicode, _returns=ComplexUser)
    def login_user(self, username, password):
        user = authenticate(username=username, password=password)
        if user:
            return ComplexUser(username=user.username, email=user.email, role=user.role)
        raise Fault(faultcode="Client", faultstring="Invalid credentials")
    
    @rpc(ComplexUser, _returns=ComplexUser)
    def update_user(self, user: ComplexUser) -> str:
        try:
            usr = User.objects.get(username=user.username)
            usr.email = user.email
            usr.password = make_password(user.password)
            usr.role = user.role
            usr.save()
            return f"User {user.username} updated successfully with role {user.role}!"
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User {user.username} does not exist.")

# SOAP Application
soap_app = Application(
    [UserService],
    tns="myproject.user",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
django_soap_app = csrf_exempt(DjangoApplication(soap_app))
