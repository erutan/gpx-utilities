#!/usr/bin/env python3
"""
GPX Splitter - Splits a large GPX file into multiple smaller files with customizable number of waypoints.
Usage: python gpx_splitter.py input.gpx [output_prefix] [--waypoints-per-file=1000]
"""

import sys
import os
import xml.etree.ElementTree as ET
import re
import argparse

def parse_gpx(gpx_file):
    """Parse a GPX file and extract all waypoints."""
    try:
        # Parse the GPX file
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        
        # Define namespace dictionary based on the input file
        # Most GPX files use this namespace
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        
        # Try to find the namespace if it's not the default one
        if root.tag != 'gpx' and '{' in root.tag:
            ns_match = re.match(r'\{(.+?)\}', root.tag)
            if ns_match:
                namespace = ns_match.group(1)
                ns = {'gpx': namespace}
        
        # Find all waypoints using the namespace
        waypoints = root.findall('.//gpx:wpt', ns)
        
        # If no waypoints found with namespace, try without namespace
        if not waypoints:
            waypoints = root.findall('.//wpt')
            if waypoints:
                ns = {}  # Empty namespace
        
        waypoint_count = len(waypoints)
        print(f"Found {waypoint_count} waypoints in {gpx_file}")
        
        # Extract the header structure (everything except waypoints)
        header = root
        
        return waypoints, header, ns, waypoint_count
    
    except Exception as e:
        print(f"Error parsing GPX file: {e}")
        sys.exit(1)

def create_output_files(waypoints, header, namespace, output_prefix, waypoints_per_file=1000):
    """Split waypoints into multiple files with specified number of waypoints each."""
    total_waypoints = len(waypoints)
    
    # Calculate number of output files needed
    num_files = (total_waypoints + waypoints_per_file - 1) // waypoints_per_file  # Ceiling division
    
    print(f"Splitting {total_waypoints} waypoints into {num_files} files with up to {waypoints_per_file} waypoints each")
    total_written = 0
    
    # Create each output file
    for file_num in range(num_files):
        start_idx = file_num * waypoints_per_file
        end_idx = min((file_num + 1) * waypoints_per_file, total_waypoints)
        
        # Create a new GPX tree
        new_root = ET.Element(header.tag, header.attrib)
        
        # Copy over metadata and other non-waypoint elements
        for child in header:
            # Skip waypoint elements in the original header
            if 'wpt' not in child.tag:
                new_root.append(ET.fromstring(ET.tostring(child)))
        
        # Add waypoints for this file
        current_waypoints = waypoints[start_idx:end_idx]
        for wpt in current_waypoints:
            new_root.append(ET.fromstring(ET.tostring(wpt)))
        
        # Create the output file name
        output_file = f"{output_prefix}_{file_num + 1:03d}.gpx"
        
        # Write the new GPX file
        tree = ET.ElementTree(new_root)
        ET.register_namespace('', namespace.get('gpx', ''))
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        waypoints_in_file = len(current_waypoints)
        total_written += waypoints_in_file
        print(f"Created {output_file} with {waypoints_in_file} waypoints (range {start_idx+1}-{end_idx})")
    
    print(f"Total waypoints written: {total_written}")
    if total_written != total_waypoints:
        print(f"WARNING: Mismatch between parsed waypoints ({total_waypoints}) and written waypoints ({total_written})")
    
    return total_written

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Split a GPX file into multiple smaller files')
    parser.add_argument('input_file', help='Input GPX file to split')
    parser.add_argument('output_prefix', nargs='?', help='Prefix for output files (default: input filename)')
    parser.add_argument('--waypoints-per-file', '-w', type=int, default=1000, 
                        help='Number of waypoints per output file (default: 1000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output for debugging')
    
    args = parser.parse_args()
    
    gpx_file = args.input_file
    
    # Use input filename as prefix if not specified
    output_prefix = args.output_prefix if args.output_prefix else os.path.splitext(gpx_file)[0]
    
    # Parse the GPX file
    waypoints, header, namespace, waypoint_count = parse_gpx(gpx_file)
    
    if args.verbose:
        print(f"Detailed waypoints information:")
        print(f"Total waypoints array length: {len(waypoints)}")
        print(f"First waypoint index: 0, Last waypoint index: {len(waypoints) - 1}")
    
    # Create output files
    total_written = create_output_files(waypoints, header, namespace, output_prefix, args.waypoints_per_file)
    
    print(f"Successfully split {gpx_file} into multiple files with prefix '{output_prefix}'")
    print(f"Each file contains up to {args.waypoints_per_file} waypoints")
    print(f"Total waypoints processed: {waypoint_count}, Total waypoints written: {total_written}")

if __name__ == "__main__":
    main()
