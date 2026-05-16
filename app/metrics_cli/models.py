from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FunctionMetrics:
    file: str
    function: str
    language: str
    cc: int


@dataclass
class MetricsResult:
    files: int = 0
    loc: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: List[FunctionMetrics] = field(default_factory=list)


@dataclass
class CommitMetrics:
    commit: str
    date: str
    author: str
    metrics: Dict[str, Dict[str, float]]
