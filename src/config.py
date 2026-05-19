from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    portal_base_url: str
    portal_username: str
    portal_password: str
    api_base_url: str
    rpa_api_key: str
    source_system: str
    headless: bool
    slow_mo_ms: int
    timezone: str
    artifacts_dir: Path

    @classmethod
    def load(cls) -> Settings:
        base = os.getenv("PORTAL_BASE_URL", "http://localhost:5500").rstrip("/")
        return cls(
            portal_base_url=base,
            portal_username=os.getenv("PORTAL_USERNAME", "demo"),
            portal_password=os.getenv("PORTAL_PASSWORD", "demo123"),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8080").rstrip("/"),
            rpa_api_key=os.getenv("RPA_API_KEY", "dev-rpa-key-change-me"),
            source_system=os.getenv("SOURCE_SYSTEM", "ponto_agil"),
            headless=_env_bool("HEADLESS", False),
            slow_mo_ms=int(os.getenv("SLOW_MO_MS", "600")),
            timezone=os.getenv("TIMEZONE", "America/Sao_Paulo"),
            artifacts_dir=_ROOT / "artifacts",
        )


def parse_br_date_to_iso(date_br: str) -> str:
    """Converte DD/MM/AAAA para AAAA-MM-DD."""
    parts = date_br.strip().split("/")
    if len(parts) != 3:
        raise ValueError(f"Data inválida: {date_br}")
    day, month, year = parts
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def build_datetime_iso(work_date_iso: str, time_hhmm: str, tz_name: str) -> str:
    hour, minute = time_hhmm.strip().split(":")
    year, month, day = work_date_iso.split("-")
    dt = datetime(
        int(year),
        int(month),
        int(day),
        int(hour),
        int(minute),
        tzinfo=ZoneInfo(tz_name),
    )
    return dt.isoformat()
