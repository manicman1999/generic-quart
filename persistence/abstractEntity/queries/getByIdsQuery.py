from typing import Type, TypeVar
from uuid import UUID
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.utility.mongoHelpers import serialize
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar("T", bound=AbstractEntity)


@serviceErrorHandling
async def GetByIdsQuery(type: Type[T], ids: list[UUID]) -> Option[list[T]]:
    collection = getDb()[type.getCollectionName()]
    query = {"_id": {"$in": ids}}
    cursor = collection.find(query)

    serialized_objects = []
    async for document in cursor:
        serialized_object = type.fromDict(document)
        serialized_objects.append(serialized_object)

    return Option(serialized_objects)
