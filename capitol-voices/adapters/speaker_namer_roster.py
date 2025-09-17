from __future__ import annotations
import json, re
from pathlib import Path
from typing import Iterable, List, Dict
from core.interfaces import Segment, SpeakerNamer

ADDR_TOKENS = ("chair", "chairman", "chairwoman", "ranking", "member", "senator", "representative", "mr", "ms", "mrs", "dr")

class RosterSpeakerNamer(SpeakerNamer):
    """Heuristic, roster-aware speaker naming.
    Roster JSON format:
    {
      "hearing_id": "demo-001",
      "chair": {"name": "Rep. Doe", "aliases": ["Chair Doe", "Madam Chair"]},
      "ranking": {"name": "Rep. Smith", "aliases": ["Ranking Member Smith"]},
      "members": ["Rep. A", "Rep. B"],
      "witnesses": ["Dr. X", "Ms. Y"]
    }
    """
    def __init__(self, roster_path: str):
        self.roster_path = roster_path
        self.roster = {}
        p = Path(roster_path)
        if p.exists():
            self.roster = json.loads(p.read_text(encoding="utf-8"))

    def name_speakers(self, hearing_id: str, segments: Iterable[Segment]) -> Iterable[Segment]:
        segs = list(segments)
        roster = self.roster if self.roster.get("hearing_id")==hearing_id or "hearing_id" not in self.roster else self.roster
        # Simple heuristics: first long turn -> Chair; second long turn -> Ranking (if present)
        long = [s for s in segs if len(s.get("text","").split()) > 20]
        if long:
            long[0]["speaker_key"] = roster.get("chair",{}).get("name","Chair")
            if len(long) > 1:
                long[1]["speaker_key"] = roster.get("ranking",{}).get("name","Ranking Member")
        # Addressed forms: "Thank you, Chairwoman ..." set following speaker
        pat = re.compile(r"thank you,?\s+(chair\w+|ranking member|mr\.?\s+\w+|ms\.?\s+\w+)", re.I)
        for i, s in enumerate(segs[:-1]):
            if pat.search(s.get("text","")):
                # next segment likely a different speaker (witness/member)
                if not segs[i+1].get("speaker_key"):
                    segs[i+1]["speaker_key"] = "Witness/Member"
        return segs
