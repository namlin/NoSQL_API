import os
from dotenv import load_dotenv

load_dotenv()

DB_BACKEND: str = os.getenv("DB_BACKEND", "mock")
NEO4J_URI: str = os.getenv("NEO4J_URI", os.getenv("DB_URL", "bolt://localhost:7687"))
NEO4J_USER: str = os.getenv("NEO4J_USER", os.getenv("DB_USER", "neo4j"))
NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", os.getenv("DB_PASSWORD", ""))