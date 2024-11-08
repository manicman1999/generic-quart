from typing import Callable, Iterable, List, TypeVar, Union
from uuid import UUID

from domain.abstractEntity.abstractEntity import AbstractEntity


T = TypeVar("T")
R = TypeVar("R")

A = TypeVar("A", bound=AbstractEntity)


def groupBy(
    lst: list[T], keySelector: Callable[[T], R] = lambda x: x
) -> dict[R, list[T]]:
    output: dict[R, list[T]] = {}
    for item in lst:
        key = keySelector(item)
        if key in output:
            output[key].append(item)
        else:
            output[key] = [item]
    return output


def idDict(lst: list[A]) -> dict[UUID, A]:
    return {item.id: item for item in lst}


def firstOrDefault(lst: Iterable[T], default: R = None) -> Union[T, R]:
    iterator = iter(lst)
    return next(iterator, default)


def intersection(lst1: List[T], lst2: List[T]) -> List[T]:
    return list(set(lst1) & set(lst2))
