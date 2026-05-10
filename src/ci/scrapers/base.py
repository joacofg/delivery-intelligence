from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from ci.catalog import PRODUCTS, AnchorAddress, match_product
from ci.models import ScrapeRecord
from ci.normalize import parse_eta_range, parse_money


LOGGER = logging.getLogger(__name__)


def persist_evidence_artifacts(
    *,
    evidence_root: Path,
    run_id: str,
    platform: str,
    address: AnchorAddress,
    payloads: Sequence[dict[str, Any]],
    chosen_index: Optional[int],
    scrape_stage: str,
    extractor_used: str,
    failure_category: str,
    duration_ms: int,
    screenshot_path: str,
) -> dict[str, str]:
    evidence_dir = Path(evidence_root) / run_id / platform / address.address_id
    evidence_dir.mkdir(parents=True, exist_ok=True)

    payload_paths: list[Path] = []
    for index, payload in enumerate(payloads, start=1):
        payload_path = evidence_dir / f"payload-{index:03d}.json"
        payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        payload_paths.append(payload_path)

    chosen_payload_path = str(payload_paths[chosen_index]) if chosen_index is not None and chosen_index < len(payload_paths) else ""
    metadata = {
        "run_id": run_id,
        "platform": platform,
        "address_id": address.address_id,
        "scrape_stage": scrape_stage,
        "extractor_used": extractor_used,
        "failure_category": failure_category,
        "duration_ms": duration_ms,
        "screenshot_path": screenshot_path,
        "chosen_payload_path": chosen_payload_path,
        "payload_count": len(payloads),
        "evidence_dir": str(evidence_dir),
    }
    (evidence_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"evidence_dir": str(evidence_dir), "chosen_payload_path": chosen_payload_path}


