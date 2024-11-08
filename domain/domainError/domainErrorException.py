from typing import Optional
from domain.domainError.domainError import DomainError


class DomainErrorException(Exception):
    domainError: DomainError

    def __init__(self, domainError: DomainError):
        super().__init__(domainError.message)
        self.domainError = domainError

    @classmethod
    def new(cls, errorCode: str, message: str, status: Optional[int] = None):
        domainError = DomainError(errorCode, message, status=status or 400)
        return cls(domainError)

    def __str__(self):
        return self.domainError.__str__()
