from typing import Generic, Type, TypeVar
from uuid import UUID
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.domainError.domainError import DomainError
from domain.utility.errorHandling import serviceErrorHandling
from persistence.abstractEntity.commands.deleteCommand import DeleteCommand
from persistence.abstractEntity.commands.upsertByIdCommand import UpsertByIdCommand
from persistence.abstractEntity.queries.getAllQuery import GetAllQuery
from persistence.abstractEntity.queries.getByIdsQuery import GetByIdsQuery
from domain.option.option import Option

T = TypeVar("T", bound=AbstractEntity)


class AbstractService(Generic[T]):
    entityType: Type[T]

    @classmethod
    def _entityType(cls) -> Type[T]:
        # This method should return the actual type of the entity
        raise NotImplementedError("Must be implemented by subclass")

    @classmethod
    def serviceName(cls) -> str:
        return f"{cls._entityType().__name__}Service"

    @classmethod
    def className(cls) -> str:
        return cls._entityType().__name__

    @classmethod
    @serviceErrorHandling
    async def getByIds(cls, ids: list[UUID]) -> Option[list[T]]:
        return await GetByIdsQuery(cls._entityType(), ids)

    @classmethod
    @serviceErrorHandling
    async def getById(cls, id: UUID) -> Option[T]:
        result = await GetByIdsQuery(cls._entityType(), [id])
        objects = result.valueOrThrow()
        if len(objects) == 0:
            return Option.Error(
                DomainError(
                    f"{cls.serviceName()}-Get{cls.className()}ById-E02",
                    f"Could not find {cls.className()}",
                )
            )
        return Option(objects[0])

    @classmethod
    @serviceErrorHandling
    async def getAll(cls) -> Option[list[T]]:
        return await GetAllQuery(cls._entityType())

    @classmethod
    @serviceErrorHandling
    async def upsert(cls, entity: T) -> Option[T]:
        return await UpsertByIdCommand(entity)

    @classmethod
    @serviceErrorHandling
    async def deleteById(cls, id: UUID) -> Option[bool]:
        entityOptional = await cls.getById(id)
        entity = entityOptional.valueOrThrow()
        return await DeleteCommand(entity)
