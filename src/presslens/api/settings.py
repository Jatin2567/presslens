"""Explicit configuration with no credentials or mutation at import time."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    web_dist: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_path=Path(os.getenv("PRESSLENS_DATABASE_PATH", "data/demo/presslens.sqlite")),
            web_dist=Path(os.getenv("WEB_DIST", "apps/web/dist")),
        )
