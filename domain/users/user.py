from dataclasses import dataclass, field, InitVar
from datetime import datetime
import random
from typing import Optional
from uuid import UUID, uuid4
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.users.userRole import UserRole
from domain.utility.auth import hashPassword


@dataclass
class User(AbstractEntity):
    email: str
    username: str
    password: str
    roles: list[str]
    profileImageUrl: Optional[str]
    salt: str
    verificationHash: str
    verificationSendTime: Optional[datetime]

    isGuest: bool
    isVerified: bool

    def __init__(self):
        now = datetime.utcnow()
        super().__init__(uuid4(), now, None, now, None)

        randomNumber = str(random.randint(100_000_000, 999_999_999))
        self.username = f"user_{randomNumber}"
        self.salt = str(random.randint(100_000_000, 999_999_999))

        randomNumber2 = str(random.randint(100_000_000, 999_999_999))
        self.password = hashPassword(str(randomNumber2) + self.salt)
        self.isGuest = True
        self.isVerified = False
        self.roles = []
        self.email = ""
        self.profileImageUrl = None

    def changePassword(self, newPassword: str):
        self.password = hashPassword(newPassword + self.salt)
