from dataclasses import dataclass
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    get_type_hints,
)
from quart import Blueprint, request

from api.auth.roleChecking import verifyRoles
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.abstractEntity.baseEntity import BaseEntity
from domain.domainError.domainError import DomainError
from domain.domainError.domainErrorException import DomainErrorException
from domain.option.option import Option
from domain.utility.errorHandling import apiErrorHandling
from quart_jwt_extended import jwt_required

T = TypeVar("T", bound=AbstractEntity)
R = TypeVar("R", bound=BaseEntity)
V = TypeVar("V")


@dataclass
class RouteConfig(BaseEntity):
    prefix: str
    rule: str
    methods: list[str]
    requiredRoles: list[str]
    jwtOptional: bool
    inputTemplate: Optional[dict[Any, Any]]
    inputType: Optional[str]
    outputType: Optional[str]


class AbstractController(Generic[T]):
    entityType: Type[T]
    blueprint: Blueprint
    routePrefix: str
    controllerName: str
    routeRegistry: List[RouteConfig]

    def __init__(self, entityType: Type[T]):
        self.entityType = entityType
        self.blueprint = Blueprint(f"{entityType.__name__}Routes", __name__)
        self.routePrefix = entityType.getRoutePrefix()
        self.controllerName = f"{entityType.__name__}Controller"
        self.routeRegistry = []

    def addRoute(
        self,
        rule: str,
        endpoint: str,
        view_func: Callable[..., Awaitable[Any]],
        **options: Any,
    ) -> None:
        full_rule = self.routePrefix + rule
        self.blueprint.add_url_rule(full_rule, endpoint, view_func, **options)

    async def deserializeEntity(self, entityType: Type[R]) -> R:
        entityData = await request.json
        if entityData is None:
            raise DomainErrorException(
                DomainError(
                    f"{self.controllerName}-E01",
                    f"Could not deserialize {entityType}.",
                    status=400,
                )
            )
        return entityType.fromDict(entityData)

    async def handleRequest(
        self,
        f: Callable[..., Awaitable[Option[V]]],
        entity: Optional[R],
        *args,
        **kwargs,
    ):
        # Get URL query parameters
        url_params = request.args.to_dict()
        
        if entity is not None:
            result = await f(entity, *args, **kwargs, **url_params)
        else:
            result = await f(*args, **kwargs, **url_params)
        return result.okOrNotFound()

    def createDecoratedFunction(
        self,
        f: Callable[..., Awaitable[Option[V]]],
        jwtOptional: bool,
        requiredRoles: list,
        entityType: Optional[Type[R]],
    ):
        @wraps(f)
        @apiErrorHandling
        @verifyRoles(requiredRoles)
        async def decoratedFunction(*args, **kwargs):
            entity = None
            if entityType:
                entity = await self.deserializeEntity(entityType)
            return await self.handleRequest(f, entity, *args, **kwargs)

        if not jwtOptional:
            decoratedFunction = jwt_required(decoratedFunction)

        return decoratedFunction

    def controllerRoute(
        self,
        rule: str,
        *requiredRoles,
        methods: list[str] = ["GET"],
        jwtOptional=False,
        entityType: Optional[Type[R]] = None,
        **options: Any,
    ):
        def decorator(f: Callable[..., Awaitable[Option[V]]]):
            decoratedFunction = self.createDecoratedFunction(
                f, jwtOptional, list(requiredRoles), entityType
            )
            # Add to the blueprint
            self.addRoute(
                rule, f.__name__, decoratedFunction, methods=methods, **options
            )

            # Add to the registry
            # Extract the return type
            typeHints = get_type_hints(f)
            returnType = typeHints.get('return')
            
            outputTypeString = None
            
            if returnType:
                # Unwrap Awaitable and Optional
                if hasattr(returnType, '__args__'):
                    try:
                        outputType = returnType.__args__[0]
                    
                        if hasattr(outputType, '__args__'):
                            outputTypeString = f"{outputType.__name__}[{outputType.__args__[0].__name__}]"
                        else:
                            outputTypeString = outputType.__name__
                    except Exception as e:
                        print(e)
                    
            inputTemplate = (
                entityType.getTemplate(True) if entityType is not None else None
            )
            routeConfig = RouteConfig(
                prefix=self.routePrefix,
                rule=rule,
                methods=methods,
                requiredRoles=list(requiredRoles),
                jwtOptional=jwtOptional,
                inputTemplate=inputTemplate,
                inputType=entityType.__name__ if entityType is not None else None,
                outputType=outputTypeString
            )
            self.routeRegistry.append(routeConfig)

            return decoratedFunction

        return decorator
