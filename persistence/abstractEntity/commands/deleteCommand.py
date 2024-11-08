from typing import Any, Type, TypeVar
from uuid import UUID
from domain.abstractEntity.abstractEntity import AbstractEntity
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar("T", bound=AbstractEntity)


@serviceErrorHandling
async def DeleteCommand(entity: Any) -> Option[bool]:
    entityType = type(entity)
    collection = getDb()[entityType.getCollectionName()]

    query = {"_id": entity.id}
    result = await collection.delete_one(query)

    return Option(result.deleted_count > 0)


@serviceErrorHandling
async def DeleteAllCommand(entityType: Type) -> Option[bool]:
    collection = getDb()[entityType.getCollectionName()]

    result = await collection.delete_many({})

    return Option(result.deleted_count > 0)

@serviceErrorHandling
async def DeleteManyCommand(entityType: Type, ids: list[UUID]) -> Option[bool]:
    collection = getDb()[entityType.getCollectionName()]

    result = await collection.delete_many({"id": {"$in": ids}})

    return Option(result.deleted_count > 0)
