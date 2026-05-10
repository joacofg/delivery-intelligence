from pathlib import Path

from ci.analysis import run_analysis
from ci.pipeline import copy_snapshot_dataset
from ci.reporting import generate_report


def test_analysis_and_reporting_generate_expected_artifacts(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    analysis_dir = tmp_path / "analysis"
    report_dir = tmp_path / "report"

    json_path, _, _ = copy_snapshot_dataset(raw_dir)
    analysis = run_analysis(json_path, analysis_dir)
    report = generate_report(analysis, report_dir)

    assert (analysis_dir / "platform_summary.csv").exists()
    assert (analysis_dir / "zone_summary.csv").exists()
    assert (analysis_dir / "coverage_summary.csv").exists()
    assert len(analysis["chart_paths"]) == 6
    assert len(analysis["insights"]) == 5
    assert report["html_path"].exists()
    assert "Top 5 insights" in report["html_path"].read_text(encoding="utf-8")
    assert "Coverage & confidence" in report["html_path"].read_text(encoding="utf-8")
