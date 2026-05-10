from ci.catalog import ANCHOR_ADDRESSES
from ci.scrapers.adapters.rappi import RappiAdapter


RAPPI_MENU_TEXT = """
McDonald's - Roma Norte
Avenida Cuauhtemoc no19 Int19 Local C Col. Roma Norte, CP 06700 Cuauhtemoc CDMX
Delivery
28 min
Envío
Gratis
(nuevos usuarios)
McTrío Big Mac mediano+McFlurry Oreo
McTrío Mediano Big Mac + McFlurry Oreo
$ 169.00
McTrio mediano McNuggets 10 pzas
McTrío de 10 McNuggets, tiernos y jugosos trocitos 100% de pechuga de pollo
$ 159.00
Home Office con Big Mac
Big Mac + Papas Medianas
$ 113.00
Coca-Cola mediana
Refréscate con Coca Cola de 21 oz
$ 55.00
"""


def test_rappi_adapter_dom_fallback_extracts_expected_products() -> None:
    adapter = RappiAdapter()
    records = adapter.parse_dom_text(
        body_text=RAPPI_MENU_TEXT,
        address=ANCHOR_ADDRESSES[1],
        run_id="live-001",
        captured_at="2026-05-10T10:00:00Z",
        source_mode="live_curated",
        screenshot_path="outputs/raw/example.png",
        evidence_dir="outputs/raw/evidence/live-001/rappi/roma-001",
    )

    assert len(records) == 4
    assert {record.product_key for record in records} == {
        "big_mac",
        "combo_mediano_big_mac",
        "mcnuggets_10",
        "coca_cola",
    }
    assert all(record.extractor_used == "dom" for record in records)
    assert all(record.confidence == "high" for record in records)


def test_rappi_adapter_ranks_payload_candidates_deterministically() -> None:
    adapter = RappiAdapter()
    payloads = [
        {"kind": "analytics", "items": []},
        {"store": {"name": "McDonald's", "products": [{"name": "Big Mac", "price": "$ 100.00"}]}},
        {"store": {"name": "Burger King"}},
    ]

    chosen_index, chosen_payload = adapter.rank_payload_candidates(payloads)

    assert chosen_index == 1
    assert chosen_payload["store"]["name"] == "McDonald's"
