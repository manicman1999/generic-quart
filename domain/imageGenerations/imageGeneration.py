from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
from domain.abstractEntity.abstractEntity import AbstractEntity

@dataclass
class ImageGeneration(AbstractEntity):

    prompt: str
    imageUrl: str

    def __init__(self, prompt: str, imageUrl: str):
        now = datetime.utcnow()
        super().__init__(uuid4(), now, None, now, None)
        self.prompt = prompt
        self.imageUrl = imageUrl