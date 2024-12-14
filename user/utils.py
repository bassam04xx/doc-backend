import jwt
from django.conf import settings
from datetime import datetime, timedelta


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
