from spyne import ComplexModel, Unicode


class User(ComplexModel):
    username = Unicode
    email = Unicode
    password = Unicode
    role = Unicode
    