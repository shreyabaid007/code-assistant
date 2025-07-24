import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    github_token: str = ""
    max_file_size: int = 100_000  # bytes
    supported_extensions: list = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb',
                                  '.php']
    analysis_model: str = "gpt-4.1"  # Latest coding-focused model
    reasoning_model: str = "o4-mini"  # Latest reasoning model

    class Config:
        env_file = ".env"


settings = Settings()