#!/usr/bin/env python3
"""Tests for gpx_waypoint_deduper."""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from gpx_waypoint_deduper.gpx_waypoint_deduper import GPXDeduplicator

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

        tree = ET.parse(str(out))
        root = tree.getroot()
        wpts = root.findall(".//wpt")
        assert len(wpts) == 2


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
