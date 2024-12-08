from django.shortcuts import render
import requests
from spyne import Application, rpc, ServiceBase, Unicode, Fault, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from django.http import JsonResponse
from .complexTypes import User as ComplexUser

# Constants
SOAP_URL = "/user/soap/"  # Your SOAP endpoint
VALID_ROLES = ["manager", "employee", "admin"]  # Valid roles for registration

User = get_user_model()

# Validator function
def validate_user(user: ComplexUser):
    """Validate user input."""
    # Validate email
    try:
        validate_email(user.email)
    except ValidationError:
        raise Fault(faultcode="Client", faultstring="Invalid email format.")

    # Validate role
    if user.role not in VALID_ROLES:
        raise Fault(faultcode="Client", faultstring=f"Invalid role. Valid roles: {', '.join(VALID_ROLES)}")

    # Ensure first name and last name are provided (Django default fields)
    if not user.first_name or not user.last_name:
        raise Fault(faultcode="Client", faultstring="First name and last name are required.")
    
    return user

def process_soap_request(payload):
    """Helper function to send SOAP request."""
    headers = {'Content-Type': 'text/xml'}
    response = requests.post(SOAP_URL, data=payload, headers=headers)
    return response

def register_view(request):
    """View to register a user via SOAP."""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        payload = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:usr="project.user">
                <soapenv:Header/>
                <soapenv:Body>
                    <usr:register_user>
                        <username>{username}</username>
                        <email>{email}</email>
                        <password>{password}</password>
                        <role>{role}</role>
                        <first_name>{first_name}</first_name>
                        <last_name>{last_name}</last_name>
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
    """View to handle user login via SOAP."""
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

class UserService(ServiceBase):
    """SOAP Service for user-related actions."""

    @rpc(ComplexUser, _returns=Unicode)
    def register_user(self, user: ComplexUser):
        """Register a new user."""
        try:
            validate_user(user)  # Validate user input

            usr = User.objects.create(
                username=user.username,
                email=user.email,
                password=make_password(user.password),
                role=user.role,
                first_name=user.first_name,
                last_name=user.last_name
            )
            return f"User {user.username} registered successfully with role {user.role}!"
        except IntegrityError:
            raise Fault(faultcode="Client", faultstring="Username or email already exists.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring=str(e))

    @rpc(ComplexUser, _returns=Unicode)
    def register_admin(self, user: ComplexUser):
        """Register an admin user."""
        try:
            validate_user(user)  # Validate user input

            # Set is_staff for admin users
            user_obj = User.objects.create_user(
                username=user.username,
                email=user.email,
                password=user.password,
                role="admin",  # Admin role
                first_name=user.first_name,
                last_name=user.last_name,
                is_staff=True  # Admin should have staff privileges
            )
            user_obj.save()
            return f"Admin {user.username} registered successfully!"
        except IntegrityError:
            raise Fault(faultcode="Client", faultstring="Username or email already exists.")
        except Exception as e:
            raise Fault(faultcode="Server", faultstring="An unexpected error occurred.")

    @rpc(ComplexUser, _returns=ComplexUser)
    def login_user(self, user: ComplexUser):
        """Login user and return role-specific redirect path."""
        user_obj = authenticate(username=user.username, password=user.password)
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
            usr = User.objects.get(username=user.username)
            usr.email = user.email
            usr.password = make_password(user.password)
            usr.role = user.role
            usr.first_name = user.first_name
            usr.last_name = user.last_name
            usr.save()
            return ComplexUser(username=usr.username, email=usr.email, role=usr.role, first_name=usr.first_name, last_name=usr.last_name)
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"User {user.username} does not exist.")

# SOAP Application Setup
soap_app = Application(
    [UserService],
    tns="project.user",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

# Django Soap App with CSRF exemption
django_soap_app = csrf_exempt(DjangoApplication(soap_app))
