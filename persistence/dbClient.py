import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class DatabaseClient:
    _instance = None
    _client = None

    @staticmethod
    def getInstance():
        if DatabaseClient._instance is None:
            DatabaseClient._instance = DatabaseClient()
            DatabaseClient._instance._initialize_client()
        return DatabaseClient._instance

    def _initialize_client(self):
        environment = os.getenv("FLASK_ENV", "development")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = int(os.environ.get("DB_PORT", 27017))
        db_user = os.getenv("DB_USER", "admin")
        db_password = os.getenv("DB_PASSWORD", "password")

        if environment == "production":
            ssl_cert_path = "global-bundle.pem"
            self._client = AsyncIOMotorClient(
                f"mongodb://{db_user}:{db_password}@{db_host}:{db_port}/?tls=true&tlsCAFile={ssl_cert_path}&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false",
                uuidRepresentation="standard",
            )
        else:
            self._client = AsyncIOMotorClient(
                f"mongodb://{db_host}:{db_port}/", uuidRepresentation="standard"
            )
        self._db: AsyncIOMotorDatabase = self._client["generic"]

    def getDb(self) -> AsyncIOMotorDatabase:
        return self._db


def getDb():
    instance = DatabaseClient.getInstance()
    db = instance.getDb()
    return db
