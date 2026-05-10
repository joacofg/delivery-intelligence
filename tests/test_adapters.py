import json
from pathlib import Path

import pytest

from ci.catalog import ANCHOR_ADDRESSES
from ci.scrapers.adapters.didi_food import DidiFoodAdapter
from ci.scrapers.adapters.rappi import RappiAdapter
from ci.scrapers.adapters.uber_eats import UberEatsAdapter


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("adapter", "fixture_name", "platform", "expected_fee", "expected_eta"),
    [
        (RappiAdapter(), "rappi_payload.json", "rappi", 19.0, (25, 35)),
        (UberEatsAdapter(), "ubereats_payload.json", "uber_eats", 18.0, (28, 38)),
        (DidiFoodAdapter(), "didifood_payload.json", "didi_food", 20.0, (30, 40)),
    ],
)
def test_platform_adapters_parse_payloads(adapter, fixture_name, platform, expected_fee, expected_eta) -> None:
    payload = json.loads((FIXTURES / fixture_name).read_text(encoding="utf-8"))
    records = adapter.parse_payload(
        payload=payload,
        address=ANCHOR_ADDRESSES[0],
        run_id="live-test",
        captured_at="2026-05-10T10:00:00Z",
        source_mode="live",
        screenshot_path="outputs/live/example.png",
    )

    assert len(records) == 4
    assert {record.product_key for record in records} == {
        "big_mac",
        "combo_mediano_big_mac",
        "mcnuggets_10",
        "coca_cola",
    }
    assert all(record.platform == platform for record in records)
    assert all(record.delivery_fee == expected_fee for record in records)
    assert all((record.eta_min, record.eta_max) == expected_eta for record in records)
