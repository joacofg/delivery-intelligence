from __future__ import annotations

import argparse
import logging
from pathlib import Path

from ci.analysis import run_analysis
from ci.catalog import ANCHOR_ADDRESSES
from ci.pipeline import copy_snapshot_dataset
from ci.reporting import generate_report
from ci.scrapers.live import run_live_scrape


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = REPO_ROOT / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
ANALYSIS_DIR = OUTPUTS_DIR / "analysis"
REPORT_DIR = OUTPUTS_DIR / "reports"
DEFAULT_LIVE_ADDRESS_IDS = ("roma-001", "condesa-001", "delvalle-001")


def _latest_raw_json() -> Path:
    candidates = sorted(RAW_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No raw dataset found. Run `python -m ci scrape --mode snapshot` or `--mode live` first.")
    return candidates[0]


def _select_live_addresses(args) -> list:
    selected_addresses = list(ANCHOR_ADDRESSES)
    if args.address_id:
        selected_addresses = [address for address in selected_addresses if address.address_id == args.address_id]
        if not selected_addresses:
            raise ValueError(f"Unknown address id: {args.address_id}")
        return selected_addresses

    if args.all_addresses:
        if args.limit_addresses:
            return selected_addresses[: args.limit_addresses]
        return selected_addresses

    has_live_filter = any((args.platform, args.limit_addresses))
    if not has_live_filter:
        selected_addresses = [
            address for address in selected_addresses if address.address_id in DEFAULT_LIVE_ADDRESS_IDS
        ]
        logging.getLogger(__name__).info(
            "Live scrape defaulting to demo-safe addresses: %s. Use --all-addresses for the full sweep.",
            ", ".join(address.address_id for address in selected_addresses),
        )
        return selected_addresses

    if args.limit_addresses:
        selected_addresses = selected_addresses[: args.limit_addresses]
    return selected_addresses


def handle_scrape(args) -> None:
    if args.mode == "snapshot":
        copy_snapshot_dataset(RAW_DIR, run_id="snapshot-demo")
        return

    selected_addresses = _select_live_addresses(args)
    platforms = [args.platform] if args.platform else None
    run_live_scrape(RAW_DIR, addresses=selected_addresses, platforms=platforms, debug_evidence=args.debug_evidence)


def handle_analyze(args) -> None:
    raw_json = Path(args.input) if args.input else _latest_raw_json()
    run_analysis(raw_json, ANALYSIS_DIR)


def handle_report(args) -> None:
    raw_json = Path(args.input) if args.input else _latest_raw_json()
    analysis = run_analysis(raw_json, ANALYSIS_DIR)
    generate_report(analysis, REPORT_DIR)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Competitive intelligence pipeline for the Rappi challenge.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scrape = subparsers.add_parser("scrape", help="Run scraping or snapshot ingestion.")
    scrape.add_argument("--mode", choices=["snapshot", "live"], default="snapshot")
    scrape.add_argument("--limit-addresses", type=int, help="Optional limit for live runs.")
    scrape.add_argument("--platform", choices=["rappi", "uber_eats", "didi_food"], help="Run a single platform.")
    scrape.add_argument("--address-id", help="Run a single known anchor address.")
    scrape.add_argument("--all-addresses", action="store_true", help="Run the full live address sweep instead of demo-safe defaults.")
    scrape.add_argument("--debug-evidence", action="store_true", help="Persist all candidate payloads for debugging.")
    scrape.set_defaults(func=handle_scrape)

    analyze = subparsers.add_parser("analyze", help="Analyze latest raw dataset.")
    analyze.add_argument("--input", help="Optional raw JSON path.")
    analyze.set_defaults(func=handle_analyze)

    report = subparsers.add_parser("report", help="Generate HTML/PDF report.")
    report.add_argument("--input", help="Optional raw JSON path.")
    report.set_defaults(func=handle_report)

    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
