from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from playwright.sync_api import sync_playwright

from ci.catalog import ANCHOR_ADDRESSES
from ci.models import ScrapeRecord
from ci.pipeline import write_records_bundle
from ci.scrapers.adapters.didi_food import DidiFoodAdapter
from ci.scrapers.adapters.rappi import RappiAdapter
from ci.scrapers.adapters.uber_eats import UberEatsAdapter


LOGGER = logging.getLogger(__name__)


def run_live_scrape(
    output_dir: Path,
    addresses: Iterable = ANCHOR_ADDRESSES,
    platforms: Iterable[str] | None = None,
    debug_evidence: bool = False,
) -> tuple[Path, Path, List[ScrapeRecord]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_root = output_dir / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("live-%Y%m%d-%H%M%S")
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    adapters = {
        "rappi": RappiAdapter(),
        "uber_eats": UberEatsAdapter(),
        "didi_food": DidiFoodAdapter(),
    }
    selected_platforms = list(platforms) if platforms else list(adapters.keys())
    records: List[ScrapeRecord] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for address in addresses:
            for platform in selected_platforms:
                adapter = adapters[platform]
                page = browser.new_page(locale="es-MX")
                evidence_dir = evidence_root / run_id / adapter.platform / address.address_id
                evidence_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = evidence_dir / "screenshot.png"
                LOGGER.info("Scraping %s for %s", adapter.platform, address.address_id)
                records.extend(
                    adapter.scrape(
                        page=page,
                        address=address,
                        run_id=run_id,
                        captured_at=captured_at,
                        screenshot_path=str(screenshot_path),
                        evidence_root=evidence_root,
                        debug_evidence=debug_evidence,
                    )
                )
                page.close()
        browser.close()

    json_path, csv_path = write_records_bundle(output_dir, run_id, records)
    return json_path, csv_path, records
