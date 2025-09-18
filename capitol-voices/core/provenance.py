from __future__ import annotations
import json, os, hashlib, time, subprocess
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

def _git_sha() -> Optional[str]:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        return sha
    except Exception:
        return None

def _hash_file(path: str) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                b = f.read(1<<20)
                if not b: break
                h.update(b)
        return h.hexdigest()
    except Exception:
        return None

@dataclass
class RunMeta:
    run_id: str
    hearing_id: str
    started_at: float
    finished_at: float | None = None
    asr_engine: str | None = None
    asr_model: str | None = None
    diar_engine: str | None = None
    summarizer: str | None = None
    config_json: str | None = None
    git_sha: str | None = None
    audio_sha256: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

def start_run(hearing_id: str, audio_path: str, cfg) -> RunMeta:
    rid = f"{hearing_id}-{int(time.time())}"
    meta = RunMeta(
        run_id=rid,
        hearing_id=hearing_id,
        started_at=time.time(),
        asr_engine=getattr(cfg, "asr_engine", None),
        asr_model=getattr(cfg, "asr_model", None),
        diar_engine=getattr(cfg, "diar_engine", None),
        summarizer=getattr(cfg, "llm_mode", None),
        config_json=getattr(cfg, "__dict__", {}).__str__(),
        git_sha=_git_sha(),
        audio_sha256=_hash_file(audio_path)
    )
    return meta

def finish_run(meta: RunMeta) -> RunMeta:
    meta.finished_at = time.time()
    return meta
