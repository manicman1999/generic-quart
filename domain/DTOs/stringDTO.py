from dataclasses import dataclass

from domain.abstractEntity.baseEntity import BaseEntity


@dataclass
class StringDTO(BaseEntity):
    value: str
