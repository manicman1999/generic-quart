import logging
import traceback
import watchtower
from datetime import datetime
from threading import Lock
import boto3
from botocore.exceptions import ClientError
import os
import json
from typing import Any, Optional, Union

from domain.domainError.domainError import DomainError
from domain.utility.serialization import customJsonSerializer
from domain.utility.userProvider import UserProvider


class Logger:
    _instance = None
    _lock = Lock()

    def __new__(cls, log_level=logging.INFO, log_group=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Logger, cls).__new__(cls)
                    cls._initialize_logger(log_level, log_group)
        return cls._instance

    @classmethod
    def _initialize_logger(cls, log_level, log_group):
        cls._logger = logging.getLogger("GenericLogger")
        cls._logger.setLevel(log_level)

        if not cls._logger.handlers:
            # Determine if we're in production
            is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"

            # Console handler (for non-production)
            if not is_production:
                consoleHandler = logging.StreamHandler()
                consoleHandler.setLevel(log_level)
                formatter = logging.Formatter(
                    "%(message)s"  # Simplified format for console
                )
                consoleHandler.setFormatter(formatter)
                cls._logger.addHandler(consoleHandler)

            # CloudWatch handler (for production)
            if is_production:
                try:
                    # Set up AWS session
                    session = boto3.Session(
                        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-west-2"),
                    )

                    # Create CloudWatch logs client
                    logs_client = session.client("logs")

                    cloudwatchHandler = watchtower.CloudWatchLogHandler(
                        log_group=log_group
                        or os.environ.get("LOG_GROUP", "generic-backend-prod"),
                        stream_name=f'app-{datetime.now().strftime("%Y-%m-%d")}',
                        boto3_client=logs_client,
                        send_interval=20,
                    )
                    cloudwatchHandler.setLevel(log_level)
                    cls._logger.addHandler(cloudwatchHandler)
                except (ClientError, ValueError) as e:
                    print(f"Failed to initialize CloudWatch logging: {e}")
                    # Fallback to console logging if CloudWatch fails
                    consoleHandler = logging.StreamHandler()
                    consoleHandler.setLevel(log_level)
                    formatter = logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                    consoleHandler.setFormatter(formatter)
                    cls._logger.addHandler(consoleHandler)

    @classmethod
    def _getLogger(cls):
        if cls._instance is None:
            cls()
        return cls._logger

    @staticmethod
    def _makeLogData(
        message: str,
        errorCode: str = "",
        exception: Optional[Exception] = None,
        properties: dict[str, Any] = {},
        level: str = "INFO",
    ) -> str:
        dataDict = {
            "errorCode": errorCode,
            "message": message,
            "exception": (
                "".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                )
                if exception is not None
                else ""
            ),
            "level": level,
            "timestamp": datetime.utcnow(),
            "contextUserId": UserProvider.userId(),
        }

        try:
            for key, value in properties.items():
                dataDict[key] = value
        except Exception as e:
            pass

        # Pretty print for local development
        is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"
        if not is_production:
            output_parts = []
            output_parts.append(f"{dataDict['timestamp']} [{level}] {message}")
            
            if errorCode:
                output_parts.append(f"Error Code: {errorCode}")
            if exception is not None:
                output_parts.append(f"Exception: {dataDict['exception']}")
            if properties:
                output_parts.append(f"Properties: {properties}")
            
            return "\n".join(output_parts)
        
        # JSON format for production/CloudWatch
        return json.dumps(dataDict, indent=4, default=customJsonSerializer)

    @classmethod
    def debug(cls, msg: str, properties: dict[str, Any] = {}):
        data = cls._makeLogData(msg, properties=properties, level="DEBUG")
        cls._getLogger().debug(data)

    @classmethod
    def info(cls, msg: str, properties: dict[str, Any] = {}):
        data = cls._makeLogData(msg, properties=properties, level="INFO")
        cls._getLogger().info(data)

    @classmethod
    def warning(cls, errorCode: str, msg: str, properties: dict[str, Any] = {}):
        data = cls._makeLogData(msg, errorCode, properties=properties, level="WARNING")
        cls._getLogger().warning(data)

    # This weird typing union thing is so we can just Logger.error(domainError)
    # It's bad and ugly here, I admit, but it makes it prettier in use
    # Python needs extensions and interfaces
    @classmethod
    def error(
        cls,
        error: Union[str, DomainError],
        msg: str = "",
        properties: dict[str, Any] = {},
    ):
        if isinstance(error, DomainError):
            cls.domainError(error, properties=properties)
            return
        data = cls._makeLogData(msg, error, properties=properties, level="ERROR")
        cls._getLogger().error(data)

    @classmethod
    def domainError(cls, domainError: DomainError, properties: dict[str, Any] = {}):
        data = cls._makeLogData(
            domainError.message,
            domainError.errorCode,
            domainError.exception,
            properties=properties,
            level="INFO",
        )
        cls._getLogger().error(data)
