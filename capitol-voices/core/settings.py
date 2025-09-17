from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    asr_engine: str = "whisper"
    asr_model: str = "large-v3"
    diar_engine: str = "pyannote"
    db_path: str = "data/hearings.db"
    artifacts_dir: str = "artifacts"
    hf_token: str | None = None
    log_level: str = "INFO"
    chunk_seconds: int = 600
    max_workers: int =  max(1, __import__('os').cpu_count() or 2) - 1
    roster_path: str = "configs/roster.demo.json"
    llm_mode: str = "extractive"  # or "llm"
    llm_model_name: str = "local-llm"
    
    # PostgreSQL configuration
    storage_engine: str = "sqlite"  # "sqlite" or "postgresql"
    postgresql_connection_string: str = "postgresql://capitol_voices:password@localhost:5432/capitol_voices"
    postgresql_schema: str = "capitol_voices"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
