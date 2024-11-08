from typing import TypeVar
from domain.abstractEntity.abstractEntity import AbstractEntity
from domain.domainError.domainError import DomainError
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

T = TypeVar("T", bound=AbstractEntity)


@serviceErrorHandling
async def UpsertByIdCommand(entity: T) -> Option[T]:
    entity_type = type(entity)
    collection = getDb()[entity_type.getCollectionName()]

    entity.fillInfo()

    query = {"_id": entity.id}
    result = await collection.replace_one(query, entity.toDict(), upsert=True)

    if result.upserted_id or result.matched_count > 0:
        return Option(entity)
    else:
        error = DomainError(
            "UpsertAutoTypingPromptCommand-E01", "Failed to run UpsertAutoTypingPrompt"
        )
        return Option.Error(error)
