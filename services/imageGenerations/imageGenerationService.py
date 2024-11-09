import asyncio
from typing import Literal, Type
from domain.aIClients.aiClient import AIClient
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling
from services.abstractService.abstractService import AbstractService

from domain.imageGenerations.imageGeneration import ImageGeneration


class ImageGenerationService(AbstractService[ImageGeneration]):

    @classmethod
    def _entityType(cls) -> Type[ImageGeneration]:
        return ImageGeneration
    
    @classmethod
    @serviceErrorHandling
    async def generateImages(cls, prompt: str, ratio: str, n: int = 3) -> Option[list[ImageGeneration]]:
        aiClient = AIClient()
        imagesOptional = await aiClient.generateImages(prompt, ratio, n) # type: ignore
        imageUrls = imagesOptional.valueOrThrow()

        imageGenerations = [ImageGeneration(prompt, imageUrl) for imageUrl in imageUrls]

        await asyncio.gather(*[cls.upsert(ig) for ig in imageGenerations])

        return Option(imageGenerations)
