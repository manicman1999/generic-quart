from typing import TypeVar
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.domainError.domainError import DomainError
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar("T", bound=AbstractEntity)


@serviceErrorHandling
async def AddCommand(entity: T) -> Option[T]:
    entity_type = type(entity)
    collection = getDb()[entity_type.getCollectionName()]

    entity.fillInfo()

    result = await collection.insert_one(entity.toDict())

    if result.acknowledged and result.inserted_id:
        return Option(entity)
    else:
        error = DomainError(
            "UpsertAutoTypingPromptCommand-E01", "Failed to run UpsertAutoTypingPrompt"
        )
        return Option.Error(error)
