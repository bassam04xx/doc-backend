from spyne import Fault
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from user.models import User

VALID_ROLES = ["manager", "employee"]
VALID_MANAGER_TYPES = ["hr", "finance", "reporting"]


def validate_credentials(user: User):
    try:
        validate_email(user.email)
    except ValidationError:
        raise Fault(faultcode="Client", faultstring="Invalid email format.")
    if not user.first_name or not user.last_name:
        raise Fault(faultcode="Client", faultstring="First name and last name are required.")
    if not user.password or len(user.password) < 8:
        raise Fault(faultcode="Client", faultstring="Password must be at least 8 characters long.")
    if user.role == "manager" and not user.manager_type:
        raise Fault(faultcode="Client", faultstring="Manager type must be specified for users with the 'manager' role.")
    if user.role != "manager" and user.manager_type:
        raise Fault(faultcode="Client", faultstring="Only users with the 'manager' role can have a manager type.")


def validate_user(user: User):
    clean_user = user.clean()
    validate_credentials(user)
    if user.role not in VALID_ROLES:
        raise Fault(faultcode="Client", faultstring=f"Invalid role. Valid roles: {', '.join(VALID_ROLES)}")
