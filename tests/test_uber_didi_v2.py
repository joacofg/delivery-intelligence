from ci.catalog import ANCHOR_ADDRESSES
from ci.scrapers.adapters.didi_food import DidiFoodAdapter
from ci.scrapers.adapters.uber_eats import UberEatsAdapter


UBER_MENU_TEXT = """
McDonald's (Reforma)
Roma 48, Juárez
Ciudad de México, CDMX
Too far to deliver
Enter address
to see delivery time
Home Office con Big Mac
MX$109.00 MX$200.00
Big Mac + Papas Medianas
McTrío mediano Big Mac
MX$149.00
McTrío Big Mac mediano+McFlurry Oreo
MX$169.00 MX$218.00
McTrío mediano McNuggets 10 pzas
MX$159.00
Coca-Cola mediana
MX$59.00
Refréscate con Coca Cola de 21 oz
"""


DIDI_MENU_TEXT = """
McDonald's (Portal Centro)
Home Office con Big Mac
MX$174.00
Big Mac + Papas Medianas
McTrío mediano Big Mac
MX$149.00
McTrío Mediano Big Mac + McFlurry Oreo
Paquete Botanero
MX$194.00
Disfruta tus partidos favoritos con 10 McNuggets + Papas grandes
Coca-Cola mediana
MX$55.00
Refréscate con Coca Cola de 21 oz
"""


def test_uber_adapter_dom_parse_extracts_expected_products() -> None:
    adapter = UberEatsAdapter()
    records = adapter.parse_dom_text(
        body_text=UBER_MENU_TEXT,
        address=ANCHOR_ADDRESSES[1],
        run_id="live-001",
        captured_at="2026-05-10T10:00:00Z",
        source_mode="live_curated",
        screenshot_path="outputs/raw/example.png",
        evidence_dir="outputs/raw/evidence/live-001/uber/roma-001",
    )

    assert len(records) == 4
    assert all(record.platform == "uber_eats" for record in records)
    assert all(record.extractor_used == "dom" for record in records)
    assert all(record.status == "ok" for record in records)
    assert {record.product_key for record in records} == {
        "big_mac",
        "combo_mediano_big_mac",
        "mcnuggets_10",
        "coca_cola",
    }


def test_didi_adapter_dom_parse_extracts_expected_products() -> None:
    adapter = DidiFoodAdapter()
    records = adapter.parse_dom_text(
        body_text=DIDI_MENU_TEXT,
        address=ANCHOR_ADDRESSES[1],
        run_id="live-001",
        captured_at="2026-05-10T10:00:00Z",
        source_mode="live_curated",
        screenshot_path="outputs/raw/example.png",
        evidence_dir="outputs/raw/evidence/live-001/didi/roma-001",
    )

    assert len(records) == 4
    assert all(record.platform == "didi_food" for record in records)
    assert all(record.extractor_used == "dom" for record in records)
    assert {record.product_key for record in records} == {
        "big_mac",
        "combo_mediano_big_mac",
        "mcnuggets_10",
        "coca_cola",
    }
