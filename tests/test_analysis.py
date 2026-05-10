from ci.analysis import build_coverage_summary, build_platform_summary, build_zone_summary
from ci.models import ScrapeRecord


def _record(**overrides):
    base = {
        "run_id": "snapshot-001",
        "captured_at": "2026-05-10T10:00:00Z",
        "platform": "rappi",
        "city": "CDMX",
        "address_id": "polanco-001",
        "zone_type": "high_income",
        "restaurant_chain": "McDonald's",
        "product_key": "big_mac",
        "product_name_raw": "Big Mac",
        "price": 100.0,
        "currency": "MXN",
        "delivery_fee": 20.0,
        "service_fee": 0.0,
        "eta_min": 25,
        "eta_max": 35,
        "promo_text": "",
        "source_mode": "snapshot_real",
        "screenshot_path": "",
        "status": "ok",
        "error_reason": "",
        "store_reference": "store-roma",
        "confidence": "high",
        "extractor_used": "dom",
        "scrape_stage": "extract_menu",
        "failure_category": "",
        "run_duration_ms": 1200,
        "evidence_dir": "",
        "chosen_payload_path": "",
    }
    base.update(overrides)
    return ScrapeRecord(**base)


def test_build_platform_summary_only_uses_usable_rows_for_metric_means() -> None:
    rows = [
        _record(platform="rappi", price=100.0, delivery_fee=20.0, eta_min=20, eta_max=30),
        _record(platform="uber_eats", price=110.0, delivery_fee=15.0, eta_min=25, eta_max=35, source_mode="snapshot_synthetic"),
        _record(platform="didi_food", price=95.0, delivery_fee=18.0, eta_min=30, eta_max=40, source_mode="snapshot_synthetic"),
        _record(platform="rappi", status="blocked", failure_category="restaurant_not_found", error_reason="restaurant_not_found", price=0.0, delivery_fee=0.0, eta_min=0, eta_max=0),
    ]

    summary = build_platform_summary(rows)

    assert list(summary["platform"]) == ["didi_food", "rappi", "uber_eats"]
    assert float(summary.loc[summary["platform"] == "rappi", "avg_price"].iloc[0]) == 100.0


def test_build_zone_summary_compares_competitors_against_rappi() -> None:
    rows = [
        _record(platform="rappi", address_id="roma-001", zone_type="central", price=100.0),
        _record(platform="uber_eats", address_id="roma-001", zone_type="central", price=120.0, source_mode="snapshot_synthetic"),
        _record(platform="didi_food", address_id="roma-001", zone_type="central", price=90.0, source_mode="snapshot_synthetic"),
    ]

    summary = build_zone_summary(rows)

    uber_gap = summary.loc[summary["platform"] == "uber_eats", "avg_price_gap_vs_rappi"].iloc[0]
    didi_gap = summary.loc[summary["platform"] == "didi_food", "avg_price_gap_vs_rappi"].iloc[0]
    assert float(uber_gap) == 20.0
    assert float(didi_gap) == -10.0


def test_build_coverage_summary_counts_failures_and_origins() -> None:
    rows = [
        _record(platform="rappi", address_id="roma-001", source_mode="snapshot_real"),
        _record(platform="rappi", address_id="roma-001", product_key="combo_mediano_big_mac", source_mode="snapshot_real"),
        _record(platform="rappi", address_id="narvarte-001", status="blocked", error_reason="restaurant_not_found", failure_category="restaurant_not_found", price=0.0, delivery_fee=0.0, eta_min=0, eta_max=0),
        _record(platform="uber_eats", address_id="roma-001", source_mode="snapshot_synthetic"),
    ]

    summary = build_coverage_summary(rows)

    rappi = summary[summary["platform"] == "rappi"].iloc[0]
    assert int(rappi["rows_total"]) == 3
    assert int(rappi["rows_usable"]) == 2
    assert int(rappi["rows_failed"]) == 1
    assert int(rappi["unique_addresses"]) == 2
    assert int(rappi["snapshot_real_rows"]) == 2
