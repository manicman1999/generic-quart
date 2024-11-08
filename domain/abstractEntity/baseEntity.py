from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Union, get_args, get_origin
from uuid import UUID

from domain.utility.stringExtension import isUUID


@dataclass
class BaseEntity:

    def handleValue(self, fieldValue, safedate: bool):
        fieldValue = self.handleEnum(fieldValue)
        if isinstance(
            fieldValue, type
        ):  # Check if the field value is a type, which should specifically be skipped
            return str(fieldValue)
        elif is_dataclass(fieldValue):
            return fieldValue.toDict(safedate)
        elif isinstance(fieldValue, datetime):
            return fieldValue.isoformat() if safedate else fieldValue
        elif isinstance(fieldValue, list):
            return [
                item.toDict(safedate) if is_dataclass(item) else item
                for item in fieldValue
            ]
        else:
            return fieldValue

    def toDict(self, safedate = False):
        result = {}
        excludedFields = []
        for field in fields(self):
            if not hasattr(self, field.name):
                continue
            fieldValue = getattr(self, field.name)
            result[field.name] = self.handleValue(fieldValue, safedate)
        for attrName in dir(self):
            if attrName.startswith("_"):
                continue
            if attrName in excludedFields:
                continue
            if attrName in result:
                continue
            attrValue = getattr(self, attrName)
            if callable(attrValue):
                continue
            if attrName not in result:
                try:
                    result[attrName] = self.handleValue(attrValue, safedate)
                except Exception as e:
                    print(e)
        return result

    @staticmethod
    def handleEnum(value):
        if isinstance(value, Enum):
            return value.value
        return value

    @classmethod
    def fromDict(cls, d: dict):
        fieldTypes = {f.name: f.type for f in fields(cls)}
        kwargs = {}
        for f, expectedType in fieldTypes.items():
            if f in d and d[f] is not None:
                originType = get_origin(expectedType)
                argTypes = get_args(expectedType)

                if originType == Union and type(None) in argTypes:
                    expectedType = next(t for t in argTypes if t is not type(None))

                if expectedType == UUID:
                    try:
                        kwargs[f] = UUID(str(d[f]))
                    except:
                        kwargs[f] = d[f]
                elif expectedType == datetime and isinstance(d[f], str):
                    kwargs[f] = datetime.fromisoformat(d[f])
                elif get_origin(expectedType) == list:
                    elemType = get_args(expectedType)[0]
                    if elemType == UUID:
                        kwargs[f] = [UUID(str(x)) for x in d[f]]
                    elif is_dataclass(elemType):
                        kwargs[f] = [elemType.fromDict(x) for x in d[f]]
                    else:
                        kwargs[f] = d[f]
                elif is_dataclass(expectedType):
                    kwargs[f] = expectedType.fromDict(d[f])
                elif isinstance(expectedType, type) and issubclass(expectedType, Enum):
                    kwargs[f] = expectedType(d[f])
                else:
                    kwargs[f] = d[f]
            else:
                kwargs[f] = None
        instance = cls.__new__(cls)  # Create instance without calling __init__
        for key, value in kwargs.items():
            setattr(instance, key, value)
        return instance

    @classmethod
    def getTemplate(cls, friendly=False):
        template = {}
        for f in fields(cls):
            fieldType = f.type
            fieldName = f.name
            if fieldName in [
                "id",
                "createdDate",
                "createdBy",
                "updatedDate",
                "updatedBy",
            ]:
                continue
            if (
                hasattr(fieldType, "__origin__")
                and fieldType.__origin__ is not None
                and isinstance(fieldType.__origin__, type)
            ):
                if issubclass(fieldType.__origin__, list):
                    innerType = fieldType.__args__[0]
                    if is_dataclass(innerType):
                        template[fieldName] = [innerType.getTemplate(friendly)]
                    else:
                        template[fieldName] = [0 if innerType in {int, float} else ""]
            elif is_dataclass(fieldType):
                template[fieldName] = fieldType.getTemplate(friendly)
            elif fieldType == int:
                template[fieldName] = 0
            elif fieldType == str:
                template[fieldName] = ""
            elif fieldType == float:
                template[fieldName] = 0.0
            elif fieldType == UUID:
                template[fieldName] = str(UUID(int=0)) if friendly else UUID(int=0)
            elif fieldType == datetime:
                template[fieldName] = (
                    datetime(2000, 1, 1, 0, 0, 0, 0).isoformat()
                    if friendly
                    else datetime(2000, 1, 1, 0, 0, 0, 0)
                )
            elif "type" in fieldName.lower() or "enum" in fieldName.lower():
                template[fieldName] = 0
            else:
                template[fieldName] = None
        return template
