from __future__ import annotations

import base64
from pathlib import Path

from jinja2 import Template


REPORT_TEMPLATE = Template(
    """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Rappi Competitive Intelligence Report</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f4efe7;
        --ink: #1f2937;
        --muted: #6b7280;
        --accent: #ff6b35;
        --card: #fffdf8;
      }
      body {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        background: linear-gradient(180deg, #f7f1e8 0%, #f2f4f7 100%);
        color: var(--ink);
      }
      main {
        max-width: 1040px;
        margin: 0 auto;
        padding: 48px 28px 72px;
      }
      h1, h2, h3 {
        margin: 0 0 12px;
      }
      p {
        line-height: 1.55;
      }
      .hero {
        background: var(--card);
        border-radius: 20px;
        padding: 28px;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
      }
      .metrics {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        margin: 24px 0 40px;
      }
      .metric, .section {
        background: rgba(255, 253, 248, 0.95);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
      }
      .metric strong {
        display: block;
        font-size: 1.8rem;
        margin-bottom: 8px;
      }
      .charts {
        display: grid;
        gap: 18px;
      }
      img {
        width: 100%;
        border-radius: 14px;
        background: white;
      }
      ol {
        padding-left: 20px;
      }
      li {
        margin-bottom: 12px;
      }
      .muted {
        color: var(--muted);
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="muted">CDMX · McDonald's · Snapshot-backed benchmark</p>
        <h1>Rappi Competitive Intelligence Report</h1>
        <p>Benchmark de Rappi, Uber Eats y DiDi Food en 20 zonas ancla de CDMX usando 4 productos comparables de McDonald's y métricas de precio de producto, delivery fee, service fee, ETA y promociones activas.</p>
      </section>

      <section class="metrics">
        {% for metric in metrics %}
        <article class="metric">
          <span class="muted">{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <div>{{ metric.note }}</div>
        </article>
        {% endfor %}
      </section>

      <section class="section">
        <h2>Top 5 insights</h2>
        <ol>
          {% for insight in insights %}
          <li>
            <strong>Finding:</strong> {{ insight.finding }}<br>
            <strong>Impacto:</strong> {{ insight.impact }}<br>
            <strong>Recomendación:</strong> {{ insight.recommendation }}
          </li>
          {% endfor %}
        </ol>
      </section>

      <section class="section">
        <h2>Coverage & confidence</h2>
        <p>El benchmark mezcla evidencia live/curada y snapshot sintético. Esta sección muestra qué tan confiable es cada plataforma en la corrida analizada.</p>
        <table style="width:100%; border-collapse: collapse;">
          <thead>
            <tr>
              <th style="text-align:left; padding:8px 0;">Platform</th>
              <th style="text-align:left; padding:8px 0;">Rows</th>
              <th style="text-align:left; padding:8px 0;">Usable</th>
              <th style="text-align:left; padding:8px 0;">Real</th>
              <th style="text-align:left; padding:8px 0;">Synthetic</th>
            </tr>
          </thead>
          <tbody>
            {% for row in coverage_rows %}
            <tr>
              <td style="padding:6px 0;">{{ row.platform }}</td>
              <td style="padding:6px 0;">{{ row.rows_total }}</td>
              <td style="padding:6px 0;">{{ row.rows_usable }}</td>
              <td style="padding:6px 0;">{{ row.live_curated_rows + row.snapshot_real_rows }}</td>
              <td style="padding:6px 0;">{{ row.snapshot_synthetic_rows }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </section>

      <section class="section charts">
        <h2>Visualizaciones</h2>
        {% for chart in charts %}
        <figure>
          <img src="{{ chart }}" alt="Chart">
        </figure>
        {% endfor %}
      </section>

      <section class="section">
        <h2>Metodología</h2>
        <p>Se compararon Rappi, Uber Eats y DiDi Food en flujo guest, con snapshot reproducible para evitar dependencia del estado de los sitios el día de la demo. El output raw se guarda en CSV y JSON y el análisis resume gaps de pricing, delivery fee y ETA por plataforma y por zona.</p>
      </section>
    </main>
  </body>
</html>
"""
)


def _render_pdf_if_possible(html_path: Path, pdf_path: Path) -> Path | None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.pdf(path=str(pdf_path), format="A4", print_background=True)
            browser.close()
        return pdf_path
    except Exception:
        return None


def generate_report(analysis, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    platform_summary = analysis["platform_summary"]
    coverage_summary = analysis["coverage_summary"]
    cheapest = platform_summary.sort_values("avg_price").iloc[0]
    fastest = platform_summary.sort_values("avg_eta_mid").iloc[0]
    lowest_fee = platform_summary.sort_values("avg_delivery_fee").iloc[0]
    lowest_total = platform_summary.sort_values("avg_total_price").iloc[0]

    metrics = [
        {
            "label": "Precio de producto más bajo",
            "value": cheapest["platform"].replace("_", " ").title(),
            "note": f"Precio promedio: MXN {cheapest['avg_price']:.1f}",
        },
        {
            "label": "Menor delivery fee",
            "value": lowest_fee["platform"].replace("_", " ").title(),
            "note": f"Fee promedio: MXN {lowest_fee['avg_delivery_fee']:.1f}",
        },
        {
            "label": "Mejor ETA promedio",
            "value": fastest["platform"].replace("_", " ").title(),
            "note": f"ETA medio: {fastest['avg_eta_mid']:.1f} min",
        },
        {
            "label": "Menor costo total al usuario",
            "value": lowest_total["platform"].replace("_", " ").title(),
            "note": f"Producto + delivery + service fee: MXN {lowest_total['avg_total_price']:.1f}",
        },
    ]

    chart_paths = [Path(path) for path in analysis["chart_paths"]]
    chart_data_uris = [
        f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
        for p in chart_paths
    ]
    html = REPORT_TEMPLATE.render(
        metrics=metrics,
        insights=analysis["insights"],
        charts=chart_data_uris,
        coverage_rows=coverage_summary.to_dict(orient="records"),
    )

    html_path = output_dir / "competitive_intelligence_report.html"
    html_path.write_text(html, encoding="utf-8")
    pdf_path = output_dir / "competitive_intelligence_report.pdf"
    rendered_pdf = _render_pdf_if_possible(html_path, pdf_path)

    return {"html_path": html_path, "pdf_path": rendered_pdf}
