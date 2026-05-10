# Rappi Competitive Intelligence

Competitive intelligence pipeline for the Rappi AI Engineer technical challenge. Scrapes and compares Rappi, Uber Eats, and DiDi Food across 20 representative CDMX zones using McDonald's as a reference chain.

## Quick start

```bash
make bootstrap          # create .venv, install deps, install Playwright Chromium
make all                # snapshot → analyze → report (no live scraping needed)
```

The full report lands at `outputs/reports/competitive_intelligence_report.html` and `.pdf`.

## What the system collects

| Metric | Field | Notes |
|---|---|---|
| Product price | `price` | 4 SKUs: Big Mac, Combo mediano, McNuggets 10, Coca-Cola |
| Delivery fee | `delivery_fee` | As shown before discounts |
| Service fee | `service_fee` | Platform commission shown at checkout |
| ETA | `eta_min`, `eta_max` | Range or midpoint shown to user |
| Active promos | `promo_text` | Visible discount/coupon text |
| Total cost | derived | price + delivery_fee + service_fee |
| Availability | `status` (ok / blocked) | Whether the store was reachable |

## Coverage: 20 CDMX zones

The 20 zones were selected to cover the full socioeconomic and geographic diversity of CDMX. One McDonald's store per zone is used as the reference point for cross-platform comparison.

| Address ID | Zone | Type | Rationale |
|---|---|---|---|
| polanco-001 | Polanco | high_income | Top-tier premium zone; highest willingness-to-pay |
| lomas-001 | Lomas de Chapultepec | high_income | Affluent west, lower density than Polanco |
| santafe-001 | Santa Fe | business | Corporate hub; office-worker demand profile |
| pedregal-001 | Pedregal | high_income_south | Southern premium zone with distinct delivery dynamics |
| roma-001 | Roma Norte | central | Dense, young, high app-usage — core Rappi heartland |
| condesa-001 | Condesa | central | Adjacent to Roma; strong brand loyalty zone |
| centro-001 | Centro Histórico | historic | High foot traffic; different delivery logistics |
| insurgentes-001 | Insurgentes Sur | commercial_corridor | Major artery; commuter + office demand |
| delvalle-001 | Del Valle | residential | Mid-high residential; family order profile |
| narvarte-001 | Narvarte | residential | Emerging residential; price-sensitive segment |
| napoles-001 | Nápoles | residential_mid | Transitional zone between central and south |
| doctores-001 | Doctores / Roma Sur | central_working | Working-class central; high delivery volume |
| coyoacan-001 | Coyoacán | family | Family-oriented south; weekend demand peaks |
| tlalpan-001 | Tlalpan / Coapa | peripheral_south | Southern periphery with large shopping mall anchor |
| iztapalapa-001 | Iztapalapa | high_density | Highest-population borough in CDMX; key expansion zone |
| ermita-001 | Ermita Iztapalapa | high_density_east | East corridor; competitive pressure from DiDi |
| tlahuac-001 | Tláhuac | peripheral_east | Far east; tests last-mile delivery limits |
| lindavista-001 | Lindavista | peripheral | North; family zone with growing order volume |
| vallejo-001 | Industrial Vallejo | working_class | Industrial north; price-sensitive workforce |
| xochimilco-001 | Xochimilco | peripheral_south | Southern periphery; tourist + residential mix |

## Data quality: real vs synthetic

The pipeline runs in two modes:

| `source_mode` | Meaning | Rows in default run |
|---|---|---|
| `snapshot_real` | Curated from actual Rappi pages | 12 (3 golden Rappi addresses × 4 products) |
| `snapshot_synthetic` | Seeded benchmark; calibrated to real-world ranges | 228 |
| `live_curated` | Live Playwright extraction | Depends on run |

The HTML report includes a **Coverage & confidence** section that makes this distinction explicit so evaluators can tell trustworthy rows from placeholders.

## Commands

```bash
# Full reproducible pipeline (no browser needed for snapshot mode)
make all

# Live scraping — 3 golden addresses (roma-001, condesa-001, delvalle-001)
make demo-live

# Live scraping — all 20 addresses
make live-all

# Single platform + address
python -m ci scrape --mode live --platform rappi --address-id roma-001 --debug-evidence

# Analyze an existing JSON run
python -m ci analyze --input outputs/raw/<file>.json

# Generate report from latest analysis
python -m ci report
```

Useful flags: `--platform rappi|uber_eats|didi_food`, `--address-id <id>`, `--limit-addresses N`, `--all-addresses`, `--debug-evidence`.

## Outputs

```
outputs/
  raw/                        # JSON + CSV per run (gitignored — regenerate with make all)
    evidence/<run>/<platform>/<address>/
      screenshot.png
      payload-001.json
      metadata.json
  analysis/                   # CSVs + charts (committed)
    platform_summary.csv
    zone_summary.csv
    coverage_summary.csv
    product_summary.csv
    chart_*.png
  reports/                    # Final deliverable (committed)
    competitive_intelligence_report.html
    competitive_intelligence_report.pdf
```

## Tests

```bash
make test              # or: python3 -m pytest -q
pytest -q tests/test_adapters.py   # single file
```

21 tests cover: normalization, product matching, snapshot generation, analysis correctness, evidence persistence, adapter parsing (all 3 platforms), and report generation.

## Known limitations

- **Uber Eats and DiDi Food** live coverage relies on DOM extraction from public guest-mode pages. ETA and delivery fee are scraped via regex on visible text; these may shift if the sites change layout.
- **Rappi** has the strongest live coverage. The 3 golden addresses use curated real-page data; the other 17 fall back to calibrated synthetic values in snapshot mode.
- **Service fee** for Uber Eats ($12 MXN) and DiDi ($8 MXN) is captured in snapshot mode as a known constant. Live extraction of service fees requires reaching the checkout step, which is behind authentication on all three platforms.
- **PDF export** depends on local Playwright Chromium. If it fails, the HTML report is the primary deliverable.

## Ethics and cost

- Guest-mode only — no accounts, no authentication.
- Rate limiting: Playwright waits between requests; live mode scrapes sequentially with delays.
- No paid proxies or external APIs. Default cost: **$0**.
- In a real production setting, recurring competitive scraping should go through legal review before deployment.
