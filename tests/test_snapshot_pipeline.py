from pathlib import Path

from ci.pipeline import copy_snapshot_dataset


def test_copy_snapshot_dataset_writes_json_and_csv_with_hybrid_origins(tmp_path: Path) -> None:
    json_path, csv_path, records = copy_snapshot_dataset(tmp_path)

    assert json_path.exists()
    assert csv_path.exists()
    assert len(records) >= 90
    assert any(record.source_mode == "snapshot_real" and record.platform == "rappi" for record in records)
    assert any(record.source_mode == "snapshot_synthetic" and record.platform == "uber_eats" for record in records)
