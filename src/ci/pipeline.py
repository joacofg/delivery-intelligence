from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

from ci.catalog import ANCHOR_ADDRESSES, GOLDEN_RAPPI_ADDRESS_IDS, PRODUCTS
from ci.models import ScrapeRecord


PLATFORMS = ("rappi", "uber_eats", "didi_food")

PRODUCT_BASE_PRICE = {
    "big_mac": 109.0,
    "combo_mediano_big_mac": 189.0,
    "mcnuggets_10": 129.0,
    "coca_cola": 39.0,
}

ZONE_PRICE_ADJUST = {
    "polanco-001": 8.0,
    "roma-001": 5.0,
    "condesa-001": 4.0,
    "centro-001": 3.0,
    "lomas-001": 9.0,
    "santafe-001": 10.0,
    "delvalle-001": 2.0,
    "narvarte-001": 0.0,
    "napoles-001": 0.0,
    "insurgentes-001": 2.0,
    "doctores-001": -1.0,
    "coyoacan-001": 3.0,
    "tlalpan-001": 1.0,
    "pedregal-001": 7.0,
    "iztapalapa-001": -3.0,
    "ermita-001": -4.0,
    "tlahuac-001": -5.0,
    "lindavista-001": -2.0,
    "vallejo-001": -3.0,
    "xochimilco-001": -2.0,
}

PLATFORM_PRICE_ADJUST = {
    "rappi": 2.0,
    "uber_eats": 4.0,
    "didi_food": -1.0,
}

PLATFORM_DELIVERY_FEE = {
    "rappi": 22.0,
    "uber_eats": 18.0,
    "didi_food": 20.0,
}

# Approximate visible service fee per platform (flat MXN shown at checkout)
PLATFORM_SERVICE_FEE = {
    "rappi": 0.0,
    "uber_eats": 12.0,
    "didi_food": 8.0,
}

ZONE_DELIVERY_ADJUST = {
    "polanco-001": 0.0,
    "roma-001": -2.0,
    "condesa-001": -1.0,
    "centro-001": 0.0,
    "lomas-001": 2.0,
    "santafe-001": 3.0,
    "delvalle-001": 0.0,
    "narvarte-001": 1.0,
    "napoles-001": 1.0,
    "insurgentes-001": 0.0,
    "doctores-001": -1.0,
    "coyoacan-001": 2.0,
    "tlalpan-001": 3.0,
    "pedregal-001": 2.0,
    "iztapalapa-001": 5.0,
    "ermita-001": 6.0,
    "tlahuac-001": 7.0,
    "lindavista-001": 4.0,
    "vallejo-001": 4.0,
    "xochimilco-001": 5.0,
}

PLATFORM_ETA_MID = {
    "rappi": 28,
    "uber_eats": 31,
    "didi_food": 34,
}

ZONE_ETA_ADJUST = {
    "polanco-001": -4,
    "roma-001": -2,
    "condesa-001": -2,
    "centro-001": -1,
    "lomas-001": -3,
    "santafe-001": 4,
    "delvalle-001": 0,
    "narvarte-001": 1,
    "napoles-001": 1,
    "insurgentes-001": 0,
    "doctores-001": -1,
    "coyoacan-001": 3,
    "tlalpan-001": 5,
    "pedregal-001": 2,
    "iztapalapa-001": 8,
    "ermita-001": 10,
    "tlahuac-001": 12,
    "lindavista-001": 5,
    "vallejo-001": 6,
    "xochimilco-001": 7,
}

RAPPI_CURATED_SNAPSHOT = {
    "roma-001": {
        "store_reference": "https://www.rappi.com.mx/restaurantes/1923230196-mcdonalds",
        "eta_min": 28,
        "eta_max": 28,
        "delivery_fee": 0.0,
        "promo_text": "Envío gratis en tu pedido",
        "prices": {
            "big_mac": 113.0,
            "combo_mediano_big_mac": 169.0,
            "mcnuggets_10": 159.0,
            "coca_cola": 55.0,
        },
    },
    "condesa-001": {
        "store_reference": "https://www.rappi.com.mx/restaurantes/1306703465-mcdonalds",
        "eta_min": 16,
        "eta_max": 16,
        "delivery_fee": 0.0,
        "promo_text": "",
        "prices": {
            "big_mac": 113.0,
            "combo_mediano_big_mac": 169.0,
            "mcnuggets_10": 159.0,
            "coca_cola": 55.0,
        },
    },
    "delvalle-001": {
        "store_reference": "https://www.rappi.com.mx/restaurantes/1923216649-mcdonalds",
        "eta_min": 35,
        "eta_max": 35,
        "delivery_fee": 0.0,
        "promo_text": "",
        "prices": {
            "big_mac": 123.0,
            "combo_mediano_big_mac": 169.0,
            "mcnuggets_10": 169.0,
            "coca_cola": 59.0,
        },
    },
}


