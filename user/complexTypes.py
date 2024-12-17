from spyne import ComplexModel, Unicode, Integer, Boolean
from spyne.model.enum import Enum


# Enum for roles
# class RoleEnum(Enum):
#     ADMIN = "admin"
#     MANAGER = "manager"
#     EMPLOYEE = "employee"


# class ManagerTypeEnum(Enum):
#     RH = "rh"
#     FINANCE = "finance"
#     REPORTING = "reporting"

class MySoapHeaders(ComplexModel):
    __namespace__ = "project.user.headers"
    authorization = Unicode  # Token or other authorization information


class User(ComplexModel):
    id = Integer(required=False)
    username = Unicode
    email = Unicode
    password = Unicode
    role = Unicode
    first_name = Unicode
    last_name = Unicode
    manager_type = Unicode
    is_active = Boolean(required=False)
    is_superuser = Boolean(required=False)
    is_staff = Boolean(required=False)
