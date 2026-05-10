from __future__ import annotations

import json
import re
from typing import Any, List, Sequence, Tuple

from ci.catalog import AnchorAddress
from ci.models import ScrapeRecord
from ci.scrapers.base import BasePlatformAdapter


class RappiAdapter(BasePlatformAdapter):
    platform = "rappi"
    start_url = "https://www.rappi.com.mx/restaurantes"
    network_hints = ("grability", "rappi", "restaurant", "menu", "store")

    DOM_PRODUCTS = {
        "big_mac": (
            "Home Office con Big Mac",
            "Big Mac\n",
            "Big Mac ",
            "Big Mac solo",
        ),
        "combo_mediano_big_mac": (
            "McTrío Big Mac mediano+McFlurry Oreo",
            "McTrío Mediano Big Mac + McFlurry Oreo",
            "McTrío Big Mac",
            "McTrio Big Mac",
        ),
        "mcnuggets_10": (
            "McTrio mediano McNuggets 10 pzas",
            "McTrío de 10 McNuggets",
            "McNuggets 10",
            "10 McNuggets",
            "McNuggets de Pollo 10",
        ),
        "coca_cola": (
            "Coca-Cola mediana",
            "Refréscate con Coca Cola de 21 oz",
            "Coca-Cola",
            "Coca Cola",
        ),
    }

    def score_payload_candidate(self, payload: dict[str, Any]) -> int:
        score = super().score_payload_candidate(payload)
        if isinstance(payload.get("store"), dict):
            score += 5
            name = json.dumps(payload["store"], ensure_ascii=False).lower()
            if "mcdonald" in name:
                score += 5
            if "products" in payload["store"]:
                score += 4
        return score

    def scrape(
        self,
        page,
        address: AnchorAddress,
        run_id: str,
        captured_at: str,
        screenshot_path: str,
        evidence_root,
        debug_evidence: bool = False,
    ) -> List[ScrapeRecord]:
        if not address.rappi_store_url:
            return self.build_error_records(
                address=address,
                run_id=run_id,
                captured_at=captured_at,
                screenshot_path=screenshot_path,
                error_reason="address_rejected",
                scrape_stage="resolve_store",
                failure_category="address_rejected",
                run_duration_ms=0,
                evidence_dir="",
            )
        self.start_url = address.rappi_store_url
        return super().scrape(
            page=page,
            address=address,
            run_id=run_id,
            captured_at=captured_at,
            screenshot_path=screenshot_path,
            evidence_root=evidence_root,
            debug_evidence=debug_evidence,
        )

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
        restaurant = payload["restaurant"]
        return self.build_records_from_items(
            address=address,
            run_id=run_id,
            captured_at=captured_at,
            source_mode=source_mode,
            screenshot_path=screenshot_path,
            restaurant_name=restaurant["name"],
            delivery_fee_text=restaurant["delivery_fee"],
            eta_text=restaurant["eta"],
            promo_text=restaurant.get("promo", ""),
            items=restaurant["products"],
            name_key="name",
            price_key="price",
            confidence="high",
            extractor_used="network",
            scrape_stage="extract_menu",
            store_reference=address.rappi_store_url,
            evidence_dir=evidence_dir,
            chosen_payload_path=chosen_payload_path,
            run_duration_ms=run_duration_ms,
        )

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
        eta_match = re.search(r"Delivery\s+(\d+)\s+min", body_text, re.IGNORECASE)
        if not eta_match:
            raise ValueError("Could not find ETA on DOM")
        eta_text = f"{eta_match.group(1)} min"

        fee_text = "$ 0.00" if "Envío\n\nGratis" in body_text or "Envío\nGratis" in body_text or "Envío gratis" in body_text else ""
        if not fee_text:
            fee_match = re.search(r"Envío\s+\$ ?(\d+(?:\.\d{2})?)", body_text, re.IGNORECASE)
            fee_text = f"$ {fee_match.group(1)}" if fee_match else "$ 0.00"

        price_items = []
        for key, phrases in self.DOM_PRODUCTS.items():
            price = self._extract_price_after(body_text, phrases)
            raw_name = phrases[0]
            price_items.append({"name": raw_name, "price": f"$ {price:.2f}"})

        return self.build_records_from_items(
            address=address,
            run_id=run_id,
            captured_at=captured_at,
            source_mode=source_mode,
            screenshot_path=screenshot_path,
            restaurant_name=f"McDonald's - {address.zone_name}",
            delivery_fee_text=fee_text,
            eta_text=eta_text,
            promo_text="Envío gratis en tu pedido" if "$ 0.00" == fee_text else "",
            items=price_items,
            name_key="name",
            price_key="price",
            confidence="high",
            extractor_used="dom",
            scrape_stage="extract_menu",
            store_reference=address.rappi_store_url,
            evidence_dir=evidence_dir,
            chosen_payload_path="",
            run_duration_ms=0,
        )

    def _extract_price_after(self, body_text: str, phrases: Sequence[str]) -> float:
        text = body_text.replace("\r", "")
        for phrase in phrases:
            index = text.lower().find(phrase.lower())
            if index == -1:
                continue
            window = text[index : index + 400]
            prices = re.findall(r"\$ ?(\d+(?:\.\d{2})?)", window)
            if prices:
                return float(prices[0])
        raise ValueError(f"Could not find price for phrases: {phrases}")
