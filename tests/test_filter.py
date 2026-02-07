#!/usr/bin/env python3
"""Tests for gpx_waypoint_filter."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import gpxpy.gpx

from gpx_waypoint_filter.gpx_waypoint_filter import (
    WaypointFilter,
    filter_waypoints,
    validate_args,
    print_verbose_info,
)

SAMPLE_GPX = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="37.0" lon="-119.0">
    <name>Mountain Peak</name>
    <sym>Summit</sym>
    <time>2024-06-15T10:00:00Z</time>
  </wpt>
  <wpt lat="38.0" lon="-120.0">
    <name>Lake Camp</name>
    <sym>Campground</sym>
    <time>2024-07-20T14:00:00Z</time>
  </wpt>
  <wpt lat="36.0" lon="-118.0">
    <name>Desert Spring</name>
    <sym>Water</sym>
    <time>2024-08-01T08:00:00Z</time>
  </wpt>
</gpx>
"""

SAMPLE_GPX_DUPES = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="37.0" lon="-119.0">
    <name>A</name>
    <sym>Flag</sym>
  </wpt>
  <wpt lat="37.0" lon="-119.0">
    <name>A</name>
    <sym>Flag</sym>
  </wpt>
</gpx>
"""


def _make_waypoint(lat=37.0, lon=-119.0, name="Test", symbol="Flag", time=None):
    return gpxpy.gpx.GPXWaypoint(
        latitude=lat, longitude=lon, name=name, symbol=symbol, time=time
    )


def _base_criteria(**overrides):
    criteria = {
        "name_contains": None,
        "sym_contains": None,
        "time_contains": None,
        "lat_min": None,
        "lat_max": None,
        "lon_min": None,
        "lon_max": None,
        "case_sensitive": False,
        "logic_mode": "or",
        "bounds_logic": "and",
    }
    criteria.update(overrides)
    return criteria


# --- WaypointFilter unit tests ---


def test_fuzzy_match_case_insensitive():
    f = WaypointFilter(case_sensitive=False)
    assert f.fuzzy_match("Hello World", ["hello"]) is True
    assert f.fuzzy_match("Hello World", ["xyz"]) is False


def test_fuzzy_match_case_sensitive():
    f = WaypointFilter(case_sensitive=True)
    assert f.fuzzy_match("Hello World", ["hello"]) is False
    assert f.fuzzy_match("Hello World", ["Hello"]) is True


def test_fuzzy_match_empty_inputs():
    f = WaypointFilter()
    assert f.fuzzy_match("", ["hello"]) is False
    assert f.fuzzy_match("hello", []) is False
    assert f.fuzzy_match(None, ["hello"]) is False


def test_check_bounds():
    f = WaypointFilter()
    assert f.check_bounds(5.0, 0.0, 10.0) is True
    assert f.check_bounds(15.0, 0.0, 10.0) is False
    assert f.check_bounds(5.0, None, 10.0) is True
    assert f.check_bounds(5.0, 0.0, None) is True
    assert f.check_bounds(5.0, None, None) is True


def test_evaluate_name_filter():
    f = WaypointFilter()
    wpt = _make_waypoint(name="Mountain Peak")
    criteria = _base_criteria(name_contains=["mountain"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is True

    criteria = _base_criteria(name_contains=["lake"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is False


def test_evaluate_sym_filter():
    f = WaypointFilter()
    wpt = _make_waypoint(symbol="Campground")
    criteria = _base_criteria(sym_contains=["camp"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is True


def test_evaluate_time_filter():
    f = WaypointFilter()
    wpt = _make_waypoint(time=datetime(2024, 6, 15, 10, 0, 0))
    criteria = _base_criteria(time_contains=["2024-06"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is True

    criteria = _base_criteria(time_contains=["2025"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is False


def test_evaluate_time_filter_no_time():
    f = WaypointFilter()
    wpt = _make_waypoint(time=None)
    criteria = _base_criteria(time_contains=["2024"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is False


def test_evaluate_bounds_filter():
    f = WaypointFilter()
    wpt = _make_waypoint(lat=37.5, lon=-119.5)
    criteria = _base_criteria(lat_min=37.0, lat_max=38.0, lon_min=-120.0, lon_max=-119.0)
    assert f.evaluate_waypoint(wpt, criteria, "and", "and") is True

    criteria = _base_criteria(lat_min=38.0, lat_max=39.0)
    assert f.evaluate_waypoint(wpt, criteria, "and", "and") is False


def test_evaluate_and_logic():
    f = WaypointFilter()
    wpt = _make_waypoint(lat=37.5, lon=-119.5, name="Camp", symbol="Tent")
    criteria = _base_criteria(name_contains=["camp"], sym_contains=["tent"], logic_mode="and")
    assert f.evaluate_waypoint(wpt, criteria, "and", "and") is True

    criteria = _base_criteria(name_contains=["camp"], sym_contains=["flag"], logic_mode="and")
    assert f.evaluate_waypoint(wpt, criteria, "and", "and") is False


def test_evaluate_or_logic():
    f = WaypointFilter()
    wpt = _make_waypoint(name="Camp", symbol="Tent")
    criteria = _base_criteria(name_contains=["lake"], sym_contains=["tent"], logic_mode="or")
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is True


def test_evaluate_bounds_or_logic():
    f = WaypointFilter()
    wpt = _make_waypoint(lat=37.5, lon=-119.5, name="Camp")

    # bounds-or: bounds result OR text result
    criteria = _base_criteria(
        lat_min=50.0, lat_max=60.0,  # out of bounds
        name_contains=["camp"],
        logic_mode="bounds-or",
    )
    assert f.evaluate_waypoint(wpt, criteria, "bounds-or", "and") is True  # text matches

    # Both fail
    criteria = _base_criteria(
        lat_min=50.0, lat_max=60.0,
        name_contains=["lake"],
        logic_mode="bounds-or",
    )
    assert f.evaluate_waypoint(wpt, criteria, "bounds-or", "and") is False


def test_evaluate_bounds_and_logic():
    f = WaypointFilter()
    wpt = _make_waypoint(lat=37.5, lon=-119.5, name="Camp")

    # bounds-and: bounds result AND text result
    criteria = _base_criteria(
        lat_min=37.0, lat_max=38.0,
        name_contains=["camp"],
        logic_mode="bounds-and",
    )
    assert f.evaluate_waypoint(wpt, criteria, "bounds-and", "and") is True

    # Bounds pass but text fails
    criteria = _base_criteria(
        lat_min=37.0, lat_max=38.0,
        name_contains=["lake"],
        logic_mode="bounds-and",
    )
    assert f.evaluate_waypoint(wpt, criteria, "bounds-and", "and") is False


def test_evaluate_bounds_or_with_or_bounds_logic():
    f = WaypointFilter()
    wpt = _make_waypoint(lat=37.5, lon=-200.0)  # lat in range, lon out

    criteria = _base_criteria(
        lat_min=37.0, lat_max=38.0,
        lon_min=-120.0, lon_max=-119.0,
        logic_mode="bounds-or",
        bounds_logic="or",
    )
    # With bounds_logic="or", only one bound needs to match
    assert f.evaluate_waypoint(wpt, criteria, "bounds-or", "or") is True


def test_evaluate_no_criteria():
    f = WaypointFilter()
    wpt = _make_waypoint()
    criteria = _base_criteria()
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is False


def test_evaluate_no_criteria_bounds_or():
    f = WaypointFilter()
    wpt = _make_waypoint()
    criteria = _base_criteria(logic_mode="bounds-or")
    assert f.evaluate_waypoint(wpt, criteria, "bounds-or", "and") is False


# --- filter_waypoints integration tests ---


def test_filter_waypoints_by_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        criteria = _base_criteria(name_contains=["camp"])
        count = filter_waypoints(str(src), str(out), criteria)
        assert count == 1
        assert out.exists()


def test_filter_waypoints_by_bounds():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        criteria = _base_criteria(lat_min=36.5, lat_max=37.5, lon_min=-119.5, lon_max=-118.5)
        count = filter_waypoints(str(src), str(out), criteria)
        assert count == 1


def test_filter_waypoints_deduplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX_DUPES, encoding="utf-8")

        criteria = _base_criteria(name_contains=["a"])
        count = filter_waypoints(str(src), str(out), criteria)
        assert count == 1  # deduped


def test_filter_waypoints_preserves_attributes():
    """Verify filtered waypoints preserve all attributes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        criteria = _base_criteria(name_contains=["mountain"])
        count = filter_waypoints(str(src), str(out), criteria)
        assert count == 1

        # Parse output and verify waypoint has all data
        with open(str(out), "r") as f:
            gpx = gpxpy.parse(f)
        wpt = gpx.waypoints[0]
        assert wpt.name == "Mountain Peak"
        assert wpt.symbol == "Summit"


