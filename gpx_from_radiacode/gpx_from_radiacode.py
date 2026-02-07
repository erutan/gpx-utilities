#!/usr/bin/env python3
"""
GPX from Radiacode
Convert Radiacode .rctrk track files to GPX format
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import gpxpy
import gpxpy.gpx


class RadiacodeConverter:
    def __init__(self, waypoints=False, verbose=False):
        self.waypoints = waypoints
        self.verbose = verbose
        self.total_points = 0
        self.max_count_rate = 0.0
        self.max_dose_rate = 0.0

    def _parse_rctrk(self, input_file):
        """Parse a .rctrk JSON file and return the data."""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'markers' not in data or not data['markers']:
            raise ValueError("No markers found in track file")

        return data

    def _sort_markers(self, markers):
        """Sort markers chronologically by date."""
        def _sort_key(m):
            date = m.get('date', 0)
            return date if isinstance(date, (int, float)) else 0
        return sorted(markers, key=_sort_key)

    def _format_rate(self, count_rate, dose_rate):
        """Format count and dose rates for display."""
        return f"{count_rate}cps/{dose_rate}\u00b5Sv/h"

    def _build_track_name(self, start_timestamp):
        """Build track name from start date and max readings."""
        dt = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
        date_str = dt.strftime('%Y-%m-%d')
        return f"radiacode {date_str} {self._format_rate(self.max_count_rate, self.max_dose_rate)}"

    def _find_max_readings(self, markers):
        """Scan markers for maximum count and dose rates."""
        for m in markers:
            if m.get('countRate', 0) > self.max_count_rate:
                self.max_count_rate = m['countRate']
            if m.get('doseRate', 0) > self.max_dose_rate:
                self.max_dose_rate = m['doseRate']

    def _build_gpx(self, markers, track_name):
        """Build GPX object with track segment and optional waypoints from markers."""
        gpx = gpxpy.gpx.GPX()
        gpx.creator = 'gpx_from_radiacode'

        gpx_track = gpxpy.gpx.GPXTrack(name=track_name)
        gpx.tracks.append(gpx_track)

        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for m in markers:
            lat = m.get('lat')
            lon = m.get('lon')
            date = m.get('date')
            if lat is None or lon is None or date is None:
                if self.verbose:
                    print(f"Warning: Skipping marker with missing coordinates or timestamp")
                continue

            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                if self.verbose:
                    print(f"Warning: Skipping marker with out-of-range coordinates ({lat}, {lon})")
                continue

            try:
                dt = datetime.fromtimestamp(date, tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                if self.verbose:
                    print(f"Warning: Skipping marker with invalid timestamp: {date}")
                continue

            point = gpxpy.gpx.GPXTrackPoint(
                latitude=lat,
                longitude=lon,
                time=dt
            )
            gpx_segment.points.append(point)

            if self.waypoints:
                count_rate = m.get('countRate', 0)
                dose_rate = m.get('doseRate', 0)
                wpt = gpxpy.gpx.GPXWaypoint(
                    latitude=lat,
                    longitude=lon,
                    time=dt,
                    name=self._format_rate(count_rate, dose_rate)
                )
                gpx.waypoints.append(wpt)

        return gpx, gpx_segment

    def _verify_output(self, output_file, expected_points, expected_waypoints):
        """Read-back verification of the written GPX file."""
        try:
            with open(output_file, 'r', encoding='utf-8') as vf:
                verify_gpx = gpxpy.parse(vf)
            actual_points = sum(
                len(seg.points)
                for trk in verify_gpx.tracks
                for seg in trk.segments
            )
            if actual_points != expected_points:
                print(f"Warning: Read-back verification mismatch: wrote {expected_points} "
                      f"track points but read back {actual_points}", file=sys.stderr)
            if self.waypoints:
                if len(verify_gpx.waypoints) != expected_waypoints:
                    print(f"Warning: Read-back verification mismatch: wrote {expected_waypoints} "
                          f"waypoints but read back {len(verify_gpx.waypoints)}", file=sys.stderr)
        except Exception:
            print("Warning: Could not verify output file", file=sys.stderr)

    def convert(self, input_file, output_file=None):
        """Convert a .rctrk file to GPX format."""
        self.total_points = 0
        self.max_count_rate = 0.0
        self.max_dose_rate = 0.0

        try:
            data = self._parse_rctrk(input_file)

            markers = self._sort_markers(data['markers'])
            self.total_points = len(markers)
            self._find_max_readings(markers)

            # Determine start timestamp
            start_ts = data.get('start')
            if start_ts is None:
                start_ts = markers[0].get('date', 0)

            if self.verbose:
                print(f"Device: {', '.join(data.get('devices', ['unknown']))}")
                print(f"Sievert mode: {data.get('sv', False)}")
                print(f"Track points: {self.total_points}")
                print(f"Max count rate: {self.max_count_rate} cps")
                print(f"Max dose rate: {self.max_dose_rate} \u00b5Sv/h")

            track_name = self._build_track_name(start_ts)
            gpx, gpx_segment = self._build_gpx(markers, track_name)

            # Zero-result warning
            if len(gpx_segment.points) == 0:
                print("Warning: No valid track points were generated", file=sys.stderr)

            # Determine output path
            if output_file is None:
                p = Path(input_file)
                output_file = p.parent / f"{p.stem}.gpx"

            # Overwrite warning
            if Path(output_file).exists():
                print(f"Warning: Overwriting existing file '{output_file}'", file=sys.stderr)

            # Write result
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(gpx.to_xml())

            # Report results
            print(f"\nConversion complete:")
            print(f"  Track name: {track_name}")
            print(f"  Track points: {len(gpx_segment.points)}")
            if self.waypoints:
                print(f"  Waypoints: {len(gpx.waypoints)}")
            print(f"  Output saved to: {output_file}")

            self._verify_output(output_file, len(gpx_segment.points), len(gpx.waypoints))

            return True

        except (json.JSONDecodeError, OSError, ValueError) as e:
            print(f"Error processing track file: {e}", file=sys.stderr)
            return False


def main():
    """Parse arguments and convert a Radiacode track file to GPX."""
    parser = argparse.ArgumentParser(
        description='Convert Radiacode .rctrk track files to GPX format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s track.rctrk
  %(prog)s track.rctrk -o output.gpx
  %(prog)s track.rctrk -w
  %(prog)s track.rctrk -w -o output.gpx -v
        '''
    )

    parser.add_argument('input',
                        help='Input Radiacode .rctrk file')

    parser.add_argument('-o', '--output',
                        help='Output GPX file (default: input_stem.gpx)')

    parser.add_argument('-w', '--waypoints',
                        action='store_true',
                        help='Include waypoints with count/dose rate as names')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    if not args.input.lower().endswith('.rctrk'):
        print("Warning: Input file does not have .rctrk extension", file=sys.stderr)

    # Input=output guard
    if args.output and Path(args.input).resolve() == Path(args.output).resolve():
        print("Error: Input and output resolve to the same file", file=sys.stderr)
        sys.exit(1)

    # Convert file
    converter = RadiacodeConverter(
        waypoints=args.waypoints,
        verbose=args.verbose
    )

    success = converter.convert(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
