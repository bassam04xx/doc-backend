from django.core.exceptions import ObjectDoesNotExist

from user.utils import generate_jwt, validate_jwt
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


def login_user(username, password):
    user = authenticate(username=username, password=password)
    if not user:
        raise Exception("Invalid credentials")
    payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    if user.role == "manager":
        payload["manager_type"] = user.manager_type
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


def get_user_role(token: str) -> str:
    """
    Extract the user role from the JWT token.

    Args:
        token (str): The JWT token.

    Returns:
        str: The user's role.

    Raises:
        Exception: If the token is invalid or the role is not found.
    """
    try:
        payload = validate_jwt(token)
        role = payload.get("role")
        if not role:
            raise Exception("User role not found in the token.")
        if role not in ["employee", "manager", "admin"]:
            raise Exception("Invalid user role.")
        return role
    except Exception as e:
        raise Exception(f"Error extracting user role: {e}")


def get_user_id(token: str) -> int:
    """
    Extract the user ID from the JWT token.

    Args:
        token (str): The JWT token.

    Returns:
        int: The user's ID.

    Raises:
        Exception: If the token is invalid or the user ID is not found.
    """
    try:
        payload = validate_jwt(token)
        user_id = payload.get("id")
        if not user_id:
            raise Exception("User ID not found in the token.")
        return user_id
    except Exception as e:
        raise Exception(f"Error extracting user ID: {e}")


def toggle_account_status(user_id: int) -> User:
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return user
    except ObjectDoesNotExist:
        raise ValueError(f"User with ID {user_id} does not exist.")
    except Exception as e:
        raise e


def get_user_status(user_id: int) -> bool:
    try:
        user = User.objects.get(id=user_id)
        return user.is_active
    except ObjectDoesNotExist:
        raise ValueError(f"User with ID {user_id} does not exist.")
    except Exception as e:
        raise e


def get_user_username(user_id: int) -> str:
    try:
        user = User.objects.get(id=user_id)
        return user.username
    except ObjectDoesNotExist:
        raise ValueError(f"User with ID {user_id} does not exist.")
    except Exception as e:
        raise e
