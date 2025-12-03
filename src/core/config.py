import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")


# Try to login to Hugging Face if token is provided, but don't fail imports if
# the token or the huggingface_hub package is not available (useful for CI/tests)
token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
try:
    if token:
        try:
            from huggingface_hub import login

            login(token=token)
        except Exception as e:
            logging.warning("Hugging Face login failed: %s", e)
    else:
        logging.info("HUGGINGFACEHUB_API_TOKEN not set; skipping HF login")
except Exception:
    # If huggingface_hub isn't installed, just continue; tests or lint can run.
    logging.info("huggingface_hub module not available; skipping HF login")

settings = Settings()
