"""Geo-Event Context Agent — attaches geopolitical/threat-event context to a region.

Master plan Part 3.2. This is where the fine-tuned model's training shines: it reasons
about regions, actors, modalities and geopolitical context. The agent surfaces exactly
that structured context from the geo-event corpus for the HORUS brain to reason over.
"""

from __future__ import annotations

from agents.base import BaseAgent
from tools.geo_corpus_tool import GeoCorpusTool


class GeoEventAgent(BaseAgent):
    """Region + timeframe -> instability, modalities, target categories, actor references."""

    name = "geo_event"

    def __init__(self) -> None:
        super().__init__(tools=[GeoCorpusTool()])
