#!/usr/bin/env python3
"""
GPX Waypoint Deduplicator
Remove duplicate waypoints from GPX files based on various criteria
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import hashlib

class GPXDeduplicator:
    def __init__(self, strategy='time-coords', precision=6, verbose=False, keep_last=False):
        self.strategy = strategy
        self.precision = precision
        self.verbose = verbose
        self.keep_last = keep_last
        self.seen_items = {}
        self.duplicates_removed = 0
        self.total_waypoints = 0
        
    def _get_text(self, element, tag):
        """Helper to extract text from child element"""
        child = element.find(tag)
        return child.text if child is not None else None
    
    def _get_unique_key(self, wpt):
        """Get unique key based on selected strategy"""
        if self.strategy == 'time':
            return self._get_text(wpt, './/time')
            
        elif self.strategy == 'coords':
            lat = wpt.get('lat')
            lon = wpt.get('lon')
            if lat and lon:
                return (
                    round(float(lat), self.precision),
                    round(float(lon), self.precision)
                )
                
        elif self.strategy == 'name':
            return self._get_text(wpt, './/name')
            
        elif self.strategy == 'time-coords':
            time = self._get_text(wpt, './/time')
            lat = wpt.get('lat')
            lon = wpt.get('lon')
            if time and lat and lon:
                return (
                    time,
                    round(float(lat), self.precision),
                    round(float(lon), self.precision)
                )
                
        elif self.strategy == 'hash':
            # Create consistent XML string representation
            wpt_str = ET.tostring(wpt, encoding='unicode').strip()
            return hashlib.sha256(wpt_str.encode()).hexdigest()
            
        return None
    
    def process_gpx(self, input_file, output_file=None):
        """Process GPX file and remove duplicates"""
        self.seen_items = {}
        self.duplicates_removed = 0
        self.total_waypoints = 0
        try:
            # Parse GPX file
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Handle namespaced and non-namespaced GPX
            ns = root.tag.split('}')[0] + '}' if '}' in root.tag else ''
            waypoints = root.findall(f'.//{ns}wpt')
            self.total_waypoints = len(waypoints)
            
            if self.verbose:
                print(f"Found {self.total_waypoints} waypoints in {input_file}")
                print(f"Using strategy: {self.strategy}")
            
            # Track waypoints to remove
            to_remove = []
            
            for wpt in waypoints:
                key = self._get_unique_key(wpt)
                
                if key is None:
                    if self.verbose:
                        print(f"Warning: Could not extract key for waypoint")
                    continue
                
                if key in self.seen_items:
                    # Duplicate found
                    if self.keep_last:
                        # Remove previous, keep current
                        to_remove.append(self.seen_items[key])
                        self.seen_items[key] = wpt
                    else:
                        # Remove current, keep first
                        to_remove.append(wpt)
                    self.duplicates_removed += 1
                    if self.verbose:
                        print(f"Duplicate found: {key}")
                else:
                    self.seen_items[key] = wpt
            
            # Remove duplicates
            for wpt in to_remove:
                root.remove(wpt)
            
            # Determine output path
            if output_file is None:
                p = Path(input_file)
                output_file = p.parent / f"{p.stem}_dedup{p.suffix}"
            
            # Write result
            tree.write(output_file, encoding='UTF-8', xml_declaration=True)
            
            # Report results
            print(f"\nProcessing complete:")
            print(f"  Total waypoints: {self.total_waypoints}")
            print(f"  Duplicates removed: {self.duplicates_removed}")
            print(f"  Unique waypoints: {self.total_waypoints - self.duplicates_removed}")
            print(f"  Output saved to: {output_file}")
            
            return True
            
        except ET.ParseError as e:
            print(f"Error parsing GPX file: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error processing file: {e}", file=sys.stderr)
            return False

def main():
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