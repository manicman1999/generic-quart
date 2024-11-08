from dataclasses import dataclass, fields
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from domain.abstractEntity.baseEntity import BaseEntity
from domain.utility.stringExtension import camelToKebab, lowerFirstLetter, plural
from domain.utility.userProvider import UserProvider


@dataclass
class AbstractEntity(BaseEntity):
    id: UUID
    createdDate: datetime
    createdBy: Optional[UUID]
    updatedDate: datetime
    updatedBy: Optional[UUID]

    @classmethod
    def getCollectionName(cls):
        collection_name = plural(lowerFirstLetter(cls.__name__))
        return collection_name

    @classmethod
    def getRoutePrefix(cls):
        collection_name = "/" + camelToKebab(plural(cls.__name__))
        return collection_name

    def fillInfo(self):
        now = datetime.utcnow()
        userId = UserProvider.userId()
        if self.id is None or self.id == UUID(int=0):
            self.id = uuid4()
        self.createdDate = self.createdDate or now
        self.createdBy = userId
        self.updatedDate = now
        self.updatedBy = userId
        try:
            for field in fields(self):
                fieldValue = getattr(self, field.name)
                if isinstance(fieldValue, AbstractEntity):
                    fieldValue.fillInfo()
                elif isinstance(fieldValue, list) and all(
                    (isinstance(item, AbstractEntity) for item in fieldValue)
                ):
                    for item in fieldValue:
                        item.fillInfo()
        except:
            pass
