from __future__ import annotations
from pathlib import Path
from core.settings import AppSettings
from core.factory import build_components
from core.provenance import start_run, finish_run

def run_pipeline(hearing_id: str, audio_path: str):
    cfg = AppSettings()
    asr, diar, merger, namer, summarizer, storage = build_components(cfg)
    audio = Path(audio_path)

    # provenance start
    meta = start_run(hearing_id, audio_path, cfg)

    asr_segs = list(asr.transcribe(audio))
    diar_segs = list(diar.diarize(audio))
    merged = list(merger.merge(asr_segs, diar_segs))
    for m in merged:
        m["hearing_id"] = hearing_id
    named = list(namer.name_speakers(hearing_id, merged))
    storage.write_segments(hearing_id, named)
    summary = summarizer.summarize(named)
    storage.write_summary(hearing_id, summary)

    # provenance finish
    meta = finish_run(meta)
    try:
        storage.write_run(meta.to_json())
    except Exception:
        pass

    print(f"Done: {hearing_id} • segments={len(named)}")
