from functools import wraps
from quart import jsonify
from domain.domainError.domainError import DomainError
from domain.domainError.domainErrorException import DomainErrorException
from domain.logging.logger import Logger
from domain.option.option import Option


def serviceErrorHandling(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DomainErrorException as de:
            print(f"DomainErrorException caught: {de}")
            return Option.Error(de.domainError)
        except Exception as e:
            funcName = func.__name__
            locationName = "ServiceErrorHandling"
            if args and hasattr(args[0], "__class__"):
                locationName = args[0].__class__.__name__
            error = DomainError(
                f"{locationName}-{funcName}-E00", "Unhandled exception", e
            )
            print(f"Exception caught: {error}")
            return Option.Error(error)

    return wrapper


def apiErrorHandling(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return jsonify(result)
        except DomainErrorException as de:
            Logger.error(de.domainError)
            return (jsonify(de.domainError.toDict()), de.domainError.status)
        except Exception as e:
            funcName = func.__name__
            locationName = "ControllerErrorHandling"
            if args and hasattr(args[0], "__class__"):
                locationName = args[0].__class__.__name__
            error = DomainError(
                f"{locationName}-{funcName}-E00", "Unhandled exception", e
            )
            Logger.error(error)
            return (jsonify(error.toDict()), 500)

    return wrapper
