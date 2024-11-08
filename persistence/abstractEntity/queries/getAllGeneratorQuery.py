from typing import Type, TypeVar, AsyncGenerator
from domain.abstractEntity.abstractEntity import AbstractEntity
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar("T", bound=AbstractEntity)


@serviceErrorHandling
async def GetAllGeneratorQuery(type: Type[T]) -> Option[AsyncGenerator[T, None]]:
    collection = getDb()[type.getCollectionName()]
    query = {}
    cursor = collection.find(query)

    async def generator() -> AsyncGenerator[T, None]:
        async for document in cursor:
            serialized_object = type.fromDict(document)
            yield serialized_object

    return Option(generator())