# --- validate_args tests ---


def test_validate_args_missing_file():
    args = _mock_args(input_file="/nonexistent/file.gpx", name_contains=["test"])
    with pytest.raises(SystemExit):
        validate_args(args)


def test_validate_args_no_criteria():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_invalid_lat_range():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lat_min=40.0, lat_max=30.0)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_invalid_lon_range():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lon_min=-110.0, lon_max=-120.0)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_valid():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, name_contains=["test"])
        validate_args(args)  # should not raise


# --- print_verbose_info tests ---


def test_print_verbose_info(capsys):
    args = _mock_args(
        input_file="test.gpx",
        name_contains=["peak"],
        sym_contains=["summit"],
        time_contains=["2024"],
        lat_min=36.0,
        lat_max=38.0,
        lon_min=-120.0,
        lon_max=-118.0,
        case_sensitive=True,
        logic="bounds-and",
        bounds_logic="or",
    )
    print_verbose_info(args)
    captured = capsys.readouterr()
    assert "peak" in captured.out
    assert "summit" in captured.out
    assert "2024" in captured.out
    assert "36.0" in captured.out
    assert "Bounds logic: or" in captured.out


def test_print_verbose_info_minimal(capsys):
    args = _mock_args(
        input_file="test.gpx",
        name_contains=["peak"],
        logic="or",
    )
    print_verbose_info(args)
    captured = capsys.readouterr()
    assert "peak" in captured.out
    assert "Bounds logic" not in captured.out  # not printed for non-bounds logic


