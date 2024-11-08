import asyncio
from datetime import datetime, timedelta
import random
import re
from typing import Type
from uuid import UUID

import httpx
from domain.aIClients.aiClient import AIClient
from domain.domainError.domainError import DomainError
from domain.emailClients.emailClient import EmailClient
from domain.option.option import Option
from domain.users.user import User
from domain.utility.auth import checkPassword, hashPassword
from domain.utility.errorHandling import serviceErrorHandling
from persistence.abstractEntity.commands.upsertByIdCommand import UpsertByIdCommand
from persistence.abstractEntity.queries.getByIdQuery import GetByIdQuery
from persistence.abstractEntity.queries.getByUserIdsQuery import GetByUserIdsQuery
from persistence.users.queries.getUserByEmailQuery import GetUserByEmailQuery
from persistence.users.queries.getUserByUsernameQuery import GetUserByUsernameQuery
from services.abstractService.abstractService import AbstractService


class UserService(AbstractService[User]):
    @classmethod
    def _entityType(cls) -> Type[User]:
        return User

    @classmethod
    @serviceErrorHandling
    async def getUserByUsername(cls, username: str) -> Option[User]:
        return await GetUserByUsernameQuery(username).execute()

    @classmethod
    def ensurePasswordStrength(cls, password: str) -> Option[bool]:
        if len(password) < 8:
            return Option.Error(DomainError("UserService-EnsurePasswordStrength-E01", "Password must be at least 8 characters."))
        if not re.search(r"[A-Z]", password):
            return Option.Error(DomainError("UserService-EnsurePasswordStrength-E02", "Password must contain at least one uppercase letter."))
        if not re.search(r"[a-z]", password):
            return Option.Error(DomainError("UserService-EnsurePasswordStrength-E03", "Password must contain at least one lowercase letter."))
        return Option(True)

    @classmethod
    def validateEmail(cls, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    @classmethod
    @serviceErrorHandling
    async def createUser(cls) -> Option[User]:
        user = User()
        result = await cls.upsert(user)
        user = result.valueOrThrow()

        return result

    @classmethod
    @serviceErrorHandling
    async def verifyUser(cls, userId: UUID, email: str, username: str, password: str) -> Option[User]:
        userOptional = await cls.getUserByUsername(username)
        if userOptional.isSome():
            return Option.Error(
                DomainError("UserService-VerifyUser-E02", "Username taken")
            )

        userOptional = await GetUserByEmailQuery(email)
        if userOptional.isSome():
            return Option.Error(
                DomainError(
                    "UserService-VerifyUser-E05", "Email already in use, please sign in"
                )
            )

        userOptional = await cls.getById(userId)
        user = userOptional.valueOrThrow()

        if user.isVerified or not user.isGuest:
            return Option.Error(
                DomainError("UserService-VerifyUser-E03", "User already signed up.")
            )

        cls.ensurePasswordStrength(password).valueOrThrow()

        if not cls.validateEmail(email):
            return Option.Error(
                DomainError("UserService-VerifyUser-E04", "Invalid email")
            )

        user.email = email
        user.username = username
        user.password = hashPassword(password + user.salt)
        user.isGuest = False

        userOptional = await cls.upsert(user)
        user = userOptional.valueOrThrow()

        # Now, verify the email
        result = await cls.sendVerificationCode(user.id)
        result.valueOrDefault(log=True)

        return Option(user)

    @classmethod
    @serviceErrorHandling
    async def sendVerificationCode(cls, userId: UUID) -> Option[bool]:
        userOptional = await GetByIdQuery(User, userId)
        user = userOptional.valueOrThrow()

        if not cls.validateEmail(user.email):
            return Option.Error(
                DomainError("UserService-SendVerificationCode-E04", "Invalid email")
            )

        if user.isVerified:
            return Option.Error(DomainError("UserService-SendVerificationCode-E02", "User is already verified."))

        if user.verificationSendTime is not None and user.verificationSendTime - datetime.utcnow() < timedelta(minutes=1):
            return Option.Error(DomainError("UserService-SendVerificationCode-E03", "Already sent a code in the last minute."))

        rawCode = f"{str(random.randint(int(1e8), int(1e9-1)))}"
        hashedCode = hashPassword(rawCode + user.salt)

        user.verificationHash = hashedCode
        user.verificationSendTime = datetime.utcnow()

        userOptional = await UpsertByIdCommand(user)
        user = userOptional.valueOrThrow()

        emailResult = await EmailClient().sendEmail(
            subject=f"Generic Verification Code - {rawCode}",
            recipient=user.email,
            body=(
                "<div style='font-family: Arial, sans-serif; color: #1E1E32;'>"
                "<h2 style='color: #393939;'>Your Generic Verification Code</h2>"
                f"<p>Welcome to Generic, {user.username}! Please use the following verification code to complete your sign-up:</p>"
                f"<p style='font-size: 1.5em; font-weight: bold; color: #333;'>{rawCode}</p>"
                "<p>If you didn't request this code, please ignore this email.</p>"
                "<br><p>Thanks,</p>"
                "<p>The Generic Team</p>"
                "</div>"
            ),
        )
        emailResult.valueOrThrow()

        return Option(True)

    @classmethod
    @serviceErrorHandling
    async def verifyEmail(cls, userId: UUID, verificationCode: str) -> Option[User]:
        userOptional = await GetByIdQuery(User, userId)
        user = userOptional.valueOrThrow()

        if user.verificationSendTime is not None and user.verificationSendTime - datetime.utcnow() > timedelta(days=1):
            return Option.Error(DomainError("UserService-VerifyEmail-E03", "Code has expired."))

        if not checkPassword(verificationCode + user.salt, user.verificationHash):
            return Option.Error(
                DomainError("UserService-VerifyEmail-E04", "Invalid code.")
            )

        user.isVerified = True
        result = await UpsertByIdCommand(user)
        user = result.valueOrThrow()

        return Option(user)

    @classmethod
    @serviceErrorHandling
    async def addRole(cls, userId: UUID, role: str) -> Option[User]:
        userOptional = await cls.getById(userId)
        user = userOptional.valueOrThrow()
        if role in user.roles:
            return Option.Error(
                DomainError(
                    "UserService-AddRole-E02", "User already has role.", status=400
                )
            )
        user.roles.append(role)
        return await cls.upsert(user)

    @staticmethod
    async def isValidImage(imageUrl: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.get(str(imageUrl))
            if response.status_code == 200:
                contentType = response.headers.get("Content-Type", "")
                return contentType.startswith("image/")
            return False

    @classmethod
    @serviceErrorHandling
    async def setProfileImage(cls, userId: UUID, imageUrl: str) -> Option[User]:
        userOptional = await cls.getById(userId)
        user = userOptional.valueOrThrow()

        user.profileImageUrl = imageUrl

        return await cls.upsert(user)