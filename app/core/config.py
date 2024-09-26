import json
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS", "serviceAccountKey.json"
    )
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    def load_firebase_credentials(self) -> dict:
        """load firebase credentials from the json file"""
        try:
            with open(self.FIREBASE_CREDENTIALS_PATH, "r") as f:
                credentials = json.load(f)
            return credentials
        except FileNotFoundError:
            raise Exception("firebase credentials file is not found")
        except json.JSONDecodeError:
            raise Exception(f"error decoding JSON in {self.FIREBASE_CREDENTIALS_PATH}")


settings = Settings()
firebase_credentials = settings.load_firebase_credentials()
