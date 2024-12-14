from spyne import Fault
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from user.complexTypes import User as ComplexUser

VALID_ROLES = ["manager", "employee"]


def validate_credentials(user: ComplexUser):
    try:
        validate_email(user.email)
    except ValidationError:
        raise Fault(faultcode="Client", faultstring="Invalid email format.")
    if not user.first_name or not user.last_name:
        raise Fault(faultcode="Client", faultstring="First name and last name are required.")
    if not user.password or len(user.password) < 8:
        raise Fault(faultcode="Client", faultstring="Password must be at least 8 characters long.")


def validate_user(user: ComplexUser):
    validate_credentials(user)
    if user.role not in VALID_ROLES:
        raise Fault(faultcode="Client", faultstring=f"Invalid role. Valid roles: {', '.join(VALID_ROLES)}")
