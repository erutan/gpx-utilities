#!/usr/bin/env python3
"""Tests for gpx_from_radiacode."""

import copy
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import gpxpy

from gpx_from_radiacode.gpx_from_radiacode import RadiacodeConverter, main

SAMPLE_RCTRK = {
    "devices": ["RC-103-006752"],
    "sv": False,
    "periods": [
        {"distance": 100.0, "start": 1769636222, "end": 1769636322}
    ],
    "markers": [
        {"lat": 33.875677, "lon": -110.983924, "date": 1769636251,
         "countRate": 6.93, "doseRate": 8.22, "acc": 4},
        {"lat": 33.878611, "lon": -110.989916, "date": 1769640474,
         "countRate": 9.04, "doseRate": 11.12, "acc": 4},
        {"lat": 33.878007, "lon": -110.991258, "date": 1769642758,
         "countRate": 10.54, "doseRate": 11.38, "acc": 4},
        {"lat": 33.877654, "lon": -110.992483, "date": 1769643081,
         "countRate": 0, "doseRate": 0, "acc": 4},
    ],
    "start": 1769636222,
    "title": "Track 28 Jan 2026 14:37:02"
}

SAMPLE_RCTRK_UNSORTED = {
    "devices": ["RC-103-006752"],
    "sv": False,
    "periods": [],
    "markers": [
        {"lat": 33.878007, "lon": -110.991258, "date": 1769642758,
         "countRate": 10.54, "doseRate": 11.38, "acc": 4},
        {"lat": 33.875677, "lon": -110.983924, "date": 1769636251,
         "countRate": 6.93, "doseRate": 8.22, "acc": 4},
        {"lat": 33.878611, "lon": -110.989916, "date": 1769640474,
         "countRate": 9.04, "doseRate": 11.12, "acc": 4},
    ],
    "start": 1769636222,
    "title": "Test Track"
}

SAMPLE_RCTRK_SV_MODE = {
    "devices": ["RC-103-006752"],
    "sv": True,
    "periods": [],
    "markers": [
        {"lat": 33.875677, "lon": -110.983924, "date": 1769636251,
         "countRate": 5.0, "doseRate": 12.5, "acc": 3},
    ],
    "start": 1769636222,
    "title": "SV Mode Track"
}


def _write_rctrk(path, data):
    """Write a .rctrk JSON file."""
    path.write_text(json.dumps(data), encoding='utf-8')


@pytest.fixture
def rctrk_env(tmp_path):
    """Provide a temp directory with paths and a write helper."""
    src = tmp_path / "track.rctrk"
    out = tmp_path / "output.gpx"
    def write(data=None):
        _write_rctrk(src, data if data is not None else SAMPLE_RCTRK)
    return src, out, write


# --- Basic conversion tests ---


def test_convert_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        success = converter.convert(str(src), str(out))

        assert success is True
        assert converter.total_points == 4
        assert converter.max_count_rate == 10.54
        assert converter.max_dose_rate == 11.38

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks) == 1
        assert len(result_gpx.tracks[0].segments) == 1
        assert len(result_gpx.tracks[0].segments[0].points) == 4
        assert len(result_gpx.waypoints) == 0


def test_convert_with_waypoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter(waypoints=True)
        success = converter.convert(str(src), str(out))

        assert success is True

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks[0].segments[0].points) == 4
        assert len(result_gpx.waypoints) == 4

        # Check waypoint names contain rate data
        assert "cps/" in result_gpx.waypoints[0].name
        assert "\u00b5Sv/h" in result_gpx.waypoints[0].name


def test_convert_no_waypoints_by_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.waypoints) == 0


# --- Track name tests ---


def test_track_name_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        name = result_gpx.tracks[0].name
        assert name.startswith("radiacode 2026-01-28")
        assert "10.54cps" in name
        assert "11.38\u00b5Sv/h" in name


# --- Sorting tests ---


def test_markers_sorted_chronologically():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK_UNSORTED)

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        points = result_gpx.tracks[0].segments[0].points
        times = [p.time for p in points]
        assert times == sorted(times)


# --- Default output path tests ---


def test_default_output_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "mytrack.rctrk"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        success = converter.convert(str(src))

        assert success is True
        expected = Path(tmpdir) / "mytrack.gpx"
        assert expected.exists()


