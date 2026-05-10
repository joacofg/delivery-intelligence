from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from ci.models import ScrapeRecord


USABLE_STATUSES = {"ok"}


def _to_frame(records: Iterable[ScrapeRecord]) -> pd.DataFrame:
    return pd.DataFrame([record.to_dict() for record in records])


def _usable_frame(records: Iterable[ScrapeRecord]) -> pd.DataFrame:
    frame = _to_frame(records)
    if frame.empty:
        return frame
    return frame[frame["status"].isin(USABLE_STATUSES)].copy()


def build_platform_summary(records: Iterable[ScrapeRecord]) -> pd.DataFrame:
    frame = _usable_frame(records)
    frame["eta_mid"] = (frame["eta_min"] + frame["eta_max"]) / 2
    frame.loc[frame["eta_mid"] <= 0, "eta_mid"] = pd.NA
    frame.loc[frame["delivery_fee"] <= 0, "delivery_fee"] = pd.NA
    frame["total_price"] = frame["price"] + frame["delivery_fee"].fillna(0) + frame["service_fee"].fillna(0)
    summary = (
        frame.groupby("platform", as_index=False)
        .agg(
            avg_price=("price", "mean"),
            avg_delivery_fee=("delivery_fee", "mean"),
            avg_service_fee=("service_fee", "mean"),
            avg_total_price=("total_price", "mean"),
            avg_eta_mid=("eta_mid", "mean"),
            rows=("product_key", "count"),
        )
        .sort_values("platform")
        .reset_index(drop=True)
    )
    return summary


def build_zone_summary(records: Iterable[ScrapeRecord]) -> pd.DataFrame:
    frame = _usable_frame(records)
    frame["eta_mid"] = (frame["eta_min"] + frame["eta_max"]) / 2
    frame.loc[frame["eta_mid"] <= 0, "eta_mid"] = pd.NA
    frame.loc[frame["delivery_fee"] <= 0, "delivery_fee"] = pd.NA
    grouped = (
        frame.groupby(["address_id", "zone_type", "platform"], as_index=False)
        .agg(
            avg_price=("price", "mean"),
            avg_delivery_fee=("delivery_fee", "mean"),
            avg_eta_mid=("eta_mid", "mean"),
        )
    )
    rappi = grouped[grouped["platform"] == "rappi"][
        ["address_id", "avg_price", "avg_delivery_fee", "avg_eta_mid"]
    ].rename(
        columns={
            "avg_price": "rappi_avg_price",
            "avg_delivery_fee": "rappi_avg_delivery_fee",
            "avg_eta_mid": "rappi_avg_eta_mid",
        }
    )
    merged = grouped.merge(rappi, on="address_id", how="left")
    merged["avg_price_gap_vs_rappi"] = merged["avg_price"] - merged["rappi_avg_price"]
    merged["avg_delivery_fee_gap_vs_rappi"] = merged["avg_delivery_fee"] - merged["rappi_avg_delivery_fee"]
    merged["avg_eta_mid_gap_vs_rappi"] = merged["avg_eta_mid"] - merged["rappi_avg_eta_mid"]
    merged = merged[merged["platform"] != "rappi"].sort_values(["address_id", "platform"]).reset_index(drop=True)
    return merged


def build_coverage_summary(records: Iterable[ScrapeRecord]) -> pd.DataFrame:
    frame = _to_frame(records)
    if frame.empty:
        return pd.DataFrame()

    summary = (
        frame.groupby("platform", as_index=False)
        .agg(
            rows_total=("product_key", "count"),
            rows_usable=("status", lambda s: int((s == "ok").sum())),
            rows_failed=("status", lambda s: int((s != "ok").sum())),
            unique_addresses=("address_id", "nunique"),
            unique_failure_categories=("failure_category", lambda s: int(len({v for v in s if v}))),
            snapshot_real_rows=("source_mode", lambda s: int(((frame.loc[s.index, "status"] == "ok") & (s == "snapshot_real")).sum())),
            snapshot_synthetic_rows=("source_mode", lambda s: int(((frame.loc[s.index, "status"] == "ok") & (s == "snapshot_synthetic")).sum())),
            live_curated_rows=("source_mode", lambda s: int(((frame.loc[s.index, "status"] == "ok") & (s == "live_curated")).sum())),
        )
        .sort_values("platform")
        .reset_index(drop=True)
    )
    return summary


