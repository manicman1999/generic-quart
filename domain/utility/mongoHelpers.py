from typing import Type, List, TypeVar, Union
from pymongo.cursor import Cursor
from pymongo.command_cursor import CommandCursor
from domain.abstractEntity.abstractEntity import AbstractEntity

T = TypeVar("T", bound=AbstractEntity)


def serialize(cursor: Union[Cursor, CommandCursor], cls: Type[T]) -> List[T]:
    docs = list(cursor)
    return [cls.fromDict(doc) for doc in docs]
