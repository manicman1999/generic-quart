from functools import wraps
from uuid import UUID
from quart_jwt_extended import get_jwt_identity
from domain.domainError.domainError import DomainError
from domain.option.option import Option
from domain.users.userRole import UserRole
from domain.utility.userProvider import UserProvider
from services.users.userService import UserService


def verifyRoles(requiredRoles: list[str]):
    def decorator(f):
        @wraps(f)
        async def decoratedFunction(*args, **kwargs):
            if len(requiredRoles) == 0:
                return await f(*args, **kwargs)
            identity = UserProvider.identity()
            roles = identity.roles if identity is not None else []
            if not any((role in roles for role in requiredRoles)):
                return Option.Error(
                    DomainError(
                        "AuthCheck-E00",
                        "You do not have the required roles for this call.",
                        None,
                        403,
                    )
                ).okOrNotFound()
            return await f(*args, **kwargs)

        return decoratedFunction

    return decorator