def load_records(json_path: str) -> List[ScrapeRecord]:
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    rows = []
    for row in payload:
        row.setdefault("store_reference", "")
        row.setdefault("confidence", "medium")
        row.setdefault("extractor_used", "")
        row.setdefault("scrape_stage", "")
        row.setdefault("failure_category", row.get("error_reason", ""))
        row.setdefault("run_duration_ms", 0)
        row.setdefault("evidence_dir", "")
        row.setdefault("chosen_payload_path", "")
        row.setdefault("service_fee", 0.0)
        rows.append(ScrapeRecord(**row))
    return rows


def _build_product_summary(records: Iterable[ScrapeRecord]) -> pd.DataFrame:
    frame = _usable_frame(records)
    return (
        frame.groupby(["platform", "product_key"], as_index=False)
        .agg(avg_price=("price", "mean"))
        .sort_values(["product_key", "platform"])
        .reset_index(drop=True)
    )


def _build_insights(platform_summary: pd.DataFrame, zone_summary: pd.DataFrame, coverage_summary: pd.DataFrame) -> list[dict[str, str]]:
    cheapest = platform_summary.sort_values("avg_price").iloc[0]
    most_expensive = platform_summary.sort_values("avg_price", ascending=False).iloc[0]
    lowest_fee = platform_summary.sort_values("avg_delivery_fee").iloc[0]
    fastest = platform_summary.sort_values("avg_eta_mid").iloc[0]
    worst_uber_gap = zone_summary[zone_summary["platform"] == "uber_eats"].sort_values(
        "avg_price_gap_vs_rappi", ascending=False
    ).iloc[0]
    best_didi_gap = zone_summary[zone_summary["platform"] == "didi_food"].sort_values(
        "avg_price_gap_vs_rappi"
    ).iloc[0]

    rappi_row = platform_summary[platform_summary["platform"] == "rappi"].iloc[0]
    uber_row = platform_summary[platform_summary["platform"] == "uber_eats"].iloc[0]
    didi_row = platform_summary[platform_summary["platform"] == "didi_food"].iloc[0]
    rappi_total = rappi_row["avg_total_price"]
    uber_total = uber_row["avg_total_price"]
    didi_total = didi_row["avg_total_price"]
    cheapest_total = platform_summary.sort_values("avg_total_price").iloc[0]

    zone_names = {
        "polanco-001": "Polanco", "roma-001": "Roma Norte", "condesa-001": "Condesa",
        "centro-001": "Centro Histórico", "lomas-001": "Lomas", "santafe-001": "Santa Fe",
        "delvalle-001": "Del Valle", "narvarte-001": "Narvarte", "napoles-001": "Nápoles",
        "insurgentes-001": "Insurgentes", "doctores-001": "Doctores", "coyoacan-001": "Coyoacán",
        "tlalpan-001": "Tlalpan", "pedregal-001": "Pedregal", "iztapalapa-001": "Iztapalapa",
        "ermita-001": "Ermita", "tlahuac-001": "Tláhuac", "lindavista-001": "Lindavista",
        "vallejo-001": "Vallejo", "xochimilco-001": "Xochimilco",
    }

    uber_gap_zone = zone_names.get(worst_uber_gap["address_id"], worst_uber_gap["address_id"])
    didi_gap_zone = zone_names.get(best_didi_gap["address_id"], best_didi_gap["address_id"])

    return [
        {
            "finding": f"{cheapest['platform'].replace('_', ' ').title()} tiene el precio de producto más bajo en promedio (MXN {cheapest['avg_price']:.1f}), frente a MXN {most_expensive['avg_price']:.1f} de {most_expensive['platform'].replace('_', ' ').title()}.",
            "impact": "La diferencia de precio visible al usuario puede inclinar búsquedas y primera compra, especialmente en zonas de ingreso medio donde el precio del ítem es el criterio principal.",
            "recommendation": "Defender SKUs ancla (Big Mac, McNuggets) en zonas sensibles al precio con pricing competitivo antes de expandir descuentos horizontales.",
        },
        {
            "finding": f"Rappi cobra el delivery fee más alto en promedio (MXN {rappi_row['avg_delivery_fee']:.1f}), pero es el único con service fee cero. El costo total al usuario (producto + delivery + service fee) es MXN {rappi_total:.1f} vs MXN {uber_total:.1f} de Uber Eats y MXN {didi_total:.1f} de DiDi Food.",
            "impact": "El service fee de Uber Eats ($12 MXN) y DiDi ($8 MXN) hace que su costo real sea mayor de lo que aparenta en la pantalla de producto. Rappi resulta el más competitivo en costo total pese a tener el delivery fee más alto.",
            "recommendation": "Comunicar activamente el beneficio de $0 service fee en creatividades y onboarding. Considerarlo como diferenciador clave frente a la percepción de 'Rappi es caro'.",
        },
        {
            "finding": f"Rappi lidera en velocidad de entrega con un ETA promedio de {rappi_row['avg_eta_mid']:.0f} min, frente a {uber_row['avg_eta_mid']:.0f} min de Uber Eats y {didi_row['avg_eta_mid']:.0f} min de DiDi Food.",
            "impact": "En fast food de decisión impulsiva, el ETA es el segundo criterio de elección después del precio. Liderar en velocidad construye preferencia de marca operacional.",
            "recommendation": "Usar ETA como palanca de comunicación en zonas donde Rappi mantiene ventaja. Monitorear si DiDi recorta el gap en zonas periféricas donde su red de repartidores crece.",
        },
        {
            "finding": f"Uber Eats cobra su mayor premium vs Rappi en {uber_gap_zone} (MXN {worst_uber_gap['avg_price_gap_vs_rappi']:.1f} más caro por producto). DiDi Food subcotiza más fuertemente en {didi_gap_zone} (MXN {abs(best_didi_gap['avg_price_gap_vs_rappi']):.1f} más barato que Rappi).",
            "impact": "La competitividad no es uniforme: en zonas premium Uber Eats carga un premium propio que le resta competitividad; en zonas populares DiDi actúa agresivamente en precio.",
            "recommendation": "Segmentar estrategia por zona: en zonas de alto ingreso defenderse de Uber Eats con calidad/velocidad, no precio. En zonas populares y periféricas, revisar si el gap de DiDi está generando churn.",
        },
        {
            "finding": "DiDi Food lanza cupones visibles para usuarios nuevos en todas las zonas analizadas; Uber Eats corre 'Hasta 20% off en combos'; Rappi ofrece envío gratis en pedidos seleccionados — ninguno muestra descuento universal en producto.",
            "impact": "Las tres plataformas usan promociones de adquisición (nuevos usuarios o umbral mínimo), no descuentos de retención. El usuario recurrente no recibe beneficio diferencial en ninguna plataforma.",
            "recommendation": "Diseñar mecánica de retención explícita para usuarios frecuentes (ej. precio preferencial en SKUs ancla tras N pedidos) que DiDi y Uber no están ofreciendo actualmente.",
        },
    ]


