from uuid import UUID
from domain.domainError.domainError import DomainError
from domain.domainError.domainErrorException import DomainErrorException
from domain.option.option import Option
from domain.users.user import User
from domain.utility.errorHandling import serviceErrorHandling
from domain.utility.mongoHelpers import serialize
from persistence.dbClient import getDb


class GetUserByUsernameQuery:
    username: str

    def __init__(self, username: str):
        self.username = username
        self.collection = getDb()["users"]

    @serviceErrorHandling
    async def execute(self) -> Option[User]:
        query = {"username": {"$eq": self.username}}
        cursor = self.collection.find(query)
        users = []
        async for document in cursor:
            serialized_object = User.fromDict(document)
            users.append(serialized_object)

        if len(users) < 1:
            return Option.Error(
                DomainError("GetUsersByUsername-E02", "Could not find user")
            )
        return Option(users[0])
