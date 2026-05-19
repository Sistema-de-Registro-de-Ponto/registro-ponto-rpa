from __future__ import annotations

import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import Page, sync_playwright

from config import Settings, build_datetime_iso, parse_br_date_to_iso
from models.record import PunchRecord

logger = logging.getLogger(__name__)


class PontoAgilScraper:
    """Scraper do Portal Ponto Ágil (mock local ou site real)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def scrape(self) -> list[PunchRecord]:
        self._settings.artifacts_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self._settings.headless,
                slow_mo=self._settings.slow_mo_ms,
            )
            context = browser.new_context(locale="pt-BR")
            page = context.new_page()

            try:
                records = self._run_flow(page)
                logger.info("Scraping concluído: %s registro(s)", len(records))
                return records
            except Exception:
                screenshot = self._settings.artifacts_dir / "erro-scraping.png"
                page.screenshot(path=str(screenshot), full_page=True)
                logger.exception("Falha no scraping — screenshot em %s", screenshot)
                raise
            finally:
                context.close()
                browser.close()

    def _run_flow(self, page: Page) -> list[PunchRecord]:
        base = self._settings.portal_base_url
        login_url = f"{base}/login.html"

        logger.info("Abrindo portal: %s", login_url)
        page.goto(login_url, wait_until="domcontentloaded")

        logger.info("Preenchendo login...")
        page.get_by_test_id("login-username").fill(self._settings.portal_username)
        page.get_by_test_id("login-password").fill(self._settings.portal_password)
        page.get_by_test_id("login-submit").click()
        page.wait_for_url(re.compile(r".*dashboard\.html"), timeout=15_000)
        logger.info("Login realizado — dashboard carregado")

        logger.info("Navegando para espelho de ponto...")
        page.get_by_test_id("nav-registros").first.click()
        page.wait_for_url(re.compile(r".*registros\.html"), timeout=15_000)
        page.get_by_test_id("registros-table").wait_for(state="visible", timeout=15_000)

        rows = page.get_by_test_id("registro-row").all()
        logger.info("Lendo tabela: %s linha(s)", len(rows))

        records: list[PunchRecord] = []
        tz = self._settings.timezone

        for index, row in enumerate(rows, start=1):
            matricula = row.get_by_test_id("col-matricula").inner_text().strip()
            nome = row.get_by_test_id("col-nome").inner_text().strip()
            data_br = row.get_by_test_id("col-data").inner_text().strip()
            entrada = row.get_by_test_id("col-entrada").inner_text().strip()
            saida = row.get_by_test_id("col-saida").inner_text().strip()

            work_date = parse_br_date_to_iso(data_br)
            check_in_at = build_datetime_iso(work_date, entrada, tz)
            check_out_at = (
                build_datetime_iso(work_date, saida, tz) if saida else None
            )
            worked_seconds = self._calc_worked_seconds(check_in_at, check_out_at, tz)

            raw = {
                "matricula": matricula,
                "nome": nome,
                "data_br": data_br,
                "entrada": entrada,
                "saida": saida,
                "row_index": index,
            }

            record = PunchRecord(
                external_employee_id=matricula,
                employee_name=nome,
                work_date=work_date,
                check_in_at=check_in_at,
                check_out_at=check_out_at,
                worked_seconds=worked_seconds,
                raw_payload=raw,
            )
            records.append(record)
            logger.info(
                "  [%s] %s — %s %s-%s",
                matricula,
                nome,
                work_date,
                entrada,
                saida,
            )

        screenshot = self._settings.artifacts_dir / "espelho-ponto.png"
        page.screenshot(path=str(screenshot), full_page=True)
        logger.info("Screenshot salvo em %s", screenshot)

        return records

    @staticmethod
    def _calc_worked_seconds(
        check_in_at: str,
        check_out_at: str | None,
        tz_name: str,
    ) -> int | None:
        if not check_out_at:
            return None
        tz = ZoneInfo(tz_name)
        start = datetime.fromisoformat(check_in_at)
        end = datetime.fromisoformat(check_out_at)
        if start.tzinfo is None:
            start = start.replace(tzinfo=tz)
        if end.tzinfo is None:
            end = end.replace(tzinfo=tz)
        delta = end - start
        return max(0, int(delta.total_seconds()))
