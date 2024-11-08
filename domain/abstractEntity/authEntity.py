from dataclasses import dataclass

from domain.abstractEntity.abstractEntity import AbstractEntity


@dataclass
class Auth(AbstractEntity):
    username: str
    password: str