# --- Verbose output tests ---


def test_verbose_output(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter(verbose=True)
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "Device: RC-103-006752" in captured.out
        assert "Track points: 4" in captured.out
        assert "Max count rate:" in captured.out
        assert "Max dose rate:" in captured.out


def test_verbose_sv_mode(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK_SV_MODE)

        converter = RadiacodeConverter(verbose=True)
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "Sievert mode: True" in captured.out


# --- Error handling tests ---


def test_missing_markers():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        _write_rctrk(src, {"devices": [], "sv": False, "periods": [], "start": 0, "title": "empty"})
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter()
        success = converter.convert(str(src), str(out))

        assert success is False


def test_empty_markers():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = copy.deepcopy(SAMPLE_RCTRK)
        data['markers'] = []
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter()
        success = converter.convert(str(src), str(out))

        assert success is False


def test_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        src.write_text("not json", encoding='utf-8')

        converter = RadiacodeConverter()
        success = converter.convert(str(src))
        assert success is False


def test_missing_file():
    converter = RadiacodeConverter()
    success = converter.convert("/nonexistent/track.rctrk")
    assert success is False


def test_marker_missing_date(capsys):
    """Markers without a date field should be skipped gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"lat": 33.87, "lon": -110.98, "countRate": 5.0, "doseRate": 8.0, "acc": 3},
                {"lat": 33.88, "lon": -110.99, "date": 1769636300,
                 "countRate": 6.0, "doseRate": 9.0, "acc": 4},
            ],
            "start": 1769636222,
            "title": "No date"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter(verbose=True)
        success = converter.convert(str(src), str(out))

        assert success is True
        captured = capsys.readouterr()
        assert "Skipping marker 0 with missing coordinates or timestamp" in captured.out

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks[0].segments[0].points) == 1


def test_marker_invalid_date_type(capsys):
    """Markers with a non-numeric date should be skipped gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"lat": 33.87, "lon": -110.98, "date": "not-a-timestamp",
                 "countRate": 5.0, "doseRate": 8.0, "acc": 3},
                {"lat": 33.88, "lon": -110.99, "date": 1769636300,
                 "countRate": 6.0, "doseRate": 9.0, "acc": 4},
            ],
            "start": 1769636222,
            "title": "Bad date"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter(verbose=True)
        success = converter.convert(str(src), str(out))

        assert success is True
        captured = capsys.readouterr()
        assert "Skipping marker 0 with invalid timestamp" in captured.out

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks[0].segments[0].points) == 1


def test_all_markers_missing_date(capsys):
    """All markers missing dates should produce zero-result warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"lat": 33.87, "lon": -110.98, "countRate": 5.0, "doseRate": 8.0, "acc": 3},
            ],
            "start": 1769636222,
            "title": "All bad"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter()
        success = converter.convert(str(src), str(out))

        assert success is True
        captured = capsys.readouterr()
        assert "No valid track points" in captured.err


def test_marker_missing_coordinates(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"date": 1769636251, "countRate": 5.0, "doseRate": 8.0, "acc": 3},
                {"lat": 33.87, "lon": -110.98, "date": 1769636300,
                 "countRate": 6.0, "doseRate": 9.0, "acc": 4},
            ],
            "start": 1769636222,
            "title": "Partial"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter(verbose=True)
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "Skipping marker 0 with missing coordinates or timestamp" in captured.out

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks[0].segments[0].points) == 1


def test_marker_out_of_range_coordinates(capsys):
    """Markers with out-of-range lat/lon should be skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"lat": 91.0, "lon": -110.98, "date": 1769636251,
                 "countRate": 5.0, "doseRate": 8.0, "acc": 3},
                {"lat": 33.87, "lon": -181.0, "date": 1769636260,
                 "countRate": 5.0, "doseRate": 8.0, "acc": 3},
                {"lat": 33.87, "lon": -110.98, "date": 1769636300,
                 "countRate": 6.0, "doseRate": 9.0, "acc": 4},
            ],
            "start": 1769636222,
            "title": "Bad coords"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter(verbose=True)
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "out-of-range coordinates" in captured.out

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks[0].segments[0].points) == 1


