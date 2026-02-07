#!/usr/bin/env python3
"""Tests for gpx_waypoint_splitter."""

import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

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
        waypoints, header, ns, count = parse_gpx(f.name)
    assert count == 3
    assert len(waypoints) == 3


def test_parse_gpx_no_namespace():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_NO_NS)
        f.flush()
        waypoints, header, ns, count = parse_gpx(f.name)
    assert count == 2
    assert ns == {}


def test_parse_gpx_empty_file():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_EMPTY)
        f.flush()
        waypoints, header, ns, count = parse_gpx(f.name)
    assert count == 0
    assert len(waypoints) == 0


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

        waypoints, header, ns, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(waypoints, header, ns, prefix, waypoints_per_file=2)

        assert total == 3
        assert (Path(tmpdir) / "out_001.gpx").exists()
        assert (Path(tmpdir) / "out_002.gpx").exists()


def test_split_single_file_when_all_fit():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        waypoints, header, ns, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(waypoints, header, ns, prefix, waypoints_per_file=1000)

        assert total == 3
        assert (Path(tmpdir) / "out_001.gpx").exists()
        assert not (Path(tmpdir) / "out_002.gpx").exists()


def test_split_with_metadata_preserves_non_waypoint_elements():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX_WITH_METADATA, encoding="utf-8")

        waypoints, header, ns, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(waypoints, header, ns, prefix, waypoints_per_file=1000)

        assert total == 2
        tree = ET.parse(str(Path(tmpdir) / "out_001.gpx"))
        root = tree.getroot()
        # Should contain metadata element
        metadata = root.findall(".//{http://www.topografix.com/GPX/1/1}metadata")
        assert len(metadata) == 1


def test_split_empty_waypoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX_EMPTY, encoding="utf-8")

        waypoints, header, ns, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        total = create_output_files(waypoints, header, ns, prefix, waypoints_per_file=1000)

        assert total == 0
        assert not (Path(tmpdir) / "out_001.gpx").exists()


def test_split_output_files_contain_valid_xml():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        waypoints, header, ns, count = parse_gpx(str(src))
        prefix = str(Path(tmpdir) / "out")
        create_output_files(waypoints, header, ns, prefix, waypoints_per_file=1)

        for i in range(1, 4):
            tree = ET.parse(str(Path(tmpdir) / f"out_{i:03d}.gpx"))
            root = tree.getroot()
            wpts = root.findall(".//{http://www.topografix.com/GPX/1/1}wpt")
            assert len(wpts) == 1


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


# Import pytest at the top level for the raises usage
import pytest
