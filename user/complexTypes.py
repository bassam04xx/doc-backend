from spyne import ComplexModel, Unicode


class User(ComplexModel):
    username = Unicode
    email = Unicode
    password = Unicode
    role = Unicode
    first_name = Unicode  # Django's default first name
    last_name = Unicode  # Django's default last name
