from __future__ import annotations
import os, math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List
from core.interfaces import Segment, ASR

def _transcribe_span(wav_path: str, start_s: float, end_s: float, model_name: str) -> list[Segment]:
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name)
    # Note: faster-whisper doesn't support seek/duration directly; we can slice via ffmpeg temp file if needed.
    # For simplicity, decode whole file and filter here (acceptable for demo), or implement slicing in production.
    segs, _ = model.transcribe(wav_path, vad_filter=True, beam_size=5)
    out = []
    for s in segs:
        if s.start >= start_s and s.end <= end_s:
            out.append({"start_s": float(s.start), "end_s": float(s.end), "text": s.text.strip()})
    return out

class WhisperASRChunked(ASR):
    def __init__(self, model_name: str = "large-v3", chunk_seconds: int = 600, max_workers: int = 2):
        self.model_name = model_name
        self.chunk_seconds = chunk_seconds
        self.max_workers = max_workers

    def transcribe(self, audio: Path) -> Iterable[Segment]:
        try:
            import soundfile as sf
        except Exception as e:
            raise RuntimeError("Install soundfile for duration computation: pip install soundfile") from e
        f = sf.SoundFile(str(audio))
        total_s = len(f) / f.samplerate
        spans = [(float(i), float(min(i+self.chunk_seconds, total_s))) for i in range(0, math.ceil(total_s), self.chunk_seconds)]
        out: List[Segment] = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as ex:
            futs = [ex.submit(_transcribe_span, str(audio), s, e, self.model_name) for s, e in spans]
            for fut in as_completed(futs):
                out.extend(fut.result())
        return sorted(out, key=lambda x: x["start_s"])
