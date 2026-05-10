from ci.catalog import match_product
from ci.normalize import parse_eta_range, parse_money


def test_parse_money_handles_currency_symbol_and_whitespace() -> None:
    assert parse_money("$ 129.00") == 129.0


def test_parse_money_handles_decimal_comma() -> None:
    assert parse_money("MX$129,50") == 129.5


def test_parse_eta_range_for_explicit_range() -> None:
    assert parse_eta_range("30-40 min") == (30, 40)


def test_parse_eta_range_for_single_value() -> None:
    assert parse_eta_range("35 mins") == (35, 35)


def test_match_product_maps_known_aliases_to_catalog_key() -> None:
    product = match_product("Big Mac Combo Mediano")
    assert product.key == "combo_mediano_big_mac"
