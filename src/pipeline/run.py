from __future__ import annotations

import argparse
import json
import logging
import sys

import httpx

from api.client import RpaApiClient
from config import Settings
from portal.ponto_agil import PontoAgilScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("rpa")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RPA Portal Ponto Ágil — scraping e importação para a API",
    )
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Apenas faz scraping e exibe JSON (não chama a API)",
    )
    args = parser.parse_args(argv)

    settings = Settings.load()
    logger.info("Portal: %s | API: %s", settings.portal_base_url, settings.api_base_url)

    scraper = PontoAgilScraper(settings)
    records = scraper.scrape()

    if not records:
        logger.warning("Nenhum registro encontrado na tabela")
        return 1

    if args.scrape_only:
        output = [record.to_api_dict() for record in records]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        logger.info("Modo scrape-only — %s registro(s) exibidos", len(records))
        return 0

    try:
        client = RpaApiClient(settings)
        result = client.send_records(records)
        imported = result.get("imported_count", len(records))
        logger.info("Sucesso! Registros importados: %s", imported)
        return 0
    except httpx.HTTPError as exc:
        logger.error(
            "Falha ao enviar para a API. A Etapa 1 (backend) está rodando? "
            "Use --scrape-only para testar só o portal. Erro: %s",
            exc,
        )
        return 1