def test_marker_boundary_coordinates():
    """Coordinates at exact boundaries (-90/90, -180/180) should be accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"lat": 90.0, "lon": 180.0, "date": 1769636251,
                 "countRate": 5.0, "doseRate": 8.0, "acc": 3},
                {"lat": -90.0, "lon": -180.0, "date": 1769636300,
                 "countRate": 6.0, "doseRate": 9.0, "acc": 4},
            ],
            "start": 1769636222,
            "title": "Boundary coords"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks[0].segments[0].points) == 2


# --- Overwrite warning tests ---


def test_overwrite_warning(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)
        out.write_text("existing content", encoding='utf-8')

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "Overwriting existing file" in captured.err


# --- Zero-result warning tests ---


def test_zero_result_warning(capsys):
    """All markers missing coordinates should produce a zero-result warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        data = {
            "devices": ["RC-103"],
            "sv": False,
            "periods": [],
            "markers": [
                {"date": 1769636251, "countRate": 5.0, "doseRate": 8.0, "acc": 3},
            ],
            "start": 1769636222,
            "title": "No coords"
        }
        _write_rctrk(src, data)
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "No valid track points" in captured.err


# --- Read-back verification tests ---


def test_readback_no_spurious_warning(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "Read-back verification mismatch" not in captured.err
        assert "Could not verify" not in captured.err


def test_readback_with_waypoints(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter(waypoints=True)
        converter.convert(str(src), str(out))

        captured = capsys.readouterr()
        assert "Read-back verification mismatch" not in captured.err
        assert "Could not verify" not in captured.err


# --- CLI tests ---


def test_main_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0


def test_main_with_waypoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out), "-w"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0


def test_main_verbose():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out), "-v"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0


def test_main_missing_file():
    with patch.object(sys, "argv", ["prog", "/nonexistent/track.rctrk"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_main_non_rctrk_extension(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.json"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(out)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

        captured = capsys.readouterr()
        assert "Warning: Input file does not have .rctrk extension" in captured.err


def test_main_input_equals_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        _write_rctrk(src, SAMPLE_RCTRK)

        with patch.object(sys, "argv", ["prog", str(src), "-o", str(src)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1


# --- GPX content validation tests ---


def test_track_points_have_timestamps():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        for point in result_gpx.tracks[0].segments[0].points:
            assert point.time is not None


def test_waypoint_names_contain_rates():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter(waypoints=True)
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        # First marker: 6.93cps/8.22µSv/h
        assert result_gpx.waypoints[0].name == "6.93cps/8.22\u00b5Sv/h"
        # Fourth marker: 0cps/0µSv/h
        assert result_gpx.waypoints[3].name == "0cps/0\u00b5Sv/h"


def test_gpx_creator_set():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "track.rctrk"
        out = Path(tmpdir) / "output.gpx"
        _write_rctrk(src, SAMPLE_RCTRK)

        converter = RadiacodeConverter()
        converter.convert(str(src), str(out))

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert result_gpx.creator == 'gpx_from_radiacode'


# --- Integration test with real file ---


def test_real_rctrk_file():
    """Test with the actual sample .rctrk file if available."""
    real_file = Path(__file__).parent.parent / "gpx_from_radiacode" / "Track 28 Jan 2026 14-37-02.rctrk"
    if not real_file.exists():
        pytest.skip("Sample .rctrk file not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter()
        success = converter.convert(str(real_file), str(out))

        assert success is True
        assert converter.total_points > 0

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.tracks) == 1
        assert len(result_gpx.tracks[0].segments[0].points) > 0


def test_real_rctrk_file_with_waypoints():
    """Test with the actual sample .rctrk file with waypoints enabled."""
    real_file = Path(__file__).parent.parent / "gpx_from_radiacode" / "Track 28 Jan 2026 14-37-02.rctrk"
    if not real_file.exists():
        pytest.skip("Sample .rctrk file not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "output.gpx"

        converter = RadiacodeConverter(waypoints=True)
        success = converter.convert(str(real_file), str(out))

        assert success is True

        with open(str(out), 'r') as f:
            result_gpx = gpxpy.parse(f)
        assert len(result_gpx.waypoints) == len(result_gpx.tracks[0].segments[0].points)
