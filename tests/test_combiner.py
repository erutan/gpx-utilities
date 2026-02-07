#!/usr/bin/env python3
"""Tests for gpx_waypoint_combiner."""

import argparse
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pytest

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

        tree = ET.parse(str(out))
        root = tree.getroot()
        wpts = root.findall(".//{http://www.topografix.com/GPX/1/1}wpt")
        assert len(wpts) == 3


def test_combine_files_with_metadata():
    combiner = GPXCombiner()
    with tempfile.TemporaryDirectory() as tmpdir:
        a = Path(tmpdir) / "a.gpx"
        out = Path(tmpdir) / "combined.gpx"
        a.write_text(SAMPLE_GPX_A, encoding="utf-8")

        metadata = {"name": "Test Trip", "desc": "A test collection"}
        success = combiner.combine_files([str(a)], str(out), metadata=metadata)
        assert success is True

        tree = ET.parse(str(out))
        root = tree.getroot()
        name = root.find(".//{http://www.topografix.com/GPX/1/1}name")
        assert name is not None
        assert name.text == "Test Trip"


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

    root = combiner.create_combined_gpx(wpts, metadata=None)
    assert root.get("version") == "1.1"


def test_indent_empty_element():
    combiner = GPXCombiner()
    elem = ET.Element("test")
    combiner.indent(elem, level=1)
    assert elem.tail == "\n  "


def test_indent_with_children():
    combiner = GPXCombiner()
    parent = ET.Element("parent")
    ET.SubElement(parent, "child1")
    ET.SubElement(parent, "child2")
    combiner.indent(parent)
    assert parent.text is not None
    assert "\n" in parent.text


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
