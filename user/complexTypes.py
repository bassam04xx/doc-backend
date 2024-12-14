from spyne import ComplexModel, Unicode
from spyne.model.enum import Enum


# RoleEnum = Enum("admin", "manager", "employee", type_name="RoleEnum")


class User(ComplexModel):
    username = Unicode
    email = Unicode
    password = Unicode
    role = Unicode
    first_name = Unicode
    last_name = Unicode
