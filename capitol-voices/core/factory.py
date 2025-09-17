from __future__ import annotations
from .settings import AppSettings
from .interfaces import ASR, Diarizer, Merger, SpeakerNamer, Summarizer, Storage
from adapters.asr_whisper_chunked import WhisperASRChunked
from adapters.diar_pyannote import PyannoteDiarizer
from adapters.merger_overlap import OverlapMerger
from adapters.speaker_namer_roster import RosterSpeakerNamer
from adapters.sum_timestamped_llm import TimestampVerifiedSummarizer
from adapters.storage_sqlite import SQLiteStorage
from adapters.storage_postgresql import PostgreSQLStorage

def build_components(cfg: AppSettings):
    asr: ASR = WhisperASRChunked(model_name=cfg.asr_model, chunk_seconds=cfg.chunk_seconds, max_workers=cfg.max_workers)
    diar: Diarizer = PyannoteDiarizer(hf_token=cfg.hf_token)
    merger: Merger = OverlapMerger()
    namer: SpeakerNamer = RosterSpeakerNamer(cfg.roster_path)
    summarizer: Summarizer = TimestampVerifiedSummarizer(mode=cfg.llm_mode, model_name=cfg.llm_model_name)
    
    # Choose storage backend based on configuration
    if hasattr(cfg, 'storage_engine') and cfg.storage_engine == 'postgresql':
        storage: Storage = PostgreSQLStorage(
            connection_string=cfg.postgresql_connection_string,
            schema=getattr(cfg, 'postgresql_schema', 'capitol_voices')
        )
    else:
        storage: Storage = SQLiteStorage(cfg.db_path)
    
    return asr, diar, merger, namer, summarizer, storage
