import os
from dotenv import load_dotenv
from huggingface_hub import login

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")

token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if token:
    login(token=token)   
else:
    raise RuntimeError("HUGGINGFACEHUB_API_TOKEN is required")

settings = Settings()
