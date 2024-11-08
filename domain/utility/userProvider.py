from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from quart_jwt_extended import get_jwt_identity
from domain.abstractEntity.baseEntity import BaseEntity


@dataclass
class UserIdentity(BaseEntity):
    id: UUID
    roles: list[str]


class UserProvider:
    @classmethod
    def identity(cls) -> Optional[UserIdentity]:
        if jwtIdentity := get_jwt_identity():
            return UserIdentity.fromDict(jwtIdentity)
        return None

    @classmethod
    def userId(cls) -> UUID:
        if identity := cls.identity():
            return identity.id
        return UUID(int=0)

    @classmethod
    def userRoles(cls) -> list[str]:
        if identity := cls.identity():
            return identity.roles
        return []

    @classmethod
    def matchOrBypass(cls, userId: UUID, bypassRoles: list[str] = []) -> bool:
        if identity := cls.identity():
            return userId == identity.id or bool(set(identity.roles) & set(bypassRoles))
        return False
