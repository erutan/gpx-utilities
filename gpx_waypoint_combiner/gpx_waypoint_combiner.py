#!/usr/bin/env python3
"""
GPX Waypoint Combiner Tool
Combines waypoints from multiple GPX files into a single GPX file.
"""

import xml.etree.ElementTree as ET
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path


class GPXCombiner:
    def __init__(self):
        # Register namespaces to avoid prefixes in output
        ET.register_namespace('', 'http://www.topografix.com/GPX/1/1')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        
    def extract_waypoints(self, filepath):
        """Extract waypoints from a GPX file."""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Try with namespace first, then without
            waypoints = root.findall('.//{http://www.topografix.com/GPX/1/1}wpt')
            if not waypoints:
                waypoints = root.findall('.//wpt')
            
            return waypoints
            
        except (ET.ParseError, FileNotFoundError) as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
            return []
    
    def create_combined_gpx(self, all_waypoints, metadata=None):
        """Create a new GPX root element with all waypoints."""
        # Create root with namespace - ElementTree handles declaration
        root = ET.Element('{http://www.topografix.com/GPX/1/1}gpx')
        root.set('version', '1.1')
        root.set('creator', 'GPX Waypoint Combiner')
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', 
                'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
        
        # Add metadata if provided
        if metadata and any(metadata.values()):
            meta = ET.SubElement(root, 'metadata')
            
            for tag in ['name', 'desc']:
                if metadata.get(tag):
                    elem = ET.SubElement(meta, tag)
                    elem.text = metadata[tag]
            
            time_elem = ET.SubElement(meta, 'time')
            time_elem.text = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Add waypoints directly
        root.extend(all_waypoints)
        
        return root
    
    def indent(self, elem, level=0):
        """Add pretty-printing indentation to XML."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            last_child = None
            for child in elem:
                self.indent(child, level + 1)
                last_child = child
            if last_child is not None and (not last_child.tail or not last_child.tail.strip()):
                last_child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def combine_files(self, input_files, output_file, metadata=None):
        """Main method to combine multiple GPX files."""
        all_waypoints = []
        stats = {'processed': 0, 'failed': []}
        
        print(f"Processing {len(input_files)} GPX files...")
        
        for filepath in input_files:
            print(f"Reading: {filepath}")
            waypoints = self.extract_waypoints(filepath)
            
            if waypoints:
                all_waypoints.extend(waypoints)
                stats['processed'] += 1
                print(f"  Found {len(waypoints)} waypoints")
            else:
                stats['failed'].append(filepath)
                print(f"  No waypoints found")
        
        if not all_waypoints:
            print("No waypoints found in any file!")
            return False
        
        print(f"\nTotal waypoints collected: {len(all_waypoints)}")
        
        # Create and save combined GPX
        try:
            combined_root = self.create_combined_gpx(all_waypoints, metadata)
            tree = ET.ElementTree(combined_root)
            self.indent(combined_root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            
            print(f"Successfully saved combined GPX to: {output_file}")
            print(f"Files processed successfully: {stats['processed']}")
            
            if stats['failed']:
                print(f"Files that failed: {len(stats['failed'])}")
                for f in stats['failed']:
                    print(f"  - {f}")
            
            return True
            
        except (PermissionError, OSError) as e:
            print(f"Error saving file: {e}", file=sys.stderr)
            return False


def collect_input_files(args):
    """Collect all input files from arguments."""
    input_files = []
    
    # Process directory if specified
    if args.directory:
        directory = Path(args.directory)
        if not directory.exists():
            print(f"Error: Directory {args.directory} does not exist", file=sys.stderr)
            sys.exit(1)
        
        pattern = '**/*.gpx' if args.recursive else '*.gpx'
        input_files.extend(directory.glob(pattern))
    
    # Process individual files/patterns
    if args.files:
        for pattern in args.files:
            path = Path(pattern)
            # Handle wildcards
            if '*' in pattern or '?' in pattern:
                input_files.extend(Path('.').glob(pattern))
            elif path.exists():
                input_files.append(path)
            else:
                print(f"Warning: File not found: {pattern}", file=sys.stderr)
    
    # Remove duplicates while preserving order, then sort for determinism
    seen = set()
    unique_files = []
    for f in input_files:
        s = str(f)
        if s not in seen:
            seen.add(s)
            unique_files.append(s)
    return sorted(unique_files)


def main():
    parser = argparse.ArgumentParser(
        description='Combine waypoints from multiple GPX files into a single GPX file.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMAND LINE OPTIONS:
  files                  GPX files to combine (supports wildcards: *.gpx, track_?.gpx)
  -o, --output OUTPUT    Required. Output GPX file path
  -d, --directory DIR    Directory containing GPX files to process
  -n, --name NAME        Name for the combined GPX file metadata
  --desc DESCRIPTION     Description for the combined GPX file metadata  
  -r, --recursive        Recursively search subdirectories for GPX files
  -h, --help            Show this help message and exit

USAGE EXAMPLES:

Basic File Combination:
  %(prog)s file1.gpx file2.gpx -o combined.gpx
  %(prog)s track1.gpx track2.gpx track3.gpx -o all_tracks.gpx

Using Wildcards:
  %(prog)s *.gpx -o all_waypoints.gpx
  %(prog)s trail_*.gpx -o trails_combined.gpx
  %(prog)s hike_*.gpx bike_*.gpx -o all_activities.gpx

Directory Processing:
  %(prog)s -d ./gpx_folder -o combined.gpx
  %(prog)s -d ./gpx_folder -r -o all_recursive.gpx
  %(prog)s -d ./tracks2023 tracks2024/*.gpx -o all_tracks.gpx

Adding Metadata:
  %(prog)s *.gpx -o combined.gpx -n "European Vacation 2024"
  %(prog)s *.gpx -o combined.gpx -n "Mountain Trails" --desc "Summer 2024 hiking waypoints"
  %(prog)s -d ./vacation -r -o vacation.gpx -n "Vacation" --desc "All POIs and trails"

Advanced Combinations:
  %(prog)s important.gpx favorites.gpx -d ./other_tracks -o final.gpx
  %(prog)s campgrounds.gpx ./poi/*.gpx -d ./tracks -o trip.gpx -n "Pacific Coast"
  %(prog)s -d . -r -o ../output/master.gpx -n "Complete Collection"
        """
    )
    
    parser.add_argument('files', nargs='*', help='GPX files to combine')
    parser.add_argument('-o', '--output', required=True, help='Output GPX file path')
    parser.add_argument('-d', '--directory', help='Directory containing GPX files')
    parser.add_argument('-n', '--name', help='Name for the combined GPX file metadata')
    parser.add_argument('--desc', help='Description for the combined GPX file metadata')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='Recursively search for GPX files in subdirectories')
    
    args = parser.parse_args()
    
    # Collect input files
    input_files = collect_input_files(args)
    
    if not input_files:
        print("Error: No input files specified or found", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # Prepare metadata
    metadata = {'name': args.name, 'desc': args.desc}
    
    # Create combiner and process files
    combiner = GPXCombiner()
    success = combiner.combine_files(input_files, args.output, metadata)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()