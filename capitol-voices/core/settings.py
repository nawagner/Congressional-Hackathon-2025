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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
