from django.urls import path
from .views import register_view, login_view
from .views import django_soap_app  # Import the soap app

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('soap/', django_soap_app, name='soap'),  # This line maps /soap/ to the SOAP service
]
