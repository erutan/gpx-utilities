#!/usr/bin/env python3
"""
GPX Splitter - Splits a large GPX file into multiple smaller files with customizable number of waypoints.
Usage: python gpx_splitter.py input.gpx [output_prefix] [--waypoints-per-file=1000]
"""

import sys
import argparse
from pathlib import Path
import gpxpy
import gpxpy.gpx

def parse_gpx(gpx_file):
    """Parse a GPX file and extract all waypoints."""
    try:
        with open(gpx_file, 'r', encoding='utf-8') as f:
            gpx = gpxpy.parse(f)

        waypoint_count = len(gpx.waypoints)
        print(f"Found {waypoint_count} waypoints in {gpx_file}")

        # Warn about waypoints with null coordinates
        for wpt in gpx.waypoints:
            if wpt.latitude is None or wpt.longitude is None:
                print(f"Warning: Waypoint '{wpt.name}' has null coordinates", file=sys.stderr)

        return gpx, waypoint_count

    except (gpxpy.gpx.GPXXMLSyntaxException, OSError) as e:
        print(f"Error parsing GPX file: {e}", file=sys.stderr)
        sys.exit(1)

def create_output_files(gpx, output_prefix, waypoints_per_file=1000):
    """Split waypoints into multiple files with specified number of waypoints each."""
    waypoints = gpx.waypoints
    total_waypoints = len(waypoints)

    if total_waypoints == 0:
        print("No waypoints to split")
        return 0

    # Ceiling division
    num_files = -(-total_waypoints // waypoints_per_file)

    print(f"Splitting {total_waypoints} waypoints into {num_files} files with up to {waypoints_per_file} waypoints each")
    total_written = 0

    # Create each output file
    for file_num in range(num_files):
        start_idx = file_num * waypoints_per_file
        end_idx = min((file_num + 1) * waypoints_per_file, total_waypoints)

        # Create a new GPX with metadata from original
        new_gpx = gpxpy.gpx.GPX()
        new_gpx.creator = gpx.creator
        new_gpx.name = gpx.name
        new_gpx.description = gpx.description
        new_gpx.author_name = gpx.author_name
        new_gpx.author_email = gpx.author_email
        new_gpx.time = gpx.time
        new_gpx.tracks = gpx.tracks
        new_gpx.routes = gpx.routes

        # Add waypoints for this file
        new_gpx.waypoints = waypoints[start_idx:end_idx]

        # Create the output file name
        output_file = f"{output_prefix}_{file_num + 1:03d}.gpx"

        # Overwrite warning
        if Path(output_file).exists():
            print(f"Warning: Overwriting existing file '{output_file}'", file=sys.stderr)

        # Write the new GPX file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_gpx.to_xml())

        # Read-back verification
        try:
            with open(output_file, 'r', encoding='utf-8') as vf:
                verify_gpx = gpxpy.parse(vf)
            expected_count = end_idx - start_idx
            if len(verify_gpx.waypoints) != expected_count:
                print(f"Warning: Read-back verification mismatch in '{output_file}': "
                      f"wrote {expected_count} waypoints but read back "
                      f"{len(verify_gpx.waypoints)}", file=sys.stderr)
        except Exception:
            print(f"Warning: Could not verify output file '{output_file}'", file=sys.stderr)

        waypoints_in_file = end_idx - start_idx
        total_written += waypoints_in_file
        print(f"Created {output_file} with {waypoints_in_file} waypoints (range {start_idx+1}-{end_idx})")

    print(f"Total waypoints written: {total_written}")
    if total_written != total_waypoints:
        print(f"WARNING: Mismatch between parsed waypoints ({total_waypoints}) and written waypoints ({total_written})")

    return total_written

def main():
    """Parse arguments and split a GPX file into smaller files."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Split a GPX file into multiple smaller files')
    parser.add_argument('input_file', help='Input GPX file to split')
    parser.add_argument('output_prefix', nargs='?', help='Prefix for output files (default: input filename)')
    parser.add_argument('--waypoints-per-file', '-w', type=int, default=1000,
                        help='Number of waypoints per output file (default: 1000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output for debugging')

    args = parser.parse_args()

    if args.waypoints_per_file < 1:
        parser.error("--waypoints-per-file must be a positive integer")

    gpx_file = args.input_file

    # Input existence check
    if not Path(gpx_file).exists():
        print(f"Error: Input file '{gpx_file}' not found", file=sys.stderr)
        sys.exit(1)

    # Use input filename as prefix if not specified
    output_prefix = args.output_prefix if args.output_prefix else Path(gpx_file).stem

    # Parse the GPX file
    gpx, waypoint_count = parse_gpx(gpx_file)

    if args.verbose:
        print(f"Detailed waypoints information:")
        print(f"Total waypoints array length: {len(gpx.waypoints)}")
        if gpx.waypoints:
            print(f"First waypoint index: 0, Last waypoint index: {len(gpx.waypoints) - 1}")
        else:
            print("No waypoints found in file.")

    # Create output files
    total_written = create_output_files(gpx, output_prefix, args.waypoints_per_file)

    print(f"Successfully split {gpx_file} into multiple files with prefix '{output_prefix}'")
    print(f"Each file contains up to {args.waypoints_per_file} waypoints")
    print(f"Total waypoints processed: {waypoint_count}, Total waypoints written: {total_written}")

if __name__ == "__main__":
    main()
