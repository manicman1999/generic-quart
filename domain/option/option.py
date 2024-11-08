from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Optional, Type, TypeVar, Union
from quart import jsonify
from domain.domainError.domainError import DomainError
from domain.domainError.domainErrorException import DomainErrorException
from domain.logging.logger import Logger
from domain.utility.userProvider import UserProvider

T = TypeVar("T")
R = TypeVar("R")

@dataclass
class Option(Generic[T]):
    value: Optional[T]
    error: Optional[DomainError]
    
    def __init__(
        self, value: Optional[T] = None, error: Optional[DomainError] = None
    ) -> None:
        if value is not None and error is not None:
            raise ValueError("Option cannot have both a value and an error")
        self.value: Optional[T] = value
        self.error: Optional[DomainError] = error

    @classmethod
    def Some(cls, value: T) -> Option[T]:
        return cls(value=value, error=None)

    @classmethod
    def Error(cls, error: Optional[DomainError]) -> Option[T]:
        return cls(value=None, error=error)

    def isSome(self) -> bool:
        """Check if the Option has a value."""
        return self.value is not None

    def isError(self) -> bool:
        """Check if the Option has an error."""
        return self.error is not None

    def valueOrThrow(self, errorCode: Optional[str] = None) -> T:
        if self.value is not None:
            return self.value
        elif self.error is not None:
            self.error.errorCode = errorCode or self.error.errorCode
            raise DomainErrorException(self.error)
        raise DomainErrorException.new(
            errorCode or "ErrorHandling-E00", "No error or value provided."
        )

    def valueOrDefault(self, default: R = None, log: bool = False) -> T | R:
        if log and self.value is None and self.error is not None:
            Logger.error(self.error)
        return self.value if self.value is not None else default

    def firstValueOrThrow(
        self, default: Optional[R] = None, errorCode: Optional[str] = None
    ) -> R:
        if self.error is not None:
            raise DomainErrorException(self.error)
        if self.value is None:
            raise DomainErrorException.new(
                errorCode or "ErrorHandling-E00", "No error or value provided."
            )
        if isinstance(self.value, list):
            if len(self.value) > 0:
                return self.value[0]
            elif default is not None:
                return default
            else:
                valueType = type(self.value).__name__
                raise DomainErrorException.new(
                    errorCode or "FirstValueOrThrow-E01",
                    f"{valueType} empty and no default provided.",
                )
        else:
            valueType = type(self.value).__name__
            raise DomainErrorException.new(
                errorCode or "FirstValueOrThrow-E02", f"{valueType} is not a list."
            )

    def okOrNotFound(self, hide=False, status=404):
        if self.value is not None:
            if isinstance(self.value, list):
                if all(hasattr(item, "toDict") for item in self.value):
                    return [item.toDict(True) for item in self.value]  # type: ignore
                else:
                    return self.value
            elif hasattr(self.value, "toDict"):
                return self.value.toDict(True)  # type: ignore
            else:
                return self.value
        raise DomainErrorException(
            self.error or DomainError("Error-E00", "Bad request", None, status)
        )

    def mapResult(self, func: Callable[[T], R]) -> Option[R]:
        if self.value is not None:
            try:
                newValue = func(self.value)
                return Option(newValue)
            except Exception as ex:
                return Option.Error(
                    DomainError(errorCode="MapResult-E00", message=str(ex))
                )
        else:
            return Option.Error(self.error)

    async def amapResult(self, func: Callable[[T], Awaitable[R]]) -> Option[R]:
        if self.value is not None:
            try:
                newValue = await func(self.value)
                return Option(newValue)
            except Exception as ex:
                return Option.Error(
                    DomainError(errorCode="MapResult-E00", message=str(ex))
                )
        else:
            return Option.Error(self.error)
        
    def mapResultOption(self, func: Callable[[T], Option[R]]) -> Option[R]:
        if self.value is not None:
            try:
                return func(self.value)
            except Exception as ex:
                return Option.Error(
                    DomainError(errorCode="MapResult-E00", message=str(ex))
                )
        else:
            return Option.Error(self.error)

    async def amapResultOption(self, func: Callable[[T], Awaitable[Option[R]]]) -> Option[R]:
        if self.value is not None:
            try:
                return await func(self.value)
            except Exception as ex:
                return Option.Error(
                    DomainError(errorCode="MapResult-E00", message=str(ex))
                )
        else:
            return Option.Error(self.error)
