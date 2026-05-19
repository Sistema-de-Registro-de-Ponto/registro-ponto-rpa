from __future__ import annotations

import logging

import httpx

from config import Settings
from models.record import PunchRecord

logger = logging.getLogger(__name__)


class RpaApiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._url = f"{settings.api_base_url}/v1/rpa/imports"

    def send_records(self, records: list[PunchRecord]) -> dict:
        if not records:
            raise ValueError("Nenhum registro para importar")

        payload = {
            "source_system": self._settings.source_system,
            "records": [record.to_api_dict() for record in records],
        }

        logger.info("Enviando %s registro(s) para %s", len(records), self._url)

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self._url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Rpa-Api-Key": self._settings.rpa_api_key,
                },
            )

        if response.status_code >= 400:
            logger.error("API respondeu %s: %s", response.status_code, response.text)
            response.raise_for_status()

        data = response.json()
        logger.info("Importação concluída: %s", data)
        return data
