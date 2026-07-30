"""Environment variables and app-wide settings."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    cache_path: str = os.getenv("CACHE_PATH", "./cache")


settings = Settings()
