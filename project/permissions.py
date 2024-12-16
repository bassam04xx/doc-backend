from rest_framework.permissions import BasePermission
from user.services.user_services import get_user_role

from rest_framework.permissions import BasePermission
from user.services.user_services import get_user_role
from user.utils import validate_jwt


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return False
        token = token[len("Bearer "):]
        try:
            is_valid = validate_jwt(token)
            return is_valid
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        token = token[len("Bearer "):]
        print(f"Token: {token}")
        user_role = get_user_role(token)
        print(f"Role from token: {user_role}")
        return user_role == 'admin'


class IsManager(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        token = token[len("Bearer "):]
        print(f"Token: {token}")
        user_role = get_user_role(token)
        print(f"Role from token: {user_role}")
        return user_role == 'manager'


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        token = token[len("Bearer "):]
        print(f"Token: {token}")
        user_role = get_user_role(token)
        print(f"Role from token: {user_role}")
        return user_role == 'employee'
