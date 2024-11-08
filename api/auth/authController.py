import asyncio
from datetime import timedelta
from typing import Any, Optional
from quart import request
from quart_jwt_extended import create_access_token
from api.abstractEntity.abstractController import AbstractController
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.abstractEntity.authEntity import Auth
from domain.domainError.domainError import DomainError
from domain.option.option import Option
from domain.utility.userProvider import UserIdentity, UserProvider
from services.auth.authService import AuthService


class AuthController(AbstractController[Auth]):
    def __init__(self):
        super().__init__(Auth)
        self.routePrefix = "/auth"
        self.controllerName = "AuthController"
        self.defineRoutes()

    def defineRoutes(self):
        @self.controllerRoute(
            "/login", methods=["POST"], jwtOptional=True, entityType=Auth
        )
        async def login(auth: Auth) -> Option[Any]:
            userOption = await AuthService.authenticate(auth.username, auth.password)
            if userOption.isError():
                await asyncio.sleep(5.0)
            user = userOption.valueOrThrow()

            accessToken = create_access_token(
                identity=UserIdentity(user.id, user.roles).toDict(),
                expires_delta=False,
            )
            return Option({"access_token": accessToken, "user": user.toDict()})

        @self.controllerRoute("/context", methods=["GET"])
        async def getContext() -> Option[UserIdentity]:
            userIdentity: Optional[UserIdentity] = UserProvider.identity()
            if userIdentity is not None:
                return Option(userIdentity)
            else:
                return Option.Error(
                    DomainError(
                        "AuthController-GetContext-E01", "No JWT identity found."
                    )
                )
