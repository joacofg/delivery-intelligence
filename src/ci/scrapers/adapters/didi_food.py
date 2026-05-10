from __future__ import annotations

import re
from typing import Any, List

from ci.catalog import AnchorAddress
from ci.models import ScrapeRecord
from ci.scrapers.base import BasePlatformAdapter


class DidiFoodAdapter(BasePlatformAdapter):
    platform = "didi_food"
    start_url = "https://web.didiglobal.com/mx/food/"
    network_hints = ("didi", "food", "menu")
    # Phrases ordered from most specific to least specific for each product.
    # big_mac uses "\nBig Mac" to avoid matching inside combo names like "McTrío mediano Big Mac".
    DOM_PRODUCTS = {
        "big_mac": ("\nBig Mac\n", "\nBig Mac ", "Big Mac solo", "Big Mac individual"),
        "combo_mediano_big_mac": ("McTrío Mediano Big Mac", "McTrío mediano Big Mac", "Combo Mediano Big Mac"),
        "mcnuggets_10": ("McNuggets de Pollo 10", "10 McNuggets de Pollo", "McNuggets 10 piezas", "Paquete Botanero"),
        "coca_cola": ("Coca-Cola mediana", "Coca-Cola 400 ml", "Coca Cola de 21 oz"),
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
        if not address.didi_store_url:
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
        self.start_url = address.didi_store_url
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
        shop = payload["payload"]["shop"]
        items = []
        for category in shop["menu"]["categories"]:
            items.extend(category.get("products", []))
        return self.build_records_from_items(
            address=address,
            run_id=run_id,
            captured_at=captured_at,
            source_mode=source_mode,
            screenshot_path=screenshot_path,
            restaurant_name=shop["displayName"],
            delivery_fee_text=shop["shipping"]["fee"],
            eta_text=shop["etaText"],
            promo_text=shop.get("couponText", ""),
            items=items,
            name_key="displayName",
            price_key="amount",
            confidence="medium",
            extractor_used="network",
            scrape_stage="extract_menu",
            store_reference=address.didi_store_url,
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
        # Delivery fee: "Envío MX$20", "Costo de envío: $20", "Envío gratis"
        fee = 0.0
        fee_match = re.search(
            r"(?:Costo de env[íi]o|Env[íi]o)[\s:]*(?:MX)?\$\s*([0-9]+(?:\.[0-9]+)?)",
            body_text, re.IGNORECASE,
        )
        if fee_match:
            parsed_fee = float(fee_match.group(1))
            fee = parsed_fee if parsed_fee < 500 else 0.0

        # ETA: "25-35 min", "25 min", "~30 min"
        eta_text = "0 min"
        eta_match = re.search(r"(\d{1,2})\s*[–\-]\s*(\d{1,2})\s*min", body_text, re.IGNORECASE)
        if eta_match:
            eta_text = f"{eta_match.group(1)}-{eta_match.group(2)} min"
        else:
            eta_match = re.search(r"~?\s*(\d{1,2})\s*min(?:utos?)?", body_text, re.IGNORECASE)
            if eta_match:
                eta_text = f"{eta_match.group(1)} min"

        price_items = []
        for key, phrases in self.DOM_PRODUCTS.items():
            price = self._extract_price_after(body_text, phrases)
            price_items.append({"displayName": phrases[0].strip(), "amount": f"MX${price:.2f}"})

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
            name_key="displayName",
            price_key="amount",
            confidence="medium",
            extractor_used="dom",
            scrape_stage="extract_menu",
            store_reference=address.didi_store_url,
            evidence_dir=evidence_dir,
        )

    def _extract_price_after(self, body_text: str, phrases) -> float:
        text = body_text.replace("\r", "")
        for phrase in phrases:
            phrase_lower = phrase.lower()
            search_text = text.lower()
            start = 0
            while True:
                index = search_text.find(phrase_lower, start)
                if index == -1:
                    break
                # Avoid matching phrase inside longer words/names (e.g. "Big Mac" inside "McTrío mediano Big Mac")
                before = text[max(0, index - 30) : index].lower()
                if any(frag in before for frag in ("trio", "trío", "mediano", "combo", "paquete")):
                    start = index + 1
                    continue
                window = text[index : index + 200]
                matches = re.findall(r"MX\$([0-9]+(?:\.[0-9]+)?)", window)
                if matches:
                    return float(matches[0])
                break
        raise ValueError(f"Could not find price for phrases: {phrases}")
