from django.urls import path
from .views import django_soap_app

urlpatterns = [
    path('soap/', django_soap_app),
]
