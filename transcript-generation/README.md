## Transcription (OpenAI Whisper)

This project can transcribe audio files to text using OpenAI Whisper via the OpenAI Python SDK.

### Setup

1. Ensure you have an OpenAI API key and set it in your environment:

```bash
export OPENAI_API_KEY="sk-..."
```

2. Install dependencies (using uv or pip):

```bash
# with uv
uv sync

# or with pip
pip install -e .
```

### Usage

Transcribe an audio file to a `.txt` next to the audio:

```bash
python transcribe.py -i path/to/audio.mp3
```

Specify an explicit output path:

```bash
python transcribe.py -i path/to/audio.m4a -o /tmp/result.txt
```

Optional flags:

- `--model` (default: `whisper-1`)
- `--prompt` (optional guidance for the model)
- `--temperature` (default: `0.0`)
- `--language` (e.g., `en`)
- `--no-chunk` (disable automatic chunking)
- `--chunk-seconds` (default: `600` seconds per chunk)
- `--max-chunk-mb` (default: `20` MB per chunk)

The command prints the path to the written transcript file.

### Limits and Chunking

- Whisper API requests have a per-file size limit. This tool automatically chunks large inputs using `ffmpeg` by default.
- Install ffmpeg if you plan to transcribe long recordings:

```bash
brew install ffmpeg
```

- You can tweak `--chunk-seconds` and `--max-chunk-mb` to fit within current API limits. Each chunk is transcribed independently and concatenated.

## YouTube audio extraction

Two simple helpers are available in `youtube_audio.py`:

```python
from youtube_audio import download_audio_to_file, download_audio_to_bytes

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 1) Save MP3 to a specific path (file or directory)
path = download_audio_to_file(url, "/tmp/my-audio.mp3")
print("Saved:", path)

# 2) Get MP3 as bytes (e.g., to upload or process in-memory)
audio_bytes = download_audio_to_bytes(url)
print("Bytes:", len(audio_bytes))
```

Notes:
- `yt-dlp` is used under the hood and requires `ffmpeg` to be available in your system PATH.
- If you pass a directory to `download_audio_to_file`, an `audio.mp3` file will be created inside it.

