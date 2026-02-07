# GPX Waypoint Deduplicator

A Python script for removing duplicate GPS waypoints from GPX files based on various criteria including timestamps, coordinates, names, or content hashes.

## Features

- **Multiple deduplication strategies**: Remove duplicates based on time, coordinates, names, or complete content
- **Configurable precision**: Adjust coordinate comparison precision for location-based deduplication  
- **Safe processing**: Original files are preserved by default
- **Verbose mode**: See detailed information about duplicates found
- **Flexible output**: Specify custom output filename or use automatic naming
- **Keep first or last**: Choose whether to keep the first (default) or last occurrence of duplicates

## Installation

### Requirements

- Python 3.6 or higher
- No external dependencies (uses Python standard library only)

### Setup

1. Download the script `gpx_dedup.py`
2. Make it executable (Linux/Mac):
   ```bash
   chmod +x gpx_dedup.py
   ```

## Usage

### Basic Usage

Remove duplicates based on both timestamp AND coordinates (default):
```bash
python gpx_dedup.py input.gpx
```

This creates `input_dedup.gpx` with duplicates removed.

### Specify Output File

```bash
python gpx_dedup.py input.gpx -o cleaned.gpx
```

### Deduplication Strategies

#### Time AND Coordinates (default)
Remove only if both time and location are duplicates:
```bash
python gpx_dedup.py track.gpx -s time-coords
```

#### Time-based
Remove waypoints with duplicate timestamps:
```bash
python gpx_dedup.py track.gpx -s time
```

#### Coordinate-based
Remove waypoints at the same location:
```bash
python gpx_dedup.py track.gpx -s coords
```

#### Name-based
Remove waypoints with duplicate names:
```bash
python gpx_dedup.py waypoints.gpx -s name
```

#### Content Hash
Remove waypoints with identical XML content:
```bash
python gpx_dedup.py track.gpx -s hash
```

### Advanced Options

#### Coordinate Precision
Adjust decimal places for coordinate comparison (default: 6):
```bash
# Less precise - will find more "duplicates"
python gpx_dedup.py track.gpx -s coords -p 3

# More precise - will find fewer "duplicates"
python gpx_dedup.py track.gpx -s coords -p 8
```

#### Verbose Output
See detailed processing information:
```bash
python gpx_dedup.py track.gpx -v
```

#### Keep Last Occurrence
By default, the first occurrence of duplicates is kept. To keep the last occurrence instead:
```bash
python gpx_dedup.py track.gpx --keep-last
```

Note: The default behavior is to keep the first occurrence, so there's no need for a `--keep-first` flag.

## Command-Line Flags

| Flag | Long Option | Description | Default |
|------|------------|-------------|---------|
| `-o` | `--output` | Output filename | `input_dedup.gpx` |
| `-s` | `--strategy` | Deduplication strategy | `time-coords` |
| `-p` | `--precision` | Coordinate decimal precision | `6` |
| `-v` | `--verbose` | Enable verbose output | `False` |
| | `--keep-last` | Keep last occurrence instead of first | `False` |

## Examples

### Example 1: Basic Deduplication
Remove duplicate waypoints from a GPS track based on both timestamps and coordinates:
```bash
python gpx_dedup.py morning_run.gpx
```
Output: `morning_run_dedup.gpx`

### Example 2: Clean GPS Logger Output
GPS loggers sometimes create duplicate points at the same location:
```bash
python gpx_dedup.py gps_log.gpx -s coords -p 5 -v
```

### Example 3: Remove Duplicate POIs
Remove duplicate Points of Interest based on names:
```bash
python gpx_dedup.py poi_collection.gpx -s name -o unique_pois.gpx
```

### Example 4: Thorough Cleaning
Remove exact duplicate entries using hash comparison:
```bash
python gpx_dedup.py messy_track.gpx -s hash -v
```

### Example 5: Keep Last Occurrence
When duplicates are found, keep the last occurrence instead of the first:
```bash
python gpx_dedup.py track.gpx --keep-last -v
```

### Example 6: Batch Processing
Process multiple files with a bash loop:
```bash
for file in *.gpx; do
    python gpx_dedup.py "$file" -o "clean_${file}"
done
```

## How It Works

1. **Parsing**: The script parses the GPX XML structure to find all `<wpt>` (waypoint) elements
2. **Key Extraction**: Based on the selected strategy, it extracts a unique key from each waypoint:
   - Time: Contents of `<time>` tags
   - Coords: Latitude and longitude attributes
   - Name: Contents of `<name>` tags
   - Hash: MD5 hash of the entire waypoint XML
3. **Duplicate Detection**: Tracks seen keys and identifies duplicates
4. **Removal**: Removes duplicate waypoints from the XML tree
5. **Output**: Saves the cleaned GPX file

## GPX Structure Example

The script processes waypoints like this:
```xml
<gpx version="1.1">
  <wpt lat="37.7749" lon="-122.4194">
    <time>2024-01-15T10:30:00Z</time>
    <name>Waypoint 1</name>
  </wpt>
  <wpt lat="37.7749" lon="-122.4194">
    <time>2024-01-15T10:30:00Z</time>  <!-- Duplicate time -->
    <name>Waypoint 2</name>
  </wpt>
</gpx>
```

## Limitations

- Currently processes only waypoints (`<wpt>` elements), not track points or routes
- Does not handle track segments (`<trkseg>`) or route points (`<rtept>`)

## Troubleshooting

### "Could not extract unique key"
- The selected strategy couldn't find the required data (e.g., no `<time>` tags when using time strategy)
- Try a different strategy or use `-v` for verbose output

### "Error parsing GPX file"
- Ensure the file is valid GPX XML
- Check for proper XML structure and encoding

### Coordinate Precision Issues
- Adjust `-p` parameter if too many/few duplicates are found
- Lower precision (3-4) for approximate matches
- Higher precision (7-8) for exact matches

## Performance

- Efficient for files with thousands of waypoints
- Memory usage proportional to number of unique waypoints
- Processing time: O(n) where n is the number of waypoints

## License

This script is provided as-is for GPS data management purposes.

## Contributing

Feel free to report issues or suggest improvements!