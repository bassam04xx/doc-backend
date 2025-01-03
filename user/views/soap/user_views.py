from spyne import Application, rpc, ServiceBase, Unicode, Fault, Integer, Iterable
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from user.complexTypes import User as ComplexUser, MySoapHeaders
from user.services.user_services import create_user, get_all_users, get_users_by_role, patch_user, get_user_by_id, \
    update_user, delete_user, login_user, get_user_by_username, get_user_role, toggle_account_status, get_user_status, \
    get_user_username, get_active_users_stats, get_user_role_distribution
from spyne.model.primitive import AnyDict
from user.validators import validate_user
from user.utils import complex_user_to_model_user, model_user_to_complex_user

User = get_user_model()


def check_authorization(headers: MySoapHeaders, required_roles) -> None:
    """
    Validates the authorization header and checks for the required role.
    """
    if not headers or not headers.authorization:
        raise Fault(faultcode="Client.Auth", faultstring="Missing authorization header.")

    # Example: Validate the token and get user role
    token = headers.authorization
    role = get_user_role(token)  # Function to extract role from the token

    if role not in required_roles:
        raise Fault(faultcode="Client.Auth", faultstring=f"Unauthorized. Role '{role}' cannot access this resource.")


class UserSOAPService(ServiceBase):

    @rpc(ComplexUser, _returns=Unicode)
    def register_user(self, complex_user: ComplexUser):
        try:
            model_user = complex_user_to_model_user(complex_user)
            validate_user(model_user)
            new_user = create_user(model_user)
            if new_user.role != "employee":
                return (f"User {model_user.username} registered successfully with role {model_user.role}! Please wait "
                        f"for admin approval.")
            token = login_user(model_user.username, model_user.password)
            return token
        except IntegrityError:
            raise Fault(faultcode="Client", faultstring="Username or email already exists.")
        except Exception as e:
            raise Fault(faultcode="Client", faultstring=str(e))

    @rpc(Unicode, Unicode, _returns=Unicode)
    def login_user(self, username, password):
        try:
            user = get_user_by_username(username)
            if not user.is_active:
                raise Fault(
                    faultcode="Client",
                    faultstring="Your account is not active. Please contact admin."
                )
            return login_user(username, password)
        except Fault as fault:
            raise fault
        except Exception as e:
            raise Fault(faultcode="Client", faultstring=str(e))

    @rpc(ComplexUser, _returns=ComplexUser)
    def update_user(self, complex_user: ComplexUser):
        try:
            model_user = complex_user_to_model_user(complex_user)
            validate_user(model_user)
            updated_user = update_user(model_user)
            token = login_user(updated_user.username, updated_user.password)
            return f"User {updated_user.username} updated successfully! Token: {token}"
        except User.DoesNotExist:
            raise Fault(faultcode="Client", faultstring=f"User {complex_user.username} does not exist.")

    @rpc(Integer, AnyDict, _returns=ComplexUser)
    def patch_user(self, userId: int, updated_data: dict):
        try:
            updated_user = patch_user(userId, updated_data)
            return updated_user
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User with ID {userId} does not exist.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(Integer, _returns=ComplexUser)
    def get_user(self, userId: int):
        try:
            user = get_user_by_id(userId)
            return user
        except User.DoesNotExist:
            raise Fault(faultcode="Client", faultstring=f"User with ID {userId} does not exist.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(MySoapHeaders, _returns=Iterable(ComplexUser))
    def get_all_users(self, headers: MySoapHeaders):
        check_authorization(headers, required_roles=["admin", "manager"])
        try:
            users = get_all_users()
            complex_users = [model_user_to_complex_user(user) for user in users]
            return complex_users
        except Exception as e:
            raise Fault(faultcode="Client", faultstring=str(e))

    @rpc(MySoapHeaders, Unicode, _returns=Iterable(ComplexUser))
    def get_users_by_role(self, headers: MySoapHeaders, role: str):
        check_authorization(headers, required_roles=["admin", "manager"])
        try:
            model_users = get_users_by_role(role)
            complex_users = [model_user_to_complex_user(user) for user in model_users]
            return complex_users
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(MySoapHeaders, Integer, _returns=Unicode)
    def delete_user(self, headers: MySoapHeaders, userId: int):
        check_authorization(headers, required_roles=["admin"])
        try:
            delete_user(userId)
            return f"User with ID {userId} deleted successfully."
        except User.DoesNotExist:
            raise Fault(faultcode="Client", faultstring=f"User with ID {userId} does not exist.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(Unicode, _returns=Unicode)
    def get_user_role(self, token: str):
        try:
            role = get_user_role(token)
            return role
        except Exception as e:
            raise Fault(faultcode="Client", faultstring=str(e))

    @rpc(MySoapHeaders, Integer, _returns=Unicode)
    def toggle_account_status(self, headers: MySoapHeaders, userId: int):
        check_authorization(headers, required_roles=["admin"])
        try:
            toggle_account_status(userId)
            status = {
                True: "active",
                False: "inactive"
            }[get_user_status(userId)]
            username = get_user_username(userId)
            return f"User {username} is now {status}."
        except User.DoesNotExist:
            raise Fault(faultcode="Client", faultstring=f"User with ID {userId} does not exist.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(MySoapHeaders, _returns=AnyDict)
    def get_active_users_stats(self, headers: MySoapHeaders):
        check_authorization(headers, required_roles=["admin"])
        try:
            stats = get_active_users_stats()
            return stats
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(MySoapHeaders, _returns=AnyDict)
    def fetch_user_role_distribution(self, headers: MySoapHeaders):
        """
        Fetch the distribution of users across roles.

        Args:
            headers (MySoapHeaders): The SOAP headers containing the authorization token.

        Returns:
            dict: A dictionary with roles and their respective user counts.
        """
        # Optional: Check authorization
        check_authorization(headers, required_roles=["admin", "manager"])  # Only admins or managers can access

        try:
            distribution = get_user_role_distribution()
            return distribution
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))


soap_app = Application(
    [UserSOAPService],
    tns="project.user",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

django_soap_app = csrf_exempt(DjangoApplication(soap_app))
