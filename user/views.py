from django.shortcuts import render
from spyne import Application, rpc, ServiceBase, Unicode, Fault, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()

import requests
from django.http import JsonResponse

SOAP_URL = "/user/soap/"  # Your SOAP endpoint

def process_soap_request(payload):
    headers = {'Content-Type': 'text/xml'}
    response = requests.post(SOAP_URL, data=payload, headers=headers)
    return response

def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        payload = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:usr="project.user">
                <soapenv:Header/>
                <soapenv:Body>
                    <usr:register_user>
                        <username>{username}</username>
                        <email>{email}</email>
                        <password>{password}</password>
                        <role>{role}</role>
                    </usr:register_user>
                </soapenv:Body>
            </soapenv:Envelope>
        """

        response = process_soap_request(payload)
        if response.ok:
            return JsonResponse({"message": "Registration successful!"})
        return JsonResponse({"message": "Registration failed!"}, status=400)

    return render(request, 'user/register.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        payload = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:usr="project.user">
                <soapenv:Header/>
                <soapenv:Body>
                    <usr:login_user>
                        <username>{username}</username>
                        <password>{password}</password>
                    </usr:login_user>
                </soapenv:Body>
            </soapenv:Envelope>
        """

        response = process_soap_request(payload)
        if response.ok:
            return JsonResponse({"message": "Login successful!"})
        return JsonResponse({"message": "Invalid credentials!"}, status=400)

    return render(request, 'user/login.html')


class UserData(ComplexModel):
    username = Unicode
    email = Unicode
    role = Unicode
    redirect_path = Unicode  # Add a field for the redirection path


class UserService(ServiceBase):


    @rpc(Unicode, Unicode, Unicode, Unicode, _returns=Unicode)
    def register_user(ctx, username, email, password, role):
        """
        Register a user with roles 'manager' or 'employee'.
        """
        try:
            # Validate email format
            validate_email(email)

            # Validate role
            VALID_ROLES = ["manager", "employee"]
            if role not in VALID_ROLES:
                raise Fault(faultcode="Client", faultstring=f"Invalid role. Valid roles are: {', '.join(VALID_ROLES)}")

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,  # Use the role provided in the request
            )
            return f"User {username} registered successfully with role {role}!"
        except IntegrityError:
            raise Fault(faultcode="Client", faultstring="Username or email already exists.")
        except ValidationError as e:
            raise Fault(faultcode="Client", faultstring=f"Invalid email: {str(e)}")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring="An unexpected error occurred.")

    @rpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def register_admin(ctx, username, email, password):
        """
        Register an admin user. This is a separate function for admin registration.
        """
        try:
            # Validate email format
            validate_email(email)

            # Create the admin user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="admin",  # Set the role to admin for this method
            )
            return f"Admin {username} registered successfully!"
        except IntegrityError:
            raise Fault(faultcode="Client", faultstring="Username or email already exists.")
        except ValidationError as e:
            raise Fault(faultcode="Client", faultstring=f"Invalid email: {str(e)}")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring="An unexpected error occurred.")

    @rpc(Unicode, Unicode, _returns=UserData)
    def login_user(ctx, username, password):
        """
        Login user and return role-specific redirect path.
        """
        user = authenticate(username=username, password=password)
        if user:
            # Define redirect paths based on user role
            REDIRECT_PATHS = {
                "employee": "/dashboard/employee",
                "manager": "/dashboard/manager",
                "admin": "/dashboard/admin",
            }

            role = user.role
            redirect_path = REDIRECT_PATHS.get(role, "/dashboard")  # Default path if role not mapped
            return UserData(username=user.username, email=user.email, role=role, redirect_path=redirect_path)

        raise Fault(faultcode="Client", faultstring="Invalid credentials")


# SOAP Application
soap_app = Application(
    [UserService],
    tns="project.user",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
django_soap_app = csrf_exempt(DjangoApplication(soap_app))
