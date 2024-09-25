import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    API_TOKEN: str = os.getenv("API_TOKEN","")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS","")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET","")
    

settings = Settings()