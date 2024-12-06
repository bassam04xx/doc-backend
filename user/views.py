from spyne import Application, rpc, ServiceBase, Unicode, Fault, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from django.db import IntegrityError

User = get_user_model()

class UserData(ComplexModel):
    username = Unicode
    email = Unicode
    role = Unicode

class UserService(ServiceBase):

    @rpc(Unicode, Unicode, Unicode, Unicode, _returns=Unicode)
    def register_user(ctx, username, email, password, role):
        try:
            if role not in dict(User.ROLE_CHOICES):
                raise ValueError(f"Invalid role. Valid roles: {', '.join(dict(User.ROLE_CHOICES))}")
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role=role,
            )
            user.save()
            return f"User {username} registered successfully with role {role}!"
        except IntegrityError:
            return "Error: Username or email already exists."
        except Exception as e:
            return f"Error: {str(e)}"

    @rpc(Unicode, Unicode, _returns=UserData)
    def login_user(ctx, username, password):
        user = authenticate(username=username, password=password)
        if user:
            return UserData(username=user.username, email=user.email, role=user.role)
        raise Fault(faultcode="Client", faultstring="Invalid credentials")

# SOAP Application
soap_app = Application(
    [UserService],
    tns="myproject.user",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
django_soap_app = csrf_exempt(DjangoApplication(soap_app))
