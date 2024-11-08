import json
from datetime import datetime, date, time
from uuid import UUID
from decimal import Decimal
from enum import Enum
from dataclasses import is_dataclass, asdict

def customJsonSerializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    if isinstance(obj, time):
        return obj.isoformat()
    
    if isinstance(obj, UUID):
        return str(obj)
    
    if isinstance(obj, Decimal):
        return float(obj)
    
    if isinstance(obj, Enum):
        return obj.value
    
    if isinstance(obj, set):
        return list(obj)
    
    if is_dataclass(obj):
        return asdict(obj) # type: ignore
    
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    
    if hasattr(obj, 'toDict'):
        return obj.toDict()
    
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# Usage example:
# json.dumps(your_object, default=customJsonSerializer)