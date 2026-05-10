import json
from pathlib import Path

from ci.catalog import ANCHOR_ADDRESSES
from ci.scrapers.base import persist_evidence_artifacts


def test_persist_evidence_artifacts_writes_payloads_and_metadata(tmp_path: Path) -> None:
    target = tmp_path / "evidence"
    meta = persist_evidence_artifacts(
        evidence_root=target,
        run_id="live-001",
        platform="rappi",
        address=ANCHOR_ADDRESSES[1],
        payloads=[{"kind": "irrelevant"}, {"store": {"name": "McDonald's"}}],
        chosen_index=1,
        scrape_stage="extract_menu",
        extractor_used="dom",
        failure_category="",
        duration_ms=4200,
        screenshot_path="outputs/raw/example.png",
    )

    evidence_dir = Path(meta["evidence_dir"])
    assert evidence_dir.exists()
    assert (evidence_dir / "payload-001.json").exists()
    assert (evidence_dir / "payload-002.json").exists()
    metadata = json.loads((evidence_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["chosen_payload_path"].endswith("payload-002.json")
    assert metadata["scrape_stage"] == "extract_menu"
