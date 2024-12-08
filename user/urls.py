from django.urls import path
from user.views.soap.user_views import django_soap_app


urlpatterns = [
    # path('register/', register_view, name='register'),
    # path('login/', login_view, name='login'),
    path('soap/', django_soap_app, name='soap'),  # This line maps /soap/ to the SOAP service
]
