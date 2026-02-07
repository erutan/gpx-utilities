#!/usr/bin/env python3
"""
GPX Waypoint Deduplicator
Remove duplicate waypoints from GPX files based on various criteria
"""

import argparse
import sys
import hashlib
from pathlib import Path
import gpxpy
import gpxpy.gpx


class GPXDeduplicator:
    def __init__(self, strategy='time-coords', precision=6, verbose=False, keep_last=False):
        self.strategy = strategy
        self.precision = precision
        self.verbose = verbose
        self.keep_last = keep_last
        self.seen_items = {}
        self.duplicates_removed = 0
        self.total_waypoints = 0

    def _get_unique_key(self, wpt):
        """Get unique key based on selected strategy."""
        if self.strategy == 'time':
            return wpt.time

        elif self.strategy == 'coords':
            if wpt.latitude is not None and wpt.longitude is not None:
                return (
                    round(wpt.latitude, self.precision),
                    round(wpt.longitude, self.precision)
                )

        elif self.strategy == 'name':
            return wpt.name

        elif self.strategy == 'time-coords':
            if wpt.time and wpt.latitude is not None and wpt.longitude is not None:
                return (
                    wpt.time,
                    round(wpt.latitude, self.precision),
                    round(wpt.longitude, self.precision)
                )

        elif self.strategy == 'hash':
            parts = (
                str(wpt.latitude), str(wpt.longitude), str(wpt.elevation),
                str(wpt.time), str(wpt.name), str(wpt.description),
                str(wpt.symbol), str(wpt.comment), str(wpt.source),
            )
            return hashlib.sha256('|'.join(parts).encode()).hexdigest()

        return None

    def process_gpx(self, input_file, output_file=None):
        """Process GPX file and remove duplicates."""
        self.seen_items = {}
        self.duplicates_removed = 0
        self.total_waypoints = 0
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)

            self.total_waypoints = len(gpx.waypoints)

            if self.verbose:
                print(f"Found {self.total_waypoints} waypoints in {input_file}")
                print(f"Using strategy: {self.strategy}")

            # Build list of unique waypoints
            unique_waypoints = []

            for wpt in gpx.waypoints:
                key = self._get_unique_key(wpt)

                if key is None:
                    if self.verbose:
                        print(f"Warning: Could not extract key for waypoint")
                    unique_waypoints.append(wpt)
                    continue

                if key in self.seen_items:
                    if self.keep_last:
                        # Replace previous occurrence with current
                        prev_idx = self.seen_items[key]
                        unique_waypoints[prev_idx] = wpt
                    self.duplicates_removed += 1
                    if self.verbose:
                        print(f"Duplicate found: {key}")
                else:
                    self.seen_items[key] = len(unique_waypoints)
                    unique_waypoints.append(wpt)

            gpx.waypoints = unique_waypoints

            # Determine output path
            if output_file is None:
                p = Path(input_file)
                output_file = p.parent / f"{p.stem}_dedup{p.suffix}"

            # Write result
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(gpx.to_xml())

            # Report results
            print(f"\nProcessing complete:")
            print(f"  Total waypoints: {self.total_waypoints}")
            print(f"  Duplicates removed: {self.duplicates_removed}")
            print(f"  Unique waypoints: {self.total_waypoints - self.duplicates_removed}")
            print(f"  Output saved to: {output_file}")

            return True

        except (gpxpy.gpx.GPXXMLSyntaxException, OSError, ValueError) as e:
            print(f"Error processing file: {e}", file=sys.stderr)
            return False

def main():
    """Parse arguments and deduplicate waypoints in a GPX file."""
    parser = argparse.ArgumentParser(
        description='Remove duplicate waypoints from GPX files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Strategies:
  time-coords  - Remove waypoints with both duplicate time AND coordinates (default)
  time         - Remove waypoints with duplicate timestamps
  coords       - Remove waypoints with duplicate coordinates
  name         - Remove waypoints with duplicate names
  hash         - Remove waypoints with identical content

Examples:
  %(prog)s input.gpx
  %(prog)s input.gpx -o output.gpx
  %(prog)s input.gpx -s coords -p 4
  %(prog)s input.gpx -s hash -v
  %(prog)s input.gpx --keep-last
        '''
    )

    parser.add_argument('input',
                       help='Input GPX file')

    parser.add_argument('-o', '--output',
                       help='Output GPX file (default: input_dedup.gpx)')

    parser.add_argument('-s', '--strategy',
                       choices=['time', 'coords', 'name', 'time-coords', 'hash'],
                       default='time-coords',
                       help='Deduplication strategy (default: time-coords)')

    parser.add_argument('-p', '--precision',
                       type=int,
                       default=6,
                       help='Decimal precision for coordinate comparison (default: 6)')

    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Enable verbose output')

    parser.add_argument('--keep-last',
                       action='store_true',
                       help='Keep last occurrence of duplicates instead of first')

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    if not args.input.lower().endswith('.gpx'):
        print("Warning: Input file does not have .gpx extension", file=sys.stderr)

    # Process file
    dedup = GPXDeduplicator(
        strategy=args.strategy,
        precision=args.precision,
        verbose=args.verbose,
        keep_last=args.keep_last
    )

    success = dedup.process_gpx(args.input, args.output)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