# --- Coordinate range validation tests ---


def test_validate_args_lat_min_out_of_range():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lat_min=-91.0)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_lat_max_out_of_range():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lat_max=91.0)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_lon_min_out_of_range():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lon_min=-181.0)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_lon_max_out_of_range():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lon_max=181.0)
        with pytest.raises(SystemExit):
            validate_args(args)


def test_validate_args_boundary_coords_accepted():
    """Boundary values (-90, 90, -180, 180) should be accepted."""
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, lat_min=-90.0, lat_max=90.0,
                          lon_min=-180.0, lon_max=180.0)
        validate_args(args)  # should not raise


# --- Input=output guard tests ---


def test_validate_args_input_equals_output():
    with tempfile.NamedTemporaryFile(suffix=".gpx", mode="w", delete=False) as f:
        f.write(SAMPLE_GPX)
        f.flush()
        args = _mock_args(input_file=f.name, output_file=f.name, name_contains=["test"])
        with pytest.raises(SystemExit):
            validate_args(args)


# --- Zero-result warning tests ---


def test_zero_result_warning(capsys):
    """Filter that matches nothing should produce a zero-result warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        criteria = _base_criteria(name_contains=["nonexistent_xyz"])
        count = filter_waypoints(str(src), str(out), criteria)

        assert count == 0
        captured = capsys.readouterr()
        assert "No waypoints matched the filter criteria" in captured.err


# --- Overwrite warning tests ---


def test_overwrite_warning(capsys):
    """Writing to an existing file should produce a stderr warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")
        out.write_text("existing content", encoding="utf-8")

        criteria = _base_criteria(name_contains=["mountain"])
        filter_waypoints(str(src), str(out), criteria)

        captured = capsys.readouterr()
        assert "Overwriting existing file" in captured.err


# --- Read-back verification tests ---


def test_readback_no_spurious_warning(capsys):
    """Normal operation should not produce a read-back warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "input.gpx"
        out = Path(tmpdir) / "output.gpx"
        src.write_text(SAMPLE_GPX, encoding="utf-8")

        criteria = _base_criteria(name_contains=["mountain"])
        filter_waypoints(str(src), str(out), criteria)

        captured = capsys.readouterr()
        assert "Read-back verification mismatch" not in captured.err
        assert "Could not verify" not in captured.err


# --- Helper ---


def _mock_args(**kwargs):
    import argparse
    defaults = {
        "input_file": "input.gpx",
        "output_file": "output.gpx",
        "name_contains": None,
        "sym_contains": None,
        "time_contains": None,
        "lat_min": None,
        "lat_max": None,
        "lon_min": None,
        "lon_max": None,
        "case_sensitive": False,
        "logic": "or",
        "bounds_logic": "and",
        "verbose": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)
