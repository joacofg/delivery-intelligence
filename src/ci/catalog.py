from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ProductSpec:
    key: str
    canonical_name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class AnchorAddress:
    address_id: str
    zone_name: str
    zone_type: str
    address_line: str
    reserve_address_line: str
    rappi_store_url: str = ""
    uber_store_url: str = ""
    didi_store_url: str = ""


PRODUCTS: tuple[ProductSpec, ...] = (
    ProductSpec("big_mac", "Big Mac", ("big mac",)),
    ProductSpec(
        "combo_mediano_big_mac",
        "Combo Mediano Big Mac",
        ("big mac combo mediano", "combo mediano big mac", "big mac meal", "mctrio big mac", "mctrío big mac"),
    ),
    ProductSpec("mcnuggets_10", "McNuggets 10", ("mcnuggets 10", "nuggets 10", "10 nuggets", "paquete botanero", "10 mcnuggets")),
    ProductSpec("coca_cola", "Coca-Cola", ("coca cola", "coca-cola", "coca cola 500ml")),
)

# fmt: off
ANCHOR_ADDRESSES: tuple[AnchorAddress, ...] = (
    # ── Central / alta renta ────────────────────────────────────────────────────
    AnchorAddress(
        "polanco-001", "Polanco", "high_income",
        "Av. Presidente Masaryk 111, Polanco, CDMX",
        "Anatole France 70, Polanco, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923762729-mc-donalds-interlomas-tier-4",
        "https://www.ubereats.com/mx/store/mcdonalds-polanco/GMcH3w_vX4CtLxBPRICeWA",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-polanco/5764607791197847890/",
    ),
    AnchorAddress(
        "roma-001", "Roma Norte", "central",
        "Álvaro Obregón 99, Roma Norte, CDMX",
        "Zacatecas 92, Roma Norte, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923230196-mcdonalds",
        "https://www.ubereats.com/mx/store/mcdonalds-reforma/yD_69FtxTTGWjKm4rJ1BEg",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-portal-centro/5764607547986935864/",
    ),
    AnchorAddress(
        "condesa-001", "Condesa", "central",
        "Av. Amsterdam 159, Condesa, CDMX",
        "Tamaulipas 95, Condesa, CDMX",
        "https://www.rappi.com.mx/restaurantes/1306703465-mcdonalds",
        "https://www.ubereats.com/mx-en/store/mcdonalds-portal-centro/tT2iwjS2RmiLR3QK4uYpUQ",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-reforma-insurgentes/5764607587992207421/",
    ),
    AnchorAddress(
        "centro-001", "Centro Histórico", "historic",
        "Av. Juárez 76, Centro Histórico, CDMX",
        "16 de Septiembre 58, Centro, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923816278-mcdonalds",
        "https://www.ubereats.com/mx/store/mcdonalds-reforma-222/LA59ctSNQ2mK1qvSGeBFOQ",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-cuauhtemoc/5764607554400026685/",
    ),
    AnchorAddress(
        "lomas-001", "Lomas de Chapultepec", "high_income_west",
        "Periférico Blvd. Manuel Ávila Camacho 50, Lomas de Chapultepec, CDMX",
        "Paseo de los Tamarindos 90, Bosques de las Lomas, CDMX",
        "",
        "https://www.ubereats.com/mx-en/store/mcdonalds-lomas-plaza/lirUzHWMQ6iakIvNZ89Hqw",
        "",
    ),
    AnchorAddress(
        "santafe-001", "Santa Fe", "business",
        "Vasco de Quiroga 3800, Santa Fe, CDMX",
        "Juan Salvador Agraz 97, Santa Fe, CDMX",
        "https://www.rappi.com.mx/restaurantes/1306705692-mc-donalds-interlomas-tier-4",
        "https://www.ubereats.com/mx-en/store/mcdonalds-santa-fe-zentrika/V77AC3JyS8-aloYvj4ag9w",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-zentrika/5764607765293826113/",
    ),
    # ── Residencial ─────────────────────────────────────────────────────────────
    AnchorAddress(
        "delvalle-001", "Del Valle", "residential",
        "Av. Insurgentes Sur 934, Del Valle, CDMX",
        "Parroquia 108, Del Valle, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923216649-mcdonalds",
        "https://www.ubereats.com/mx/store/mcdonalds-san-angel/vJpEN90bVd6GkbgCiVA5cQ",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-plaza-universidad/5764607774462574657/",
    ),
    AnchorAddress(
        "narvarte-001", "Narvarte", "residential",
        "Eugenia 901, Narvarte, CDMX",
        "Dr. José María Vértiz 1172, Narvarte, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923216654-mcdonalds",
        "https://www.ubereats.com/mx/store/mcdonalds-sears-insurgentes/mREIcg3yRhGnS6IUIL2GuQ",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-parque-hundido/5764607600071802936/",
    ),
    AnchorAddress(
        "napoles-001", "Nápoles", "residential_mid",
        "Av. Patriotismo 229, San Pedro de los Pinos, Benito Juárez, CDMX",
        "Félix Cuevas 6, Nápoles, Benito Juárez, CDMX",
        "",
        "https://www.ubereats.com/mx/store/mcdonalds-sears-insurgentes/mREIcg3yRhGnS6IUIL2GuQ",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-municipio-libre/5764607718653165718/",
    ),
    # ── Corredor comercial ───────────────────────────────────────────────────────
    AnchorAddress(
        "insurgentes-001", "Insurgentes Sur", "commercial_corridor",
        "Av. Insurgentes Sur 1971, Guadalupe Inn, CDMX",
        "Av. Insurgentes Sur 1457, Mixcoac, CDMX",
        "",
        "https://www.ubereats.com/mx/store/mcdonalds-taller/eHwyLyOlSFqBjMEzQw1HLw",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-reforma-insurgentes/5764607587992207421/",
    ),
    AnchorAddress(
        "doctores-001", "Doctores / Roma Sur", "central_working",
        "Eje 3 Sur 149, Doctores, Cuauhtémoc, CDMX",
        "Av. Baja California 1, Roma Sur, CDMX",
        "",
        "https://www.ubereats.com/mx/store/mcdonalds-taller/eHwyLyOlSFqBjMEzQw1HLw",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-sears-insurgentes/5764607651733045299/",
    ),
    # ── Familiar / popular ───────────────────────────────────────────────────────
    AnchorAddress(
        "coyoacan-001", "Coyoacán", "family",
        "Av. Miguel Ángel de Quevedo 287, Coyoacán, CDMX",
        "Av. Universidad 1000, Coyoacán, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923219830-mcdonalds-ciudad-de-mexico",
        "https://www.ubereats.com/mx-en/store/mcdonalds-coaplaza/15x-lsvkSb-bT9alq2m_5w",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-gran-sur/5764607744301334593/",
    ),
    AnchorAddress(
        "tlalpan-001", "Tlalpan / Coapa", "peripheral_south",
        "Calzada del Hueso 670, Coapa, Tlalpan, CDMX",
        "Insurgentes Sur 3579, Tlalpan, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923808910-mcdonalds",
        "https://www.ubereats.com/mx-en/store/mcdonalds-coaplaza/15x-lsvkSb-bT9alq2m_5w",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-gran-sur/5764607744301334593/",
    ),
    # ── Alta densidad / periferia sur ────────────────────────────────────────────
    AnchorAddress(
        "pedregal-001", "Pedregal", "high_income_south",
        "Anillo Periférico Sur 4690, Jardines del Pedregal, CDMX",
        "Periférico Sur 4090, Fuentes del Pedregal, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923804253-mcdonalds",
        "https://www.ubereats.com/mx/store/mcdonalds-pedregal/PHkrESyFQtOzUV_S3IC6lg",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-pedregal/5764607588327751741/",
    ),
    AnchorAddress(
        "iztapalapa-001", "Iztapalapa", "high_density",
        "Calz. Ermita Iztapalapa 748, Granjas San Antonio, CDMX",
        "Av. Canal de Garay 3278, Iztapalapa, CDMX",
        "https://www.rappi.com.mx/restaurantes/1306705707-mcdonalds",
        "https://www.ubereats.com/mx/store/mcdonalds-ermita-las-torres/n5WIOQ8VSSy8vWXEB8k4-A",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-ermita-san-miguel/5764607562264346850/",
    ),
    AnchorAddress(
        "ermita-001", "Ermita Iztapalapa Este", "high_density_east",
        "Calz. Ermita Iztapalapa 2120, San Miguel, Iztapalapa, CDMX",
        "Ermita Iztapalapa 3573, Santiago Acahualtepec, CDMX",
        "",
        "https://www.ubereats.com/mx-en/store/mcdonalds-plaza-central/zVEpEpi-RPGbzm9s60Nnxg",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-ermita/5764607560330772706/",
    ),
    AnchorAddress(
        "tlahuac-001", "Tláhuac", "peripheral_east",
        "Av. Tláhuac 3400, Los Olivos, Tláhuac, CDMX",
        "Calz. de la Viga 3000, Tláhuac, CDMX",
        "",
        "",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-san-lorenzo/5764607779520905552/",
    ),
    # ── Periferia norte / clase trabajadora ─────────────────────────────────────
    AnchorAddress(
        "lindavista-001", "Lindavista", "peripheral",
        "Av. Montevideo 279, Lindavista, CDMX",
        "Sierravista 125, Lindavista, CDMX",
        "https://www.rappi.com.mx/restaurantes/1930234854-mcdonalds",
        "",
        "",
    ),
    AnchorAddress(
        "vallejo-001", "Industrial Vallejo", "working_class",
        "Av. Othón de Mendizábal Ote. 343, Industrial Vallejo, CDMX",
        "Calzada Vallejo 1090, Azcapotzalco, CDMX",
        "https://www.rappi.com.mx/restaurantes/1930234854-mcdonalds",
        "",
        "",
    ),
    AnchorAddress(
        "xochimilco-001", "Xochimilco", "peripheral_south",
        "Av. Guadalupe Ramírez 14, Xochimilco, CDMX",
        "Av. Morelos 164, Xochimilco, CDMX",
        "https://www.rappi.com.mx/restaurantes/1923808910-mcdonalds",
        "",
        "https://web.didiglobal.com/mx/food/ciudad-de-mexico-cdmx/mcdonalds-xochimilco/5764607744301334593/",
    ),
)
# fmt: on

GOLDEN_RAPPI_ADDRESS_IDS: tuple[str, ...] = ("roma-001", "condesa-001", "delvalle-001")


def _normalize(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else " " for ch in value).strip()


def match_product(name: str, products: Iterable[ProductSpec] = PRODUCTS) -> ProductSpec:
    normalized = _normalize(name)
    tokens = {part for part in normalized.split() if part}

    best = None
    best_score = -1
    for product in products:
        candidates: List[str] = [product.canonical_name, *product.aliases]
        for candidate in candidates:
            candidate_tokens = {part for part in _normalize(candidate).split() if part}
            score = len(tokens & candidate_tokens)
            if candidate_tokens <= tokens:
                score += 5
            if score > best_score:
                best = product
                best_score = score

    if best is None or best_score <= 0:
        raise ValueError(f"Could not match product name: {name}")
    return best
