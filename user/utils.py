import jwt
from django.conf import settings
from datetime import datetime, timedelta
from user.complexTypes import User as ComplexUser
from user.models import User

from spyne import Fault


def generate_jwt(payload: dict):
    exp = datetime.utcnow() + settings.JWT_ACCESS_TOKEN_LIFETIME
    payload['exp'] = exp
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def validate_jwt(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')


def extract_jwt_from_headers(context):
    try:
        headers = context.transport.req.headers
        auth_header = headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Fault(faultcode="Client", faultstring="Authorization header is missing or invalid.")
        token = auth_header.split(' ')[1]
        return validate_jwt(token)
    except Exception as e:
        raise Fault(faultcode="Client", faultstring=str(e))


def get_redirect_path(user_role):
    redirect_paths = {
        "employee": "/dashboard/employee",
        "manager": "/dashboard/manager",
        "admin": "/dashboard/admin",
    }
    return redirect_paths.get(user_role, "/dashboard")


def complex_user_to_model_user(complex_user: ComplexUser) -> User:
    return User(
        username=complex_user.username,
        email=complex_user.email,
        password=complex_user.password,
        role=complex_user.role,
        first_name=complex_user.first_name,
        last_name=complex_user.last_name,
        manager_type=complex_user.manager_type if complex_user.role == 'manager' else None
    )


def model_user_to_complex_user(user: User):
    return ComplexUser(
        username=user.username,
        email=user.email,
        password=user.password,
        role=user.role,
        manager_type=user.manager_type,
        first_name=user.first_name,
        last_name=user.last_name
    )
