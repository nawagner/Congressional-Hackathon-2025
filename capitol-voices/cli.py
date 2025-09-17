import typer
from pipelines.runner import run_pipeline

app = typer.Typer(help="CapitolVoices CLI")

@app.command()
def run(hearing_id: str, audio_path: str):
    """Run the full pipeline on an audio file."""
    run_pipeline(hearing_id, audio_path)

@app.command()
def version():
    import sys, platform
    print("Python", sys.version)
    print("Platform", platform.platform())

if __name__ == '__main__':
    app()
