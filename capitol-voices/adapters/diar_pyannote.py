from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, List
from core.interfaces import Segment, Diarizer

class PyannoteDiarizer(Diarizer):
    def __init__(self, hf_token: str | None = None):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")

    def diarize(self, audio: Path) -> Iterable[Segment]:
        try:
            from pyannote.audio import Pipeline
        except Exception as e:
            raise RuntimeError("Missing pyannote.audio. Install deps and set HF_TOKEN.") from e
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=self.hf_token)
        diarization = pipeline(str(audio))
        out: List[Segment] = []
        for turn, _, spk in diarization.itertracks(yield_label=True):
            out.append({"start_s": float(turn.start), "end_s": float(turn.end), "speaker_key": spk, "text": ""})
        return out
