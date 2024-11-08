from dataclasses import dataclass

from domain.abstractEntity.baseEntity import BaseEntity


@dataclass
class ImageReturnDTO(BaseEntity):
    imageUrl: str
    imagePrompt: str
