from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict


@dataclass(frozen=True)
class ScrapeRecord:
    run_id: str
    captured_at: str
    platform: str
    city: str
    address_id: str
    zone_type: str
    restaurant_chain: str
    product_key: str
    product_name_raw: str
    price: float
    currency: str
    delivery_fee: float
    service_fee: float
    eta_min: int
    eta_max: int
    promo_text: str
    source_mode: str
    screenshot_path: str
    status: str
    error_reason: str
    store_reference: str = ""
    confidence: str = "medium"
    extractor_used: str = ""
    scrape_stage: str = ""
    failure_category: str = ""
    run_duration_ms: int = 0
    evidence_dir: str = ""
    chosen_payload_path: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)
