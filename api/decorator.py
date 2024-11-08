from typing import Any, Awaitable, Callable, Optional, Type, TypeVar
from functools import wraps
from quart import request
from quart_jwt_extended import jwt_required
from api.auth.roleChecking import verifyRoles
from domain.abstractEntity.baseEntity import BaseEntity
from domain.domainError.domainError import DomainError
from domain.option.option import Option
from domain.utility.errorHandling import apiErrorHandling

T = TypeVar("T")
R = TypeVar("R", bound=BaseEntity)


def controllerRoute(
    *requiredRoles, jwtOptional=False, entityType: Optional[Type[R]] = None
):
    def outerDecorator(f: Callable[..., Awaitable[Option[T]]]):
        if jwtOptional:

            @wraps(f)
            @apiErrorHandling
            @verifyRoles(list(requiredRoles))
            async def decoratedFunction(*args, **kwargs):
                if entityType:
                    entityData = await request.json
                    if entityData is None:
                        result = Option.Error(
                            DomainError(
                                "ControllerRoute-E01",
                                f"Could not deserialize {entityType}.",
                                status=400,
                            )
                        )
                    else:
                        entity = entityType.fromDict(entityData)
                        result = await f(entity, *args, **kwargs)
                else:
                    result = await f(*args, **kwargs)
                return result.okOrNotFound()

            return decoratedFunction
        else:

            @wraps(f)
            @jwt_required
            @apiErrorHandling
            @verifyRoles(list(requiredRoles))
            async def decoratedFunction(*args, **kwargs):
                if entityType:
                    entityData = await request.json
                    if entityData is None:
                        result = Option.Error(
                            DomainError(
                                "ControllerRoute-E01",
                                f"Could not deserialize {entityType}.",
                                status=400,
                            )
                        )
                    else:
                        entity = entityType.fromDict(entityData)
                        result = await f(entity, *args, **kwargs)
                else:
                    result = await f(*args, **kwargs)
                return result.okOrNotFound()

            return decoratedFunction

    return outerDecorator
