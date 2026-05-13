import os
from dotenv import load_dotenv

load_dotenv()

DB_BACKEND: str = os.getenv("DB_BACKEND", "mock")
DB_URL: str = os.getenv("DB_URL", "")
DB_USER: str = os.getenv("DB_USER", "")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
