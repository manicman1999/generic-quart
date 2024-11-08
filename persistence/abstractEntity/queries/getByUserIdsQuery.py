from typing import Type, TypeVar
from uuid import UUID
from domain.abstractEntity.abstractEntity import AbstractEntity
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar('T', bound=AbstractEntity)

# Note that this only works when there's a userId field.

@serviceErrorHandling
async def GetByUserIdsQuery(type: Type[T], userIds: list[UUID]) -> Option[list[T]]:
    collection = getDb()[type.getCollectionName()]
    query = {"userId": {"$in": userIds}}
    cursor = collection.find(query).sort([('createdDate', -1)])

    serialized_objects = []
    async for document in cursor:
        serialized_object = type.fromDict(document)
        serialized_objects.append(serialized_object)

    return Option(serialized_objects)
