#!/usr/bin/env python3
"""Tests for gpx_waypoint_combiner."""

import argparse
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import gpxpy

from gpx_waypoint_combiner.gpx_waypoint_combiner import GPXCombiner, collect_input_files, main

SAMPLE_GPX_A = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
</gpx>
"""

SAMPLE_GPX_B = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="38.0" lon="-120.0"><name>B</name></wpt>
  <wpt lat="39.0" lon="-121.0"><name>C</name></wpt>
</gpx>
"""

# Non-namespaced GPX
SAMPLE_GPX_NO_NS = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <wpt lat="40.0" lon="-122.0"><name>D</name></wpt>
</gpx>
"""

SAMPLE_GPX_EMPTY = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
</gpx>
"""

SAMPLE_GPX_INVALID = "this is not XML"


def test_extract_waypoints():
    combiner = GPXCombiner()
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_A)
        f.flush()
        wpts = combiner.extract_waypoints(f.name)
    assert len(wpts) == 1


def test_extract_waypoints_no_namespace():
    combiner = GPXCombiner()
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_NO_NS)
        f.flush()
        wpts = combiner.extract_waypoints(f.name)
    assert len(wpts) == 1


def test_extract_waypoints_missing_file():
    combiner = GPXCombiner()
    wpts = combiner.extract_waypoints("/nonexistent/file.gpx")
    assert wpts == []


def test_extract_waypoints_invalid_xml():
    combiner = GPXCombiner()
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_INVALID)
        f.flush()
        wpts = combiner.extract_waypoints(f.name)
    assert wpts == []


def test_combine_files():
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        b = Path(tmpdir) / "b.gpx"
        out = Path(tmpdir) / "combined.gpx"

        a.write_text(SAMPLE_GPX_A, encoding="utf-8")
        b.write_text(SAMPLE_GPX_B, encoding="utf-8")

        success = combiner.combine_files([str(a), str(b)], str(out))
        assert success is True
        assert out.exists()

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.waypoints) == 3


def test_combine_files_with_metadata():
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        metadata = {"name": "Test Trip", "desc": "A test collection"}
        success = combiner.combine_files([str(a)], str(out), metadata=metadata)
        assert success is True

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert result_gpx.name == "Test Trip"
        assert result_gpx.description == "A test collection"


def test_combine_files_no_waypoints():
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_EMPTY, encoding="utf-8")

        success = combiner.combine_files([str(a)], str(out))
        assert success is False


def test_combine_files_with_failed_files(capsys):
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        b = Path(tmpdir) / "b.gpx"
        out = Path(tmpdir) / "combined.gpx"

        a.write_text(SAMPLE_GPX_A, encoding="utf-8")
        b.write_text(SAMPLE_GPX_EMPTY, encoding="utf-8")

        success = combiner.combine_files([str(a), str(b)], str(out))
        assert success is True

        captured = capsys.readouterr()
        assert "Files that failed: 1" in captured.out


def test_create_combined_gpx_no_metadata():
    combiner = GPXCombiner()
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_A)
        f.flush()
        wpts = combiner.extract_waypoints(f.name)

    gpx = combiner.create_combined_gpx(wpts, metadata=None)
    assert gpx.creator == "GPX Waypoint Combiner"
    assert len(gpx.waypoints) == 1


def test_collect_input_files_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        b = Path(tmpdir) / "b.gpx"
        c = Path(tmpdir) / "c.txt"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")
        b.write_text(SAMPLE_GPX_B, encoding="utf-8")
        c.write_text("not gpx", encoding="utf-8")

        args = argparse.Namespace(
            directory=tmpdir, recursive=False, files=None
        )
        result = collect_input_files(args)
        assert len(result) == 2
        assert all(f.endswith(".gpx") for f in result)


def test_collect_input_files_recursive():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub = Path(tmpdir) / "sub"
        sub.mkdir()
        (Path(tmpdir) / "a.gpx").write_text(SAMPLE_GPX_A, encoding="utf-8")
        (sub / "b.gpx").write_text(SAMPLE_GPX_B, encoding="utf-8")

        args = argparse.Namespace(
            directory=tmpdir, recursive=True, files=None
        )
        result = collect_input_files(args)
        assert len(result) == 2


