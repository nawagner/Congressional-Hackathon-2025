from __future__ import annotations
from typing import Iterable, Dict, Any
import re
from core.interfaces import Segment, Summarizer

STOP = set("a an the and or but if then with without for from to of on in by is are was were be being been this that these those it its as at we you i he she they them his her their our your not".split())

def _ts(s: float) -> str:
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}"

class TimestampVerifiedError(Exception): ...

class TimestampVerifiedSummarizer(Summarizer):
    """Ensures each bullet references a timestamp span found in source segments.
    mode='extractive' uses in-repo heuristics; mode='llm' is a stub you can connect to your LLM.
    """
    def __init__(self, mode: str = "extractive", model_name: str = "local-llm"):
        self.mode = mode
        self.model_name = model_name

    def _extractive(self, segs: list[Segment]) -> Dict[str, Any]:
        # Rank by term frequency; produce bullets with [HH:MM:SS–HH:MM:SS]
        from collections import Counter, defaultdict
        toks = re.findall(r"[A-Za-z][A-Za-z\-']+", " ".join(s.get("text","") for s in segs).lower())
        toks = [t for t in toks if t not in STOP and len(t) > 2]
        freq = Counter(toks)
        ranked = sorted(segs, key=lambda s: sum(freq.get(t,0) for t in re.findall(r"[A-Za-z][A-Za-z\-']+", s.get("text","").lower()) if t not in STOP), reverse=True)[:10]
        bullets = [f"[{_ts(s['start_s'])}–{_ts(s['end_s'])}] {s.get('text','')}" for s in ranked]
        # per speaker
        by_speaker = defaultdict(list)
        for s in segs:
            by_speaker[s.get("speaker_key","Speaker")].append(s)
        per = []
        for spk, items in by_speaker.items():
            r = sorted(items, key=lambda s: s['start_s'])[:5]
            per.append({"speaker": spk, "points": [f"[{_ts(s['start_s'])}–{_ts(s['end_s'])}] {s.get('text','')}" for s in r]})
        return {"executive": "Unofficial summary with timestamped bullets.", "by_speaker": per, "bullets": bullets}

    def _validate_timestamps(self, segs: list[Segment], bullets: list[str]) -> None:
        def coverable(b: str) -> bool:
            m = re.search(r"\[(\d{2}:\d{2}:\d{2})–(\d{2}:\d{2}:\d{2})\]", b)
            if not m: return False
            import datetime as dt
            def to_s(ts): 
                h,m,s = map(int, ts.split(':')); return h*3600+m*60+s
            bs, be = to_s(m.group(1)), to_s(m.group(2))
            for seg in segs:
                if seg['start_s'] <= bs <= seg['end_s'] or seg['start_s'] <= be <= seg['end_s']:
                    return True
            return False
        for b in bullets:
            if not coverable(b):
                raise TimestampVerifiedError(f"Bullet lacks verifiable timestamp coverage: {b}")

    def summarize(self, segments: Iterable[Segment]) -> Dict[str, Any]:
        segs = list(segments)
        if self.mode == "llm":
            # Stub for external LLM call; ensure formatting with timestamps.
            # result = call_your_llm(...)
            # self._validate_timestamps(segs, result['bullets'])
            # return result
            result = self._extractive(segs)
        else:
            result = self._extractive(segs)
        self._validate_timestamps(segs, result.get("bullets",[]))
        return result
