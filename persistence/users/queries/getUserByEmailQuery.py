from typing import Any

from domain.domainError.domainError import DomainError
from domain.users.user import User
from persistence.dbClient import getDb
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

@serviceErrorHandling
async def GetUserByEmailQuery(email: str) -> Option[User]:
    collection = getDb()[User.getCollectionName()]

    query: dict[str, Any] = {"email": email}

    document = await collection.find_one(query)
    if document is None:
        return Option.Error(DomainError("GetUserByEmailQuery-E02", "Could not find user with that email."))
    
    user = User.fromDict(document)
    
    return Option(user)
