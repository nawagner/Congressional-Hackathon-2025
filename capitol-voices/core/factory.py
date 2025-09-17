from __future__ import annotations
from .settings import AppSettings
from .interfaces import ASR, Diarizer, Merger, SpeakerNamer, Summarizer, Storage
from adapters.asr_whisper_chunked import WhisperASRChunked
from adapters.diar_pyannote import PyannoteDiarizer
from adapters.merger_overlap import OverlapMerger
from adapters.speaker_namer_roster import RosterSpeakerNamer
from adapters.sum_timestamped_llm import TimestampVerifiedSummarizer
from adapters.storage_sqlite import SQLiteStorage

def build_components(cfg: AppSettings):
    asr: ASR = WhisperASRChunked(model_name=cfg.asr_model, chunk_seconds=cfg.chunk_seconds, max_workers=cfg.max_workers)
    diar: Diarizer = PyannoteDiarizer(hf_token=cfg.hf_token)
    merger: Merger = OverlapMerger()
    namer: SpeakerNamer = RosterSpeakerNamer(cfg.roster_path)
    summarizer: Summarizer = TimestampVerifiedSummarizer(mode=cfg.llm_mode, model_name=cfg.llm_model_name)
    storage: Storage = SQLiteStorage(cfg.db_path)
    return asr, diar, merger, namer, summarizer, storage
