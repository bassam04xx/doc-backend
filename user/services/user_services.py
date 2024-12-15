from django.core.exceptions import ObjectDoesNotExist

from user.utils import generate_jwt
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


def login_user(username, password):
    user = authenticate(username=username, password=password)
    if not user:
        raise Exception("Invalid credentials")
    payload = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    return generate_jwt(payload)


def create_user(user: User) -> User:
    status = True
    if user.role != "employee":
        status = False

    try:
        created_user = User.objects.create_user(
            username=user.username,
            email=user.email,
            password=user.password,
            role=user.role,
            manager_type=user.manager_type,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=status
        )
        return created_user
    except Exception as e:
        raise e


def update_user(user: User) -> User:
    try:
        user.email = user.email
        user.password = user.password
        user.role = user.role
        user.first_name = user.first_name
        user.last_name = user.last_name
        user.save()
        return user
    except Exception as e:
        raise e


def patch_user(user_id: int, updated_data: dict) -> User:
    try:
        user = User.objects.get(id=user_id)
        for key, value in updated_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.save()
        return user
    except ObjectDoesNotExist:
        raise ValueError(f"User with ID {user_id} does not exist.")
    except Exception as e:
        raise e


def delete_user(user_id: int) -> None:
    try:
        user = User.objects.get(id=user_id)
        user.delete()
    except ObjectDoesNotExist:
        raise ValueError(f"User with ID {user_id} does not exist.")
    except Exception as e:
        raise e


def get_all_users() -> list[User]:
    try:
        users = User.objects.all()
        return users
    except Exception as e:
        raise e


def get_users_by_role(role: str) -> list[User]:
    try:
        users = User.objects.filter(role=role)
        return users
    except Exception as e:
        raise e


def get_user_by_id(user_id: int) -> User:
    try:
        user = User.objects.get(id=user_id)
        return user
    except ObjectDoesNotExist:
        raise ValueError(f"User with ID {user_id} does not exist.")
    except Exception as e:
        raise e


def get_user_by_username(username: str) -> User:
    try:
        user = User.objects.get(username=username)
        return user
    except ObjectDoesNotExist:
        raise ValueError(f"User with username {username} does not exist.")
    except Exception as e:
        raise e


def get_user_by_email(email: str) -> User:
    try:
        user = User.objects.get(email=email)
        return user
    except ObjectDoesNotExist:
        raise ValueError(f"User with email {email} does not exist.")
    except Exception as e:
        raise e