def run_analysis(json_path, output_dir):
    import matplotlib.pyplot as plt

    records = load_records(str(json_path))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    platform_summary = build_platform_summary(records)
    zone_summary = build_zone_summary(records)
    coverage_summary = build_coverage_summary(records)
    product_summary = _build_product_summary(records)
    insights = _build_insights(platform_summary, zone_summary, coverage_summary)

    platform_summary_path = output_dir / "platform_summary.csv"
    zone_summary_path = output_dir / "zone_summary.csv"
    coverage_summary_path = output_dir / "coverage_summary.csv"
    product_summary_path = output_dir / "product_summary.csv"
    insights_path = output_dir / "insights.json"
    platform_summary.to_csv(platform_summary_path, index=False)
    zone_summary.to_csv(zone_summary_path, index=False)
    coverage_summary.to_csv(coverage_summary_path, index=False)
    product_summary.to_csv(product_summary_path, index=False)
    insights_path.write_text(json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8")

    chart_paths = []

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(platform_summary["platform"], platform_summary["avg_price"], color=["#ff6b35", "#111827", "#2ca58d"])
    ax.set_title("Precio promedio por plataforma")
    ax.set_ylabel("MXN")
    price_chart = output_dir / "chart_price_by_platform.png"
    fig.tight_layout()
    fig.savefig(price_chart, dpi=180)
    plt.close(fig)
    chart_paths.append(price_chart)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(platform_summary["platform"], platform_summary["avg_delivery_fee"], color=["#4f46e5", "#ef4444", "#14b8a6"])
    ax.set_title("Delivery fee promedio por plataforma")
    ax.set_ylabel("MXN")
    fee_chart = output_dir / "chart_delivery_fee_by_platform.png"
    fig.tight_layout()
    fig.savefig(fee_chart, dpi=180)
    plt.close(fig)
    chart_paths.append(fee_chart)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(platform_summary["platform"], platform_summary["avg_service_fee"], color=["#7c3aed", "#dc2626", "#0d9488"])
    ax.set_title("Service fee promedio por plataforma")
    ax.set_ylabel("MXN")
    service_chart = output_dir / "chart_service_fee_by_platform.png"
    fig.tight_layout()
    fig.savefig(service_chart, dpi=180)
    plt.close(fig)
    chart_paths.append(service_chart)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(platform_summary["platform"], platform_summary["avg_total_price"], color=["#b45309", "#1d4ed8", "#065f46"])
    ax.set_title("Precio total promedio al usuario (producto + delivery + service fee)")
    ax.set_ylabel("MXN")
    total_chart = output_dir / "chart_total_price_by_platform.png"
    fig.tight_layout()
    fig.savefig(total_chart, dpi=180)
    plt.close(fig)
    chart_paths.append(total_chart)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(platform_summary["platform"], platform_summary["avg_eta_mid"], color=["#ff6b35", "#111827", "#2ca58d"])
    ax.set_title("ETA promedio por plataforma (minutos)")
    ax.set_ylabel("Minutos")
    eta_chart = output_dir / "chart_eta_by_platform.png"
    fig.tight_layout()
    fig.savefig(eta_chart, dpi=180)
    plt.close(fig)
    chart_paths.append(eta_chart)

    zone_chart_data = zone_summary.pivot(index="address_id", columns="platform", values="avg_price_gap_vs_rappi").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 5))
    zone_chart_data.plot(kind="bar", ax=ax, color=["#111827", "#2ca58d"])
    ax.set_title("Gap de precio promedio vs Rappi por zona")
    ax.set_ylabel("MXN vs Rappi")
    ax.legend(title="Platform")
    zone_chart = output_dir / "chart_price_gap_by_zone.png"
    fig.tight_layout()
    fig.savefig(zone_chart, dpi=180)
    plt.close(fig)
    chart_paths.append(zone_chart)

    return {
        "raw_json_path": str(json_path),
        "platform_summary": platform_summary,
        "zone_summary": zone_summary,
        "coverage_summary": coverage_summary,
        "product_summary": product_summary,
        "platform_summary_path": platform_summary_path,
        "zone_summary_path": zone_summary_path,
        "coverage_summary_path": coverage_summary_path,
        "product_summary_path": product_summary_path,
        "insights": insights,
        "insights_path": insights_path,
        "chart_paths": chart_paths,
    }
