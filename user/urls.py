from django.urls import path
from . import soap_views

urlpatterns = [
    path('soap/', soap_views.UserService.as_view(), name='soap_service'),
]
