"""The Subject of inquiry — what a Sentinel job is authorized to assess.

A subject is deliberately narrow and typed: a domain you own, a region+timeframe,
a public organization, or a public threat entity. The subject *type* drives which
agents are relevant (a region subject leans on the Geo-Event agent; a domain subject
leans on the OSINT/Web-Infra agents). See master plan Part 1.2 and Part 3.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


class SubjectType(StrEnum):
    """The kind of thing being assessed. Drives agent relevance and scope checks."""

    DOMAIN = "domain"  # an owned or public web-facing domain
    REGION = "region"  # a geographic region + timeframe (geo-event home turf)
    ORGANIZATION = "org"  # a named public organization
    ENTITY = "entity"  # a public threat actor / infrastructure entity


class Subject(BaseModel):
    """A single, typed subject of inquiry for one Sentinel job."""

    type: SubjectType = Field(..., description="What kind of subject this is.")
    value: str = Field(
        ..., min_length=1, description="The primary identifier (domain, region name, org, entity)."
    )
    # Region subjects carry a timeframe; the geo-event corpus is indexed by year.
    year_from: int | None = Field(
        default=None, ge=1970, le=2100, description="Start year (region subjects)."
    )
    year_to: int | None = Field(
        default=None, ge=1970, le=2100, description="End year (region subjects)."
    )
    country_code: str | None = Field(
        default=None, description="ISO country hint for region/org subjects."
    )

    @model_validator(mode="after")
    def _validate_shape(self) -> Subject:
        if self.type == SubjectType.DOMAIN and not _DOMAIN_RE.match(self.value):
            raise ValueError(f"'{self.value}' is not a valid domain for a DOMAIN subject.")
        if self.type == SubjectType.REGION:
            if self.year_from is None or self.year_to is None:
                raise ValueError("REGION subjects require year_from and year_to.")
            if self.year_from > self.year_to:
                raise ValueError("year_from must be <= year_to.")
        return self

    @property
    def is_domain(self) -> bool:
        return self.type == SubjectType.DOMAIN

    def cache_key(self) -> str:
        """Stable identity for caching/dedup across tools."""
        parts = [self.type.value, self.value.lower()]
        if self.year_from is not None:
            parts.append(f"{self.year_from}-{self.year_to}")
        return ":".join(parts)
