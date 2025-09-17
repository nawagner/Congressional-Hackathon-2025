# CongressTrack

## Components

- `passed_law_pipeline.py`

  - data pipeline that aggregates data from Congress.gov API, Congress member campaign sites, and runs scoring using an LLM + similarity comparison

- `app.py`
  - streamlit app that showcases the following features
    1. Individual bill analysis and details
    2. Aggregated bill analysis
    3. Congress Member leaderboard

## How to run

### Prerequisites

- Python
- UV
- Setup venv

```sh
uv venv
source .venv/bin/activate
uv sync
```

1. Run the data pipeline to populate the `/data` directory with json data

```sh
python passed_law_pipeline.py
```

2. Run the streamlit app

```sh
streamlit run app.py
```
