from rest_framework.permissions import BasePermission
from user.services.user_services import get_user_role
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
       
        token = request.headers.get('Authorization')
        print(f"Token: {token}")
        user_role = get_user_role(token)
        print(f"Role from token: {user_role}")
        return user_role == 'admin'  # or whichever role you are testing



class IsManager(BasePermission):
    def has_permission(self, request, view):
           
            token = request.headers.get('Authorization')
            print(f"Token: {token}")
            user_role = get_user_role(token)
            print(f"Role from token: {user_role}")
            return user_role == 'manager'  # or whichever role you are testing

class IsEmployee(BasePermission):
    def has_permission(self, request, view):
            
            token = request.headers.get('Authorization')
            print(f"Token: {token}")
            user_role = get_user_role(token)
            print(f"Role from token: {user_role}")
            return user_role == 'employee'  # or whichever role you are testing
