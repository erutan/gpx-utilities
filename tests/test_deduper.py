#!/usr/bin/env python3
"""Tests for gpx_waypoint_deduper."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import gpxpy

from gpx_waypoint_deduper.gpx_waypoint_deduper import GPXDeduplicator, main

SAMPLE_GPX_DUPES = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <wpt lat="37.0" lon="-119.0"><name>A</name><time>2024-01-01T00:00:00Z</time></wpt>
  <wpt lat="37.0" lon="-119.0"><name>A</name><time>2024-01-01T00:00:00Z</time></wpt>
  <wpt lat="38.0" lon="-120.0"><name>B</name><time>2024-01-02T00:00:00Z</time></wpt>
</gpx>
"""

SAMPLE_GPX_NO_DUPES = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <wpt lat="37.0" lon="-119.0"><name>A</name><time>2024-01-01T00:00:00Z</time></wpt>
  <wpt lat="38.0" lon="-120.0"><name>B</name><time>2024-01-02T00:00:00Z</time></wpt>
</gpx>
"""

SAMPLE_GPX_NAME_DUPES = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <wpt lat="37.0" lon="-119.0"><name>Same</name></wpt>
  <wpt lat="38.0" lon="-120.0"><name>Same</name></wpt>
  <wpt lat="39.0" lon="-121.0"><name>Unique</name></wpt>
</gpx>
"""

SAMPLE_GPX_NAMESPACED = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
</gpx>
"""


def test_dedup_removes_duplicate():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1
        assert dedup.total_waypoints == 3

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.waypoints) == 2


def test_dedup_no_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_NO_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 0


def test_dedup_coords_strategy():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="coords")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1


def test_dedup_name_strategy():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_NAME_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="name")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.waypoints) == 2


def test_dedup_time_strategy():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1


def test_dedup_hash_strategy():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="hash")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1


def test_dedup_keep_last():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords", keep_last=True)
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1


def test_dedup_verbose(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords", verbose=True)
        dedup.process_gpx(str(src), str(out))

        captured = capsys.readouterr()
        assert "Found 3 waypoints" in captured.out
        assert "Using strategy: time-coords" in captured.out
        assert "Duplicate found" in captured.out


def test_dedup_verbose_no_key(capsys):
    """Waypoints without time in time-coords strategy should warn."""
    gpx_no_time = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
</gpx>
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(gpx_no_time, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords", verbose=True)
        dedup.process_gpx(str(src), str(out))

        captured = capsys.readouterr()
        assert "Could not extract key" in captured.out


def test_dedup_state_resets_between_calls():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out1 = Path(tmpdir) / "output1.gpx"
        out2 = Path(tmpdir) / "output2.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords")
        dedup.process_gpx(str(src), str(out1))
        assert dedup.duplicates_removed == 1

        dedup.process_gpx(str(src), str(out2))
        assert dedup.duplicates_removed == 1  # reset, not accumulated to 2


def test_dedup_default_output_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX_NO_DUPES, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="time-coords")
        success = dedup.process_gpx(str(src))

        assert success is True
        expected = Path(tmpdir) / "input_dedup.gpx"
        assert expected.exists()


def test_dedup_namespaced_gpx():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_NAMESPACED, encoding="utf-8")

        dedup = GPXDeduplicator(strategy="coords")
        success = dedup.process_gpx(str(src), str(out))

        assert success is True
        assert dedup.duplicates_removed == 1


def test_dedup_invalid_xml():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text("not xml", encoding="utf-8")

        dedup = GPXDeduplicator()
        success = dedup.process_gpx(str(src))
        assert success is False


def test_main_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0


def test_main_missing_file():
    with patch.object(sys, "argv", ["prog", "/nonexistent/file.gpx"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_main_non_gpx_extension(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.txt"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_NO_DUPES, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

        captured = capsys.readouterr()
        assert "Warning: Input file does not have .gpx extension" in captured.err


def test_main_with_strategy():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out), "-s", "hash"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
