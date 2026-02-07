#!/usr/bin/env python3
"""Tests for gpx_waypoint_combiner."""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from gpx_waypoint_combiner.gpx_waypoint_combiner import GPXCombiner, collect_input_files

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


def test_extract_waypoints():
    combiner = GPXCombiner()
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX_A)
        f.flush()
        wpts = combiner.extract_waypoints(f.name)
    assert len(wpts) == 1


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


def test_extract_waypoints_missing_file():
    combiner = GPXCombiner()
    wpts = combiner.extract_waypoints("/nonexistent/file.gpx")
    assert wpts == []
