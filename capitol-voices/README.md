# CapitolVoices

Adds **chunked parallel ASR**, **async ingest**, **roster-based speaker naming**, and a **timestamp-verified summarizer** to the Pro scaffold.

## Quick Start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export HF_TOKEN=your_hf_token   # for pyannote
python -c "from pipelines.runner import run_pipeline; run_pipeline('demo-001','data/hearing.wav')"
streamlit run ui/app.py
```

## What’s new
- `adapters/asr_whisper_chunked.py`: process-pool parallel decoding by chunks
- `adapters/speaker_namer_roster.py`: heuristic, roster-aware naming
- `adapters/sum_timestamped_llm.py`: every bullet must cite a verifiable timestamp span
- `pipelines/ingest_async.py`: async downloader example
- `tests/test_timestamp_validator.py`: ensures timestamp verification works
- `configs/roster.demo.json`: sample roster for demo
