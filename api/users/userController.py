from datetime import timedelta
from typing import Any
from uuid import UUID
from api.abstractEntity.abstractController import AbstractController
from domain.DTOs.stringDTO import StringDTO
from domain.domainError.domainErrorException import DomainErrorException
from domain.option.option import Option
from domain.users.user import User
from domain.utility.errorHandling import apiErrorHandling
from quart_jwt_extended import create_access_token
from domain.utility.userProvider import UserIdentity, UserProvider
from services.users.userService import UserService
from quart import request


class UserController(AbstractController[User]):
    def __init__(self):
        super().__init__(User)
        self.defineRoutes()

    def defineRoutes(self):
        @self.controllerRoute("/<string:userId>", methods=["GET"])
        async def getUserById(userId: str) -> Option[User]:
            result = await UserService.getById(UUID(userId))
            return result

        @self.controllerRoute("", methods=["POST"], jwtOptional=True)
        async def createUser() -> Option[Any]:
            # First, make the user.
            userOptional = await UserService.createUser()
            user = userOptional.valueOrThrow()

            # Give them a token
            accessToken = create_access_token(
                identity=UserIdentity(user.id, user.roles).toDict(),
                expires_delta=False,
            )

            return Option({"access_token": accessToken, "user": user.toDict()})
        
        @self.controllerRoute("/verify", methods=["POST"], entityType=User)
        async def verifyUser(user: User) -> Option[User]:
            userId = UserProvider.userId()
            return await UserService.verifyUser(userId, user.email, user.username, user.password)

        @self.controllerRoute("/add-role", "Admin", methods=["POST"])
        async def addUserRole() -> Option[User]:
            data = await request.json
            if data is None:
                raise DomainErrorException.new(
                    "UserController-UpsertUser-E01", "No data given"
                )
            userId = UUID(data["userId"])
            role = data["role"]
            result = await UserService.addRole(userId, role)
            return result
        
        @self.controllerRoute("/resend-code", methods=["POST"])
        async def resendCode() -> Option[bool]:
            userId = UserProvider.userId()
            return await UserService.sendVerificationCode(userId)

        @self.controllerRoute("/verify-email", methods=["POST"], entityType=StringDTO)
        async def verifyEmail(code: StringDTO) -> Option[User]:
            userId = UserProvider.userId()
            return await UserService.verifyEmail(userId, code.value)
        
        @self.controllerRoute("/generate-profile-images", methods=["POST"], entityType=StringDTO)
        async def generateProfileImages(description: StringDTO) -> Option[list[str]]:
            userId = UserProvider.userId()
            return await UserService.generateProfileImages(userId, description.value)
        
        @self.controllerRoute("/set-profile-image", methods=["POST"], entityType=StringDTO)
        async def setProfileImage(imageUrl: StringDTO) -> Option[User]:
            userId = UserProvider.userId()
            return await UserService.setProfileImage(userId, imageUrl.value)