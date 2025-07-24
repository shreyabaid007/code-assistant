import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    github_token: str = ""
    max_file_size: int = 100_000  # bytes
    supported_extensions: list = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb',
                                  '.php']
    analysis_model: str = "gpt-4o-mini"  # Cost-optimized model for analysis
    reasoning_model: str = "gpt-4o"  # High-quality model for reasoning
    max_analysis_files: int = 10  # Maximum files to analyze in detail
    max_file_content_chars: int = 5000  # Maximum characters per file for analysis

    class Config:
        env_file = ".env"


settings = Settings()