from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class DomainError:
    errorCode: str
    message: str
    exception: Optional[Exception]
    status: int

    def __init__(
        self,
        errorCode: str,
        message: str,
        exception: Optional[Exception] = None,
        status: int = 404,
    ):
        self.errorCode = errorCode
        self.message = message
        self.exception = exception
        self.status = status

    def toDict(self):
        return {
            "errorCode": self.errorCode,
            "message": self.message,
            "exception": str(self.exception or ""),
        }

    def __str__(self):
        if self.exception is None:
            return f"{self.errorCode}: {self.message}"
        else:
            return f"{self.errorCode}: {self.message}\nException: {self.exception}"
