import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    # QDRANT_URL: str = os.getenv("QDRANT_URL")

settings = Settings()
