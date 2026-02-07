#!/usr/bin/env python3
"""
GPX Waypoint Filter Script
Filters waypoints from a GPX file based on name, symbol, time, and location criteria.
Supports complex AND/OR logic between different filter groups.
"""

import argparse
import copy
import sys
from pathlib import Path
from typing import Set, List, Optional, Dict, Any
import gpxpy
import gpxpy.gpx


class WaypointFilter:
    """Handles filtering logic for GPX waypoints."""
    
    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive
    
    def fuzzy_match(self, text: str, search_terms: List[str]) -> bool:
        """Check if any search terms are contained in the text."""
        if not text or not search_terms:
            return False
        
        if not self.case_sensitive:
            text = text.lower()
            search_terms = [term.lower() for term in search_terms]
        
        return any(term in text for term in search_terms)
    
    def check_bounds(self, value: float, min_val: Optional[float], max_val: Optional[float]) -> bool:
        """Check if a value is within the specified bounds."""
        return (min_val is None or value >= min_val) and (max_val is None or value <= max_val)
    
    def evaluate_waypoint(self, waypoint: gpxpy.gpx.GPXWaypoint, criteria: Dict[str, Any], 
                         logic_mode: str, bounds_logic: str) -> bool:
        """
        Evaluate if a waypoint matches the filter criteria.
        
        Returns:
            True if waypoint should be included, False otherwise
        """
        # Collect text-based matches
        text_matches = []
        if criteria['name_contains']:
            text_matches.append(self.fuzzy_match(waypoint.name, criteria['name_contains']))
        if criteria['sym_contains']:
            text_matches.append(self.fuzzy_match(waypoint.symbol, criteria['sym_contains']))
        if criteria['time_contains']:
            time_str = str(waypoint.time) if waypoint.time else ""
            text_matches.append(self.fuzzy_match(time_str, criteria['time_contains']))
        
        # Collect bounds-based matches
        bounds_matches = []
        has_lat_bounds = criteria['lat_min'] is not None or criteria['lat_max'] is not None
        has_lon_bounds = criteria['lon_min'] is not None or criteria['lon_max'] is not None
        
        if has_lat_bounds:
            bounds_matches.append(
                self.check_bounds(waypoint.latitude, criteria['lat_min'], criteria['lat_max'])
            )
        if has_lon_bounds:
            bounds_matches.append(
                self.check_bounds(waypoint.longitude, criteria['lon_min'], criteria['lon_max'])
            )
        
        # Evaluate based on logic mode
        if logic_mode in ['bounds-or', 'bounds-and']:
            # Complex logic with bounds
            bounds_result = None
            if bounds_matches:
                bounds_result = all(bounds_matches) if bounds_logic == 'and' else any(bounds_matches)
            
            text_result = any(text_matches) if text_matches else None
            
            # Combine results
            results = [r for r in [bounds_result, text_result] if r is not None]
            if not results:
                return False
            
            return all(results) if logic_mode == 'bounds-and' else any(results)
        else:
            # Simple AND/OR logic
            all_matches = text_matches + bounds_matches
            if not all_matches:
                return False
            
            return all(all_matches) if logic_mode == 'and' else any(all_matches)


def filter_waypoints(input_file: str, output_file: str, criteria: Dict[str, Any]) -> int:
    """
    Filter waypoints from a GPX file based on specified criteria.
    
    Args:
        input_file: Path to input GPX file
        output_file: Path to output GPX file
        criteria: Dictionary containing all filter criteria and options
    
    Returns:
        Number of waypoints written to output file
    """
    # Parse input GPX file
    with open(input_file, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)
    
    # Initialize filter
    waypoint_filter = WaypointFilter(criteria['case_sensitive'])
    
    # Create new GPX object for filtered waypoints
    filtered_gpx = gpxpy.gpx.GPX()
    
    # Set to track unique waypoints (based on coordinates and name)
    unique_waypoints: Set[tuple] = set()
    
    for waypoint in gpx.waypoints:
        # Check if waypoint matches criteria
        if not waypoint_filter.evaluate_waypoint(
            waypoint, criteria, criteria['logic_mode'], criteria['bounds_logic']
        ):
            continue
        
        # Create unique identifier for waypoint to avoid duplicates
        waypoint_id = (
            waypoint.latitude,
            waypoint.longitude,
            waypoint.name,
            waypoint.symbol
        )
        
        if waypoint_id in unique_waypoints:
            continue
        
        unique_waypoints.add(waypoint_id)

        # Deep copy to preserve all attributes including extensions
        filtered_gpx.waypoints.append(copy.deepcopy(waypoint))
    
    # Write filtered GPX to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(filtered_gpx.to_xml())
    
    return len(filtered_gpx.waypoints)


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    # Validate input file exists
    if not Path(args.input_file).exists():
        sys.exit(f"Error: Input file '{args.input_file}' not found")
    
    # Check that at least one filter criterion is specified
    has_criteria = any([
        args.name_contains, args.sym_contains, args.time_contains,
        args.lat_min, args.lat_max, args.lon_min, args.lon_max
    ])
    
    if not has_criteria:
        sys.exit("Error: At least one filter criterion must be specified")
    
    # Validate latitude bounds
    if args.lat_min is not None and args.lat_max is not None and args.lat_min > args.lat_max:
        sys.exit(f"Error: lat-min ({args.lat_min}) must be less than lat-max ({args.lat_max})")
    
    # Validate longitude bounds
    if args.lon_min is not None and args.lon_max is not None and args.lon_min > args.lon_max:
        sys.exit(f"Error: lon-min ({args.lon_min}) must be less than lon-max ({args.lon_max})")