def test_collect_input_files_explicit():
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        args = argparse.Namespace(
            directory=None, recursive=False, files=[str(a)]
        )
        result = collect_input_files(args)
        assert len(result) == 1


def test_collect_input_files_missing_warns(capsys):
    args = argparse.Namespace(
        directory=None, recursive=False, files=["/nonexistent/file.gpx"]
    )
    result = collect_input_files(args)
    assert len(result) == 0
    captured = capsys.readouterr()
    assert "Warning: File not found" in captured.err


def test_collect_input_files_nonexistent_directory():
    args = argparse.Namespace(
        directory="/nonexistent/dir", recursive=False, files=None
    )
    with pytest.raises(SystemExit):
        collect_input_files(args)


def test_collect_input_files_deduplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        args = argparse.Namespace(
            directory=None, recursive=False, files=[str(a), str(a)]
        )
        result = collect_input_files(args)
        assert len(result) == 1


def test_collect_input_files_sorted_deterministic():
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ["z.gpx", "a.gpx", "m.gpx"]:
            (Path(tmpdir) / name).write_text(SAMPLE_GPX_A, encoding="utf-8")

        args = argparse.Namespace(
            directory=tmpdir, recursive=False, files=None
        )
        result = collect_input_files(args)
        assert result == sorted(result)


def test_main_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(a), "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

        assert out.exists()


def test_main_no_input_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "combined.gpx"

        with patch.object(sys, "argv", ["prog", "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1


# --- Self-inclusion guard tests ---


def test_self_inclusion_guard_filters_output(capsys):
    """Output file in directory mode should be excluded from inputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")
        out.write_text(SAMPLE_GPX_B, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", "-d", tmpdir, "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

        captured = capsys.readouterr()
        assert "was found in input list and excluded" in captured.err


def test_self_inclusion_guard_no_false_positive(capsys):
    """Output file not in directory should not trigger self-inclusion warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        with tempfile.TemporaryDirectory() as outdir:
            out = Path(outdir) / "combined.gpx"

            with patch.object(sys, "argv", ["prog", "-d", tmpdir, "-o", str(out)]):
                with pytest.raises(SystemExit) as exc:
                    main()
                assert exc.value.code == 0

            captured = capsys.readouterr()
            assert "was found in input list and excluded" not in captured.err


# --- Input=output guard tests ---


def test_input_equals_output_guard(capsys):
    """Single input file that resolves to same path as output should be caught."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        with patch.object(sys, "argv", ["prog", str(a), "-o", str(a)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

        captured = capsys.readouterr()
        # Self-inclusion guard catches this first
        assert "was found in input list and excluded" in captured.err


# --- Null coordinate warning tests ---


def test_null_coordinate_warning(capsys):
    """Waypoints with null coordinates should produce a stderr warning."""
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a GPX file with a null-coordinate waypoint via mock
        a = Path(tmpdir) / "a.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")
        out = Path(tmpdir) / "combined.gpx"

        import gpxpy.gpx as gpx_mod
        null_wpt = gpx_mod.GPXWaypoint(name="NullPoint")
        null_wpt.latitude = None
        null_wpt.longitude = None

        with patch.object(combiner, 'extract_waypoints', return_value=[null_wpt]):
            combiner.combine_files([str(a)], str(out))

        captured = capsys.readouterr()
        assert "has null coordinates" in captured.err


# --- Overwrite warning tests ---


def test_overwrite_warning(capsys):
    """Writing to an existing file should produce a stderr warning."""
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")
        out.write_text("existing content", encoding="utf-8")

        combiner.combine_files([str(a)], str(out))

        captured = capsys.readouterr()
        assert "Overwriting existing file" in captured.err


# --- Read-back verification tests ---


def test_readback_no_spurious_warning(capsys):
    """Normal operation should not produce a read-back warning."""
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        combiner.combine_files([str(a)], str(out))

        captured = capsys.readouterr()
        assert "Read-back verification mismatch" not in captured.err
        assert "Could not verify" not in captured.err
