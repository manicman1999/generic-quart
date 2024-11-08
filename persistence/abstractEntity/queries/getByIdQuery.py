from typing import Type, TypeVar
from uuid import UUID
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.domainError.domainError import DomainError
from domain.utility.mongoHelpers import serialize
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar("T", bound=AbstractEntity)


@serviceErrorHandling
async def GetByIdQuery(type: Type[T], id: UUID) -> Option[T]:
    collection = getDb()[type.getCollectionName()]
    query = {"_id": {"$eq": id}}
    cursor = collection.find(query).limit(1)

    async for document in cursor:
        return Option(type.fromDict(document))

    return Option.Error(DomainError("GetByIdQuery", f"Couldn't find {type.__name__} by id."))
