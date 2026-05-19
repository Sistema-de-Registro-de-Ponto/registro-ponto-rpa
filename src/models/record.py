from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PunchRecord:
    external_employee_id: str
    employee_name: str
    work_date: str
    check_in_at: str
    check_out_at: str | None
    worked_seconds: int | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "external_employee_id": self.external_employee_id,
            "employee_name": self.employee_name,
            "work_date": self.work_date,
            "check_in_at": self.check_in_at,
            "raw_payload": self.raw_payload,
        }
        if self.check_out_at:
            payload["check_out_at"] = self.check_out_at
        if self.worked_seconds is not None:
            payload["worked_seconds"] = self.worked_seconds
        return payload
