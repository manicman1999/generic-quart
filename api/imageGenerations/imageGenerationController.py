from uuid import UUID
from api.abstractEntity.abstractController import AbstractController
from domain.DTOs.stringDTO import StringDTO
from domain.option.option import Option
from domain.imageGenerations.imageGeneration import ImageGeneration
from services.imageGenerations.imageGenerationService import ImageGenerationService

class ImageGenerationController(AbstractController[ImageGeneration]):
    def __init__(self):
        super().__init__(ImageGeneration)
        self.defineRoutes()


    def defineRoutes(self):
        @self.controllerRoute("/<string:imageGenerationId>")
        async def getImageGenerationById(imageGenerationId: str) -> Option[ImageGeneration]:
            result = await ImageGenerationService.getById(UUID(imageGenerationId))
            return result

        @self.controllerRoute("/all")
        async def getAllImageGenerations() -> Option[list[ImageGeneration]]:
            result = await ImageGenerationService.getAll()
            return result


        @self.controllerRoute("/template")
        async def getImageGenerationTemplate():
            result = Option(ImageGeneration.getTemplate())
            return result


        @self.controllerRoute("", "Admin", methods=["POST"], entityType=ImageGeneration)
        async def upsertImageGeneration(imageGeneration: ImageGeneration) -> Option[ImageGeneration]:
            result = await ImageGenerationService.upsert(imageGeneration)
            return result
        
        @self.controllerRoute("/generate", methods=["POST"], entityType=StringDTO)
        async def generateImages(prompt: StringDTO, ratio: str = "1:1", n: int = 3) -> Option[list[ImageGeneration]]:
            return await ImageGenerationService.generateImages(prompt.value, ratio, n)


        @self.controllerRoute("/<string:imageGenerationId>", "Admin", methods=["DELETE"])
        async def deleteImageGeneration(imageGenerationId: str) -> Option[bool]:
            result = await ImageGenerationService.deleteById(UUID(imageGenerationId))
            return result