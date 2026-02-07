#!/usr/bin/env python3
"""Tests for gpx_waypoint_splitter."""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from gpx_waypoint_splitter.gpx_waypoint_splitter import parse_gpx, create_output_files

SAMPLE_GPX = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="37.0" lon="-119.0"><name>A</name></wpt>
  <wpt lat="37.1" lon="-119.1"><name>B</name></wpt>
  <wpt lat="37.2" lon="-119.2"><name>C</name></wpt>
</gpx>
"""


def _write_sample(path):
    Path(path).write_text(SAMPLE_GPX, encoding="utf-8")


def test_parse_gpx_finds_waypoints():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        waypoints, header, ns, count = parse_gpx(f.name)
    assert count == 3
    assert len(waypoints) == 3


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
