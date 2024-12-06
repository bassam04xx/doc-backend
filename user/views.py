from django.http import HttpResponse
from soaplib.core.service import SoapService
from soaplib.core.model import SoapObject
from soaplib.core import Application
from django.shortcuts import render
from .models import User

# Define User data structure for SOAP
class UserData(SoapObject):
    def __init__(self, username=None, email=None, role=None):
        self.username = username
        self.email = email
        self.role = role

# Create a SOAP Service
class UserService(SoapService):

    @soapdoc('register')
    def register_user(self, username, email, password, role):
        """Handles user registration through SOAP"""
        try:
            user = User.objects.create_user(username=username, email=email, password=password, role=role)
            return UserData(username=user.username, email=user.email, role=user.role)
        except Exception as e:
            return f"Error: {str(e)}"

    @soapdoc('login')
    def login_user(self, username, password):
        """Handles user login through SOAP"""
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return UserData(username=user.username, email=user.email, role=user.role)
            else:
                return "Invalid credentials"
        except User.DoesNotExist:
            return "User not found"