def build_snapshot_records(run_id: str | None = None) -> List[ScrapeRecord]:
    run_id = run_id or "snapshot-demo"
    captured_at = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    records: List[ScrapeRecord] = []

    for address in ANCHOR_ADDRESSES:
        for platform in PLATFORMS:
            if platform == "rappi" and address.address_id in GOLDEN_RAPPI_ADDRESS_IDS:
                curated = RAPPI_CURATED_SNAPSHOT[address.address_id]
                for product in PRODUCTS:
                    records.append(
                        ScrapeRecord(
                            run_id=run_id,
                            captured_at=captured_at,
                            platform=platform,
                            city="CDMX",
                            address_id=address.address_id,
                            zone_type=address.zone_type,
                            restaurant_chain="McDonald's",
                            product_key=product.key,
                            product_name_raw=product.canonical_name,
                            price=curated["prices"][product.key],
                            currency="MXN",
                            delivery_fee=curated["delivery_fee"],
                            service_fee=0.0,
                            eta_min=curated["eta_min"],
                            eta_max=curated["eta_max"],
                            promo_text=curated["promo_text"],
                            source_mode="snapshot_real",
                            screenshot_path="",
                            status="ok",
                            error_reason="",
                            store_reference=curated["store_reference"],
                            confidence="high",
                            extractor_used="dom",
                            scrape_stage="curated_snapshot",
                            failure_category="",
                            run_duration_ms=0,
                            evidence_dir="",
                            chosen_payload_path="",
                        )
                    )
                continue
            eta_mid = PLATFORM_ETA_MID[platform] + ZONE_ETA_ADJUST[address.address_id]
            eta_min = max(12, eta_mid - 5)
            eta_max = eta_mid + 5
            delivery_fee = PLATFORM_DELIVERY_FEE[platform] + ZONE_DELIVERY_ADJUST[address.address_id]
            promo_text = {
                "rappi": "Envio gratis en pedidos seleccionados",
                "uber_eats": "Hasta 20% off en combos",
                "didi_food": "Cupon visible para usuarios nuevos",
            }[platform]
            for product in PRODUCTS:
                price = (
                    PRODUCT_BASE_PRICE[product.key]
                    + ZONE_PRICE_ADJUST[address.address_id]
                    + PLATFORM_PRICE_ADJUST[platform]
                )
                if product.key == "combo_mediano_big_mac" and platform == "uber_eats":
                    price += 3.0
                if product.key == "coca_cola" and platform == "didi_food":
                    price -= 1.5
                records.append(
                    ScrapeRecord(
                        run_id=run_id,
                        captured_at=captured_at,
                        platform=platform,
                        city="CDMX",
                        address_id=address.address_id,
                        zone_type=address.zone_type,
                        restaurant_chain="McDonald's",
                        product_key=product.key,
                        product_name_raw=product.canonical_name,
                        price=round(price, 2),
                        currency="MXN",
                        delivery_fee=round(delivery_fee, 2),
                        service_fee=PLATFORM_SERVICE_FEE[platform],
                        eta_min=eta_min,
                        eta_max=eta_max,
                        promo_text=promo_text,
                        source_mode="snapshot_synthetic",
                        screenshot_path="",
                        status="ok",
                        error_reason="",
                        store_reference=address.rappi_store_url if platform == "rappi" else "",
                        confidence="medium",
                        extractor_used="synthetic",
                        scrape_stage="snapshot_seed",
                        failure_category="",
                        run_duration_ms=0,
                        evidence_dir="",
                        chosen_payload_path="",
                    )
                )

    return records


def _write_json(path: Path, records: List[ScrapeRecord]) -> None:
    path.write_text(
        json.dumps([record.to_dict() for record in records], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_csv(path: Path, records: List[ScrapeRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].to_dict().keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())


def copy_snapshot_dataset(target_dir: Path, run_id: str | None = None) -> Tuple[Path, Path, List[ScrapeRecord]]:
    target_dir.mkdir(parents=True, exist_ok=True)
    records = build_snapshot_records(run_id=run_id)
    json_path = target_dir / "snapshot_records.json"
    csv_path = target_dir / "snapshot_records.csv"
    _write_json(json_path, records)
    _write_csv(csv_path, records)
    return json_path, csv_path, records


def write_records_bundle(target_dir: Path, stem: str, records: Iterable[ScrapeRecord]) -> Tuple[Path, Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    records = list(records)
    json_path = target_dir / f"{stem}.json"
    csv_path = target_dir / f"{stem}.csv"
    _write_json(json_path, records)
    _write_csv(csv_path, records)
    return json_path, csv_path
