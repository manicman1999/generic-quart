from domain.domainError.domainError import DomainError
from domain.option.option import Option
from domain.users.user import User
from domain.utility.auth import checkPassword
from domain.utility.errorHandling import serviceErrorHandling
from services.users.userService import UserService


class AuthService:
    @classmethod
    @serviceErrorHandling
    async def authenticate(cls, username: str, password: str) -> Option[User]:
        userOption = await UserService.getUserByUsername(username)
        user = userOption.valueOrThrow()
        passwordCheck = checkPassword(password + user.salt, user.password)
        if passwordCheck:
            return Option(user)
        else:
            return Option.Error(
                DomainError(
                    "AuthService-Authenticate-E02", "Invalid credentials", status=401
                )
            )
