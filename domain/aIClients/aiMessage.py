from dataclasses import dataclass
from enum import Enum
from typing import Union

from domain.abstractEntity.baseEntity import BaseEntity

class AIRole(str, Enum):
    Assistant = "assistant"
    User = "user"
    System = "system"

@dataclass
class AIMessage(BaseEntity):
    role: AIRole
    content: str

    def __init__(self, role: Union[AIRole, str], content: str):
        super().__init__()

        self.role = role if isinstance(role, AIRole) else AIRole(role)
        self.content = content

    def oai(self) -> dict[str, str]:
        return {
            "role": str(self.role),
            "content": self.content
        }