from __future__ import annotations

import re
from typing import Any, List

from ci.catalog import AnchorAddress
from ci.models import ScrapeRecord
from ci.scrapers.base import BasePlatformAdapter


class UberEatsAdapter(BasePlatformAdapter):
    platform = "uber_eats"
    start_url = "https://www.ubereats.com/mx"
    network_hints = ("ubereats", "store", "menu")
    DOM_PRODUCTS = {
        "big_mac": ("Home Office con Big Mac", "Big Mac + Papas Medianas"),
        "combo_mediano_big_mac": ("McTrío Big Mac mediano+McFlurry Oreo", "McTrío mediano Big Mac"),
        "mcnuggets_10": ("McTrío mediano McNuggets 10 pzas", "McTrio mediano McNuggets 10 pzas", "McNuggets de Pollo 10 pzas"),
        "coca_cola": ("Coca-Cola mediana", "Coca Cola de 21 oz"),
    }

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
        if not address.uber_store_url:
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
        self.start_url = address.uber_store_url
        return super().scrape(page, address, run_id, captured_at, screenshot_path, evidence_root, debug_evidence)

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
        store = payload["data"]["store"]
        eta_range = store["etaRange"]
        items = []
        for section in store["sections"]:
            items.extend(section.get("items", []))
        return self.build_records_from_items(
            address=address,
            run_id=run_id,
            captured_at=captured_at,
            source_mode=source_mode,
            screenshot_path=screenshot_path,
            restaurant_name=store["title"],
            delivery_fee_text=store["deliveryFee"],
            eta_text=f"{eta_range['min']}-{eta_range['max']} min",
            promo_text=store.get("promotionText", ""),
            items=items,
            name_key="title",
            price_key="price",
            confidence="medium",
            extractor_used="network",
            scrape_stage="extract_menu",
            store_reference=address.uber_store_url,
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
        # Delivery fee: "Costo de envío MX$20" or "Costo de envío: $20" or "MX$0"
        fee = 0.0
        fee_match = re.search(
            r"(?:Costo de env[íi]o|Delivery fee|Envío)[\s:]*(?:MX)?\$?\s*([0-9]+(?:\.[0-9]+)?)",
            body_text, re.IGNORECASE,
        )
        if fee_match:
            parsed_fee = float(fee_match.group(1))
            fee = parsed_fee if parsed_fee < 500 else 0.0

        # ETA: "25–35 min", "25 - 35 min", "25 min"
        eta_text = "0 min"
        eta_match = re.search(r"(\d{1,2})\s*[–\-]\s*(\d{1,2})\s*min", body_text, re.IGNORECASE)
        if eta_match:
            eta_text = f"{eta_match.group(1)}-{eta_match.group(2)} min"
        else:
            eta_match = re.search(r"(\d{1,2})\s*min(?:utos?)?", body_text, re.IGNORECASE)
            if eta_match:
                eta_text = f"{eta_match.group(1)} min"

        price_items = []
        for key, phrases in self.DOM_PRODUCTS.items():
            price = self._extract_price_after(body_text, phrases)
            price_items.append({"title": phrases[0], "price": f"MX${price:.2f}"})

        return self.build_records_from_items(
            address=address,
            run_id=run_id,
            captured_at=captured_at,
            source_mode=source_mode,
            screenshot_path=screenshot_path,
            restaurant_name=f"McDonald's - {address.zone_name}",
            delivery_fee_text=f"MX${fee:.2f}",
            eta_text=eta_text,
            promo_text="",
            items=price_items,
            name_key="title",
            price_key="price",
            confidence="medium",
            extractor_used="dom",
            scrape_stage="extract_menu",
            store_reference=address.uber_store_url,
            evidence_dir=evidence_dir,
        )

    def _extract_price_after(self, body_text: str, phrases) -> float:
        text = body_text.replace("\r", "")
        for phrase in phrases:
            index = text.lower().find(phrase.lower())
            if index == -1:
                continue
            window = text[index : index + 260]
            matches = re.findall(r"MX\$([0-9]+(?:\.[0-9]+)?)|\$([0-9]+(?:\.[0-9]+)?)", window)
            for left, right in matches:
                raw = left or right
                if raw:
                    return float(raw)
        raise ValueError(f"Could not find price for phrases: {phrases}")
