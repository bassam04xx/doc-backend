from spyne import ComplexModel, Unicode
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


class User(ComplexModel):
    username = Unicode
    email = Unicode
    password = Unicode
    role = Unicode
    first_name = Unicode
    last_name = Unicode
    manager_type = Unicode
