import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    github_token: str = ""
    max_file_size: int = 100_000  # bytes
    supported_extensions: list = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb',
                                  '.php']
    # LLM Settings
    llm_provider: str = "openai"  # "openai" or "ollama"
    analysis_model: str = "gpt-4o-mini"
    reasoning_model: str = "gpt-4o"
    
    # Ollama Settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-coder:6.7b"
    
    # Analysis Settings
    max_analysis_files: int = 10
    max_file_content_chars: int = 5000

    class Config:
        env_file = ".env"


settings = Settings()