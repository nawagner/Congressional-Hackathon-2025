import pytest
from adapters.sum_timestamped_llm import TimestampVerifiedSummarizer, TimestampVerifiedError

def test_summary_bullets_have_verifiable_timestamps():
    segs = [
        dict(start_s=0.0, end_s=5.0, text="Opening statement about budget.", speaker_key="Chair"),
        dict(start_s=60.0, end_s=65.0, text="Question on oversight.", speaker_key="Member"),
    ]
    s = TimestampVerifiedSummarizer(mode="extractive").summarize(segs)
    assert s["bullets"], "Should produce bullets"
    # Negative test: tamper bullet to fail
    bad = s.copy()
    bad["bullets"] = ["[10:10:10–10:10:20] fabricated text"]
    with pytest.raises(TimestampVerifiedError):
        TimestampVerifiedSummarizer()._validate_timestamps(segs, bad["bullets"])