class BasePlatformAdapter(ABC):
    platform: str = ""
    start_url: str = ""
    network_hints: tuple[str, ...] = ()

    def wants_response(self, url: str, content_type: str) -> bool:
        if "json" not in content_type.lower():
            return False
        lowered = url.lower()
        return any(hint in lowered for hint in self.network_hints)

    def rank_payload_candidates(self, payloads: Sequence[dict[str, Any]]) -> Tuple[Optional[int], Optional[dict[str, Any]]]:
        best_index: Optional[int] = None
        best_payload: Optional[dict[str, Any]] = None
        best_score = -1
        for index, payload in enumerate(payloads):
            score = self.score_payload_candidate(payload)
            if score > best_score:
                best_score = score
                best_index = index
                best_payload = payload
        if best_score <= 0:
            return None, None
        return best_index, best_payload

    def score_payload_candidate(self, payload: dict[str, Any]) -> int:
        score = 0
        payload_text = json.dumps(payload, ensure_ascii=False).lower()
        if "mcdonald" in payload_text:
            score += 3
        if "product" in payload_text or "menu" in payload_text:
            score += 2
        if "price" in payload_text or "amount" in payload_text:
            score += 1
        return score

    @abstractmethod
    def parse_payload(
        self,
        payload: dict[str, Any],
        address: AnchorAddress,
        run_id: str,
        captured_at: str,
        source_mode: str,
        screenshot_path: str,
        evidence_dir: str = "",
        chosen_payload_path: str = "",
        run_duration_ms: int = 0,
    ) -> List[ScrapeRecord]:
        raise NotImplementedError

    def parse_dom_text(
        self,
        *,
        body_text: str,
        address: AnchorAddress,
        run_id: str,
        captured_at: str,
        source_mode: str,
        screenshot_path: str,
        evidence_dir: str,
    ) -> List[ScrapeRecord]:
        raise NotImplementedError

    def scrape(
        self,
        page,
        address: AnchorAddress,
        run_id: str,
        captured_at: str,
        screenshot_path: str,
        evidence_root: Path,
        debug_evidence: bool = False,
    ) -> List[ScrapeRecord]:
        start = time.time()
        payloads: list[dict[str, Any]] = []

        def handle_response(response) -> None:
            try:
                content_type = response.headers.get("content-type", "")
                if not self.wants_response(response.url, content_type):
                    return
                payload = response.json()
                if isinstance(payload, dict):
                    payloads.append(payload)
            except Exception:
                return

        page.on("response", handle_response)

        try:
            page.goto(self.start_url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            page.screenshot(path=screenshot_path, full_page=True)
        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            LOGGER.warning("Failed to load %s for %s: %s", self.platform, address.address_id, exc)
            evidence = persist_evidence_artifacts(
                evidence_root=evidence_root,
                run_id=run_id,
                platform=self.platform,
                address=address,
                payloads=payloads if debug_evidence else [],
                chosen_index=None,
                scrape_stage="load_page",
                extractor_used="",
                failure_category="blocked",
                duration_ms=duration_ms,
                screenshot_path=screenshot_path,
            )
            return self.build_error_records(
                address=address,
                run_id=run_id,
                captured_at=captured_at,
                screenshot_path=screenshot_path,
                error_reason="blocked",
                scrape_stage="load_page",
                failure_category="blocked",
                run_duration_ms=duration_ms,
                evidence_dir=evidence["evidence_dir"],
            )

        chosen_index, chosen_payload = self.rank_payload_candidates(payloads)
        duration_ms = int((time.time() - start) * 1000)
        evidence = persist_evidence_artifacts(
            evidence_root=evidence_root,
            run_id=run_id,
            platform=self.platform,
            address=address,
            payloads=payloads if debug_evidence else ([chosen_payload] if chosen_payload else []),
            chosen_index=0 if debug_evidence is False and chosen_payload else chosen_index,
            scrape_stage="extract_menu",
            extractor_used="network" if chosen_payload else "dom",
            failure_category="",
            duration_ms=duration_ms,
            screenshot_path=screenshot_path,
        )

        if chosen_payload is not None:
            try:
                records = self.parse_payload(
                    payload=chosen_payload,
                    address=address,
                    run_id=run_id,
                    captured_at=captured_at,
                    source_mode="live_curated",
                    screenshot_path=screenshot_path,
                    evidence_dir=evidence["evidence_dir"],
                    chosen_payload_path=evidence["chosen_payload_path"],
                    run_duration_ms=duration_ms,
                )
                if records:
                    return records
            except Exception as exc:
                LOGGER.info("Payload parse skipped for %s/%s: %s", self.platform, address.address_id, exc)

        try:
            body_text = page.locator("body").inner_text()
            records = self.parse_dom_text(
                body_text=body_text,
                address=address,
                run_id=run_id,
                captured_at=captured_at,
                source_mode="live_curated",
                screenshot_path=screenshot_path,
                evidence_dir=evidence["evidence_dir"],
            )
            updated = []
            for record in records:
                updated.append(
                    ScrapeRecord(
                        **{
                            **record.to_dict(),
                            "chosen_payload_path": evidence["chosen_payload_path"],
                            "run_duration_ms": duration_ms,
                        }
                    )
                )
            return updated
        except Exception as exc:
            LOGGER.warning("DOM parse failed for %s/%s: %s", self.platform, address.address_id, exc)
            return self.build_error_records(
                address=address,
                run_id=run_id,
                captured_at=captured_at,
                screenshot_path=screenshot_path,
                error_reason="product_missing",
                scrape_stage="extract_menu",
                failure_category="product_missing",
                run_duration_ms=duration_ms,
                evidence_dir=evidence["evidence_dir"],
                chosen_payload_path=evidence["chosen_payload_path"],
            )

    def build_records_from_items(
        self,
        *,
        address: AnchorAddress,
        run_id: str,
        captured_at: str,
        source_mode: str,
        screenshot_path: str,
        restaurant_name: str,
        delivery_fee_text: str,
        eta_text: str,
        promo_text: str,
        items: Iterable[dict[str, Any]],
        name_key: str,
        price_key: str,
        confidence: str = "high",
        extractor_used: str = "network",
        scrape_stage: str = "extract_menu",
        store_reference: str = "",
        evidence_dir: str = "",
        chosen_payload_path: str = "",
        run_duration_ms: int = 0,
    ) -> List[ScrapeRecord]:
        delivery_fee = parse_money(str(delivery_fee_text)) if str(delivery_fee_text).strip() else 0.0
        eta_min, eta_max = parse_eta_range(str(eta_text))
        records = []
        seen = set()
        for item in items:
            product_name = str(item.get(name_key, "")).strip()
            price_value = item.get(price_key, "")
            if not product_name or price_value in ("", None):
                continue
            product = match_product(product_name)
            if product.key in seen:
                continue
            seen.add(product.key)
            records.append(
                ScrapeRecord(
                    run_id=run_id,
                    captured_at=captured_at,
                    platform=self.platform,
                    city="CDMX",
                    address_id=address.address_id,
                    zone_type=address.zone_type,
                    restaurant_chain=restaurant_name,
                    product_key=product.key,
                    product_name_raw=product_name,
                    price=parse_money(str(price_value)),
                    currency="MXN",
                    delivery_fee=delivery_fee,
                    service_fee=0.0,
                    eta_min=eta_min,
                    eta_max=eta_max,
                    promo_text=promo_text,
                    source_mode=source_mode,
                    screenshot_path=screenshot_path,
                    status="ok",
                    error_reason="",
                    store_reference=store_reference,
                    confidence=confidence,
                    extractor_used=extractor_used,
                    scrape_stage=scrape_stage,
                    failure_category="",
                    run_duration_ms=run_duration_ms,
                    evidence_dir=evidence_dir,
                    chosen_payload_path=chosen_payload_path,
                )
            )

        if len(records) < len(PRODUCTS):
            missing = {product.key for product in PRODUCTS} - {record.product_key for record in records}
            if missing:
                raise ValueError(f"Missing products in payload: {sorted(missing)}")
        return records

    def build_error_records(
        self,
        *,
        address: AnchorAddress,
        run_id: str,
        captured_at: str,
        screenshot_path: str,
        error_reason: str,
        scrape_stage: str,
        failure_category: str,
        run_duration_ms: int,
        evidence_dir: str,
        chosen_payload_path: str = "",
    ) -> List[ScrapeRecord]:
        records = []
        for product in PRODUCTS:
            records.append(
                ScrapeRecord(
                    run_id=run_id,
                    captured_at=captured_at,
                    platform=self.platform,
                    city="CDMX",
                    address_id=address.address_id,
                    zone_type=address.zone_type,
                    restaurant_chain="McDonald's",
                    product_key=product.key,
                    product_name_raw=product.canonical_name,
                    price=0.0,
                    currency="MXN",
                    delivery_fee=0.0,
                    service_fee=0.0,
                    eta_min=0,
                    eta_max=0,
                    promo_text="",
                    source_mode="live_curated",
                    screenshot_path=screenshot_path,
                    status="blocked",
                    error_reason=error_reason,
                    store_reference=address.rappi_store_url if self.platform == "rappi" else "",
                    confidence="low",
                    extractor_used="",
                    scrape_stage=scrape_stage,
                    failure_category=failure_category,
                    run_duration_ms=run_duration_ms,
                    evidence_dir=evidence_dir,
                    chosen_payload_path=chosen_payload_path,
                )
            )
        return records
