#!/usr/bin/env python3
"""Tests for gpx_waypoint_filter."""

import gpxpy.gpx

from gpx_waypoint_filter.gpx_waypoint_filter import WaypointFilter


def _make_waypoint(lat=37.0, lon=-119.0, name="Test", symbol="Flag", time=None):
    wpt = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon, name=name, symbol=symbol, time=time)
    return wpt


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


def test_fuzzy_match_case_insensitive():
    f = WaypointFilter(case_sensitive=False)
    assert f.fuzzy_match("Hello World", ["hello"]) is True
    assert f.fuzzy_match("Hello World", ["xyz"]) is False


def test_fuzzy_match_case_sensitive():
    f = WaypointFilter(case_sensitive=True)
    assert f.fuzzy_match("Hello World", ["hello"]) is False
    assert f.fuzzy_match("Hello World", ["Hello"]) is True


def test_check_bounds():
    f = WaypointFilter()
    assert f.check_bounds(5.0, 0.0, 10.0) is True
    assert f.check_bounds(15.0, 0.0, 10.0) is False
    assert f.check_bounds(5.0, None, 10.0) is True
    assert f.check_bounds(5.0, 0.0, None) is True


def test_evaluate_name_filter():
    f = WaypointFilter()
    wpt = _make_waypoint(name="Mountain Peak")
    criteria = _base_criteria(name_contains=["mountain"])
    assert f.evaluate_waypoint(wpt, criteria, "or", "and") is True

    criteria = _base_criteria(name_contains=["lake"])
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
