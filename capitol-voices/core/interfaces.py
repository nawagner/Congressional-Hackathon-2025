from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Dict, Any, List, Optional, TypedDict

class Segment(TypedDict, total=False):
    hearing_id: str
    start_s: float
    end_s: float
    text: str
    speaker_key: Optional[str]

class ASR(ABC):
    @abstractmethod
    def transcribe(self, audio: Path) -> Iterable[Segment]: ...

class Diarizer(ABC):
    @abstractmethod
    def diarize(self, audio: Path) -> Iterable[Segment]: ...

class Merger(ABC):
    @abstractmethod
    def merge(self, asr: Iterable[Segment], diar: Iterable[Segment]) -> Iterable[Segment]: ...

class SpeakerNamer(ABC):
    @abstractmethod
    def name_speakers(self, hearing_id: str, segments: Iterable[Segment]) -> Iterable[Segment]: ...

class Summarizer(ABC):
    @abstractmethod
    def summarize(self, segments: Iterable[Segment]) -> Dict[str, Any]: ...

class Storage(ABC):
    @abstractmethod
    def write_segments(self, hearing_id: str, segments: Iterable[Segment]) -> None: ...
    @abstractmethod
    def write_summary(self, hearing_id: str, summary: Dict[str, Any]) -> None: ...
    @abstractmethod
    def read_segments(self, hearing_id: str) -> List[Segment]: ...
    @abstractmethod
    def read_summary(self, hearing_id: str) -> Optional[Dict[str, Any]]: ...
