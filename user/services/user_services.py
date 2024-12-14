from user.models import User
from django.core.exceptions import ObjectDoesNotExist

class UserService:
    def create_user(self, user: User) -> User:
        try :
            created_user = User.objects.create_user(
                username=user.username,
                email=user.email,
                password=user.password,
                role=user.role,
                first_name=user.first_name,
                last_name=user.last_name
                )
            return created_user
        except Exception as e:
            raise e
          
    def get_user_by_id(self, user_id: int) -> User:
        try:
            user = User.objects.get(id=user_id)
            return user
        except ObjectDoesNotExist:
            raise ValueError(f"User with ID {user_id} does not exist.")
        except Exception as e:
            raise e
          
    def get_all_users(self) -> list[User]:
        try:
            users = User.objects.all()
            return users
        except Exception as e:
            raise e
          
    def update_user(self, user: User) -> User:
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
    
    def patch_user(self, user_id: int, updated_data: dict) -> User:
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
          
    def delete_user(self, user_id: int) -> None:
        try:
            user = User.objects.get(id=user_id)
            user.delete()
        except ObjectDoesNotExist:
            raise ValueError(f"User with ID {user_id} does not exist.")
        except Exception as e:
            raise e
            

      