def print_verbose_info(args: argparse.Namespace) -> None:
    """Print verbose filtering information."""
    print(f"Reading waypoints from: {args.input_file}")
    print("Filter criteria:")
    
    if args.name_contains:
        print(f"  Name contains: {', '.join(args.name_contains)}")
    if args.sym_contains:
        print(f"  Symbol contains: {', '.join(args.sym_contains)}")
    if args.time_contains:
        print(f"  Time contains: {', '.join(args.time_contains)}")
    if args.lat_min is not None or args.lat_max is not None:
        print(f"  Latitude range: [{args.lat_min or '-∞'}, {args.lat_max or '+∞'}]")
    if args.lon_min is not None or args.lon_max is not None:
        print(f"  Longitude range: [{args.lon_min or '-∞'}, {args.lon_max or '+∞'}]")
    
    print(f"  Case sensitive: {args.case_sensitive}")
    print(f"  Logic mode: {args.logic}")
    if args.logic in ['bounds-or', 'bounds-and']:
        print(f"  Bounds logic: {args.bounds_logic}")
    print()


def main():
    """Parse arguments and filter waypoints from a GPX file."""
    parser = argparse.ArgumentParser(
        description='Filter waypoints from a GPX file based on name, symbol, time, and location criteria.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Logic Modes:
  --logic or       : Match ANY criteria (default)
  --logic and      : Match ALL specified criteria
  --logic bounds-or: Location bounds AND each other, OR with text criteria
  --logic bounds-and: Location bounds AND each other, AND with text criteria

Bounds Logic:
  --bounds-logic and: Must be within both lat AND lon bounds (default)
  --bounds-logic or : Must be within lat OR lon bounds

Examples:
  # Filter waypoints within a bounding box
  %(prog)s input.gpx output.gpx --lat-min 37.0 --lat-max 38.0 --lon-min -119.5 --lon-max -118.5
  
  # Filter waypoints in a region AND with "fish" in symbol
  %(prog)s input.gpx output.gpx --lat-min 37.0 --lat-max 38.0 --lon-min -119.5 --lon-max -118.5 \\
           --sym fish --logic bounds-and
  
  # Complex: (within bounds) OR (has "fish" in symbol) OR (has "camp" in name)
  %(prog)s input.gpx output.gpx --lat-min 37.0 --lat-max 38.0 --lon-min -119.5 --lon-max -118.5 \\
           --sym fish --name camp --logic bounds-or
        """
    )
    
    # Required arguments
    parser.add_argument('input_file', help='Input GPX file path')
    parser.add_argument('output_file', help='Output GPX file path')
    
    # Text-based filters
    parser.add_argument('--name', nargs='+', dest='name_contains',
                       help='Filter waypoints with names containing these strings')
    parser.add_argument('--sym', nargs='+', dest='sym_contains',
                       help='Filter waypoints with symbols containing these strings')
    parser.add_argument('--time', nargs='+', dest='time_contains',
                       help='Filter waypoints with times containing these strings')
    
    # Location-based filters
    parser.add_argument('--lat-min', type=float, help='Minimum latitude (decimal degrees)')
    parser.add_argument('--lat-max', type=float, help='Maximum latitude (decimal degrees)')
    parser.add_argument('--lon-min', type=float, help='Minimum longitude (decimal degrees)')
    parser.add_argument('--lon-max', type=float, help='Maximum longitude (decimal degrees)')
    
    # Logic options
    parser.add_argument('--logic', choices=['or', 'and', 'bounds-or', 'bounds-and'],
                       default='or', help='Logic mode for combining criteria (default: or)')
    parser.add_argument('--bounds-logic', choices=['and', 'or'], default='and',
                       help='Logic for combining lat/lon bounds (default: and)')
    
    # Other options
    parser.add_argument('--case-sensitive', action='store_true',
                       help='Perform case-sensitive string matching')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print detailed information about filtering')
    
    args = parser.parse_args()
    
    # Validate arguments
    validate_args(args)
    
    # Print verbose info if requested
    if args.verbose:
        print_verbose_info(args)
    
    # Prepare criteria dictionary
    criteria = {
        'name_contains': args.name_contains,
        'sym_contains': args.sym_contains,
        'time_contains': args.time_contains,
        'lat_min': args.lat_min,
        'lat_max': args.lat_max,
        'lon_min': args.lon_min,
        'lon_max': args.lon_max,
        'case_sensitive': args.case_sensitive,
        'logic_mode': args.logic,
        'bounds_logic': args.bounds_logic
    }
    
    # Perform filtering
    try:
        waypoints_count = filter_waypoints(
            args.input_file,
            args.output_file,
            criteria
        )
        
        print(f"Successfully filtered {waypoints_count} unique waypoint(s) to '{args.output_file}'")
        
    except Exception as e:
        sys.exit(f"Error processing GPX file: {e}")


if __name__ == '__main__':
    main()