#!/usr/bin/env python3
"""Tests for gpx_waypoint_splitter."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import gpxpy

from gpx_waypoint_splitter.gpx_waypoint_splitter import parse_gpx, create_output_files, main

SAMPLE_GPX = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
  <wpt lat="37.1" lon="-119.1"><name>B</name></wpt>
  <wpt lat="37.2" lon="-119.2"><name>C</name></wpt>
</gpx>
"""

# GPX without namespace (exercises the fallback path)
SAMPLE_GPX_NO_NS = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
  <wpt lat="37.1" lon="-119.1"><name>B</name></wpt>
</gpx>
"""

# GPX with metadata element (non-waypoint children)
SAMPLE_GPX_WITH_METADATA = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>Test</name></metadata>
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
  <wpt lat="37.1" lon="-119.1"><name>B</name></wpt>
</gpx>
"""

SAMPLE_GPX_EMPTY = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
</gpx>
"""


def test_parse_gpx_finds_waypoints():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        gpx, count = parse_gpx(f.name)
    assert count == 3
    assert len(gpx.waypoints) == 3


def test_parse_gpx_no_namespace():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_NO_NS)
        f.flush()
        gpx, count = parse_gpx(f.name)
    assert count == 2
    assert len(gpx.waypoints) == 2


def test_parse_gpx_empty_file():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_EMPTY)
        f.flush()
        gpx, count = parse_gpx(f.name)
    assert count == 0
    assert len(gpx.waypoints) == 0


def test_parse_gpx_invalid_file():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write("not xml at all")
        f.flush()
        with pytest.raises(SystemExit):
            parse_gpx(f.name)


def test_parse_gpx_missing_file():
    with pytest.raises(SystemExit):
        parse_gpx("/nonexistent/file.gpx")


def test_split_creates_correct_number_of_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(gpx, prefix, waypoints_per_file=2)

        assert total == 3
        assert (Path(tmpdir) / "out_001.gpx").exists()
        assert (Path(tmpdir) / "out_002.gpx").exists()


def test_split_single_file_when_all_fit():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(gpx, prefix, waypoints_per_file=1000)

        assert total == 3
        assert (Path(tmpdir) / "out_001.gpx").exists()
        assert not (Path(tmpdir) / "out_002.gpx").exists()


def test_split_with_metadata_preserves_non_waypoint_elements():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX_WITH_METADATA, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(gpx, prefix, waypoints_per_file=1000)

        assert total == 2
        with open(str(Path(tmpdir) / "out_001.gpx"), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert result_gpx.name == "Test"


def test_split_empty_waypoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX_EMPTY, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(gpx, prefix, waypoints_per_file=1000)

        assert total == 0
        assert not (Path(tmpdir) / "out_001.gpx").exists()


def test_split_output_files_contain_valid_xml():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        create_output_files(gpx, prefix, waypoints_per_file=1)

        for i in range(1, 4):
            with open(str(Path(tmpdir) / f"out_{i:03d}.gpx"), 'r') as f:
                result_gpx = gpxpy.parse(f)
            assert len(result_gpx.waypoints) == 1


def test_main_basic(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")
        prefix = str(Path(tmpdir) / "out")

        with patch.object(sys, "argv", ["prog", str(src), prefix, "-w", "2"]):
            main()

        assert (Path(tmpdir) / "out_001.gpx").exists()
        assert (Path(tmpdir) / "out_002.gpx").exists()


def test_main_verbose(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")
        prefix = str(Path(tmpdir) / "out")

        with patch.object(sys, "argv", ["prog", str(src), prefix, "-v"]):
            main()

        captured = capsys.readouterr()
        assert "Detailed waypoints information" in captured.out


def test_main_verbose_empty(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX_EMPTY, encoding="utf-8")
        prefix = str(Path(tmpdir) / "out")

        with patch.object(sys, "argv", ["prog", str(src), prefix, "-v"]):
            main()

        captured = capsys.readouterr()
        assert "No waypoints found in file." in captured.out


def test_main_default_prefix():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(src)]):
            main()

        # Default prefix is the stem (no directory), so output lands in CWD
        assert Path("input_001.gpx").exists()
        Path("input_001.gpx").unlink()  # cleanup


def test_main_invalid_waypoints_per_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(src), "-w", "0"]):
            with pytest.raises(SystemExit):
                main()


# --- Input existence check tests ---


def test_main_missing_input_file():
    """Missing input file should exit with code 1."""
    with patch.object(sys, "argv", ["prog", "/nonexistent/file.gpx"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


# --- Null coordinate warning tests ---


def test_null_coordinate_warning(capsys):
    """Waypoints with null coordinates should produce a stderr warning."""
    import gpxpy.gpx as gpx_mod

    null_wpt = gpx_mod.GPXWaypoint(name="NullPoint")
    null_wpt.latitude = None
    null_wpt.longitude = None

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a GPX with a null-coord waypoint
        src = Path(tmpdir) / "input.gpx"
        gpx = gpx_mod.GPX()
        # gpxpy won't serialize null coords normally, so we use a valid wpt + patch
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        # Patch the parse result to include a null-coord waypoint
        original_parse = gpxpy.parse

        def patched_parse(f):
            gpx = original_parse(f)
            null_wpt = gpx_mod.GPXWaypoint(name="NullPoint")
            null_wpt.latitude = None
            null_wpt.longitude = None
            gpx.waypoints.append(null_wpt)
            return gpx

        with patch('gpx_waypoint_splitter.gpx_waypoint_splitter.gpxpy.parse', side_effect=patched_parse):
            gpx_result, count = parse_gpx(str(src))

        captured = capsys.readouterr()
        assert "has null coordinates" in captured.err


# --- Overwrite warning tests ---


def test_overwrite_warning(capsys):
    """Writing to an existing file should produce a stderr warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")

        # Create first set of output files
        create_output_files(gpx, prefix, waypoints_per_file=1000)

        # Re-parse (gpx object waypoints may be consumed)
        gpx2, count2 = parse_gpx(str(src))

        # Run again to trigger overwrite
        create_output_files(gpx2, prefix, waypoints_per_file=1000)

        captured = capsys.readouterr()
        assert "Overwriting existing file" in captured.err


# --- Read-back verification tests ---


def test_readback_no_spurious_warning(capsys):
    """Normal operation should not produce a read-back warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        gpx, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        create_output_files(gpx, prefix, waypoints_per_file=2)

        captured = capsys.readouterr()
        assert "Read-back verification mismatch" not in captured.err
        assert "Could not verify" not in captured.err
