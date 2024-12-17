from spyne.service import ServiceBase
from spyne.decorator import rpc
from spyne.error import Fault

from user.services.user_services import get_user_role


def require_role(allowed_roles):
    def decorator(func):
        def wrapper(self, ctx, *args, **kwargs):
            # Access the Authorization header
            print("ctx.in_header:", ctx)

            headers = ctx.in_header
            if not headers or not headers.Authorization:
                raise Fault(faultcode="Client", faultstring="Authentication required.")

            token = headers.Authorization
            if not token.startswith("Bearer "):
                raise Fault(faultcode="Client", faultstring="Invalid token format.")

            # Validate the token (mock implementation, replace with actual validation)
            role = get_user_role(token[len("Bearer "):])  # Replace with your role validation logic
            if role not in allowed_roles:
                raise Fault(faultcode="Client", faultstring="Permission denied.")

            return func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


