# GPX Waypoint Combiner

A Python command-line tool that merges waypoints from multiple GPX files into a single file while preserving all waypoint data and metadata.

## Features

- Combine waypoints from multiple GPX files
- Preserve all waypoint attributes (coordinates, elevation, names, descriptions)
- Process entire directories of GPX files
- Recursive directory searching
- Wildcard support for file selection
- Add custom metadata to combined files
- No external dependencies required

## Requirements

- Python 3.x

## Installation

```bash
# Download the script
curl -O https://raw.githubusercontent.com/yourusername/gpx-combiner/main/gpx_combiner.py

# Make executable (Unix/Linux/Mac)
chmod +x gpx_combiner.py
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `files` | GPX files to combine (supports wildcards: *.gpx, track_?.gpx) |
| `-o, --output` | **Required.** Output GPX file path |
| `-d, --directory` | Directory containing GPX files to process |
| `-n, --name` | Name for the combined GPX file metadata |
| `--desc` | Description for the combined GPX file metadata |
| `-r, --recursive` | Recursively search subdirectories for GPX files |
| `-h, --help` | Show help message and exit |

## Usage Examples

### Basic File Combination
```bash
# Combine two specific files
python gpx_combiner.py file1.gpx file2.gpx -o combined.gpx

# Combine multiple files
python gpx_combiner.py track1.gpx track2.gpx track3.gpx -o all_tracks.gpx
```

### Using Wildcards
```bash
# Combine all GPX files in current directory
python gpx_combiner.py *.gpx -o all_waypoints.gpx

# Combine files matching a pattern
python gpx_combiner.py trail_*.gpx -o trails_combined.gpx

# Combine files with different patterns
python gpx_combiner.py hike_*.gpx bike_*.gpx -o all_activities.gpx
```

### Directory Processing
```bash
# Process all GPX files in a specific directory
python gpx_combiner.py -d ./gpx_folder -o combined.gpx

# Process directory recursively (includes subdirectories)
python gpx_combiner.py -d ./gpx_folder -r -o all_recursive.gpx

# Combine multiple directories
python gpx_combiner.py -d ./tracks2023 tracks2024/*.gpx -o all_tracks.gpx
```

### Adding Metadata
```bash
# Add a name to the combined file
python gpx_combiner.py *.gpx -o combined.gpx -n "European Vacation 2024"

# Add both name and description
python gpx_combiner.py *.gpx -o combined.gpx \
    -n "Mountain Trails" \
    --desc "Summer 2024 hiking waypoints"

# Full example with recursive directory search and metadata
python gpx_combiner.py -d ./vacation -r -o vacation.gpx \
    -n "Vacation Waypoints" \
    --desc "All POIs and trails from summer trip"
```

### Advanced Combinations
```bash
# Mix individual files with directory contents
python gpx_combiner.py important.gpx favorites.gpx -d ./other_tracks -o final.gpx

# Combine files from multiple sources with metadata
python gpx_combiner.py campgrounds.gpx ./poi/*.gpx -d ./tracks -o trip.gpx \
    -n "Pacific Coast Road Trip"

# Process current directory recursively
python gpx_combiner.py -d . -r -o ../output/master.gpx \
    -n "Complete GPX Collection"
```

## Output Format

The tool generates a valid GPX 1.1 file containing:
- All waypoints from input files with preserved attributes
- Proper XML structure with GPX schema declaration
- Optional metadata section with name, description, and timestamp
- Pretty-printed XML for readability

## Common Use Cases

### Hiking/Trail Management
Combine waypoints from multiple hiking trips into a master file:
```bash
python gpx_combiner.py -d ./hikes -r -o all_trails.gpx \
    -n "Trail Collection" --desc "All hiking waypoints 2020-2024"
```

### GPS Device Consolidation
Merge waypoints from different GPS devices:
```bash
python gpx_combiner.py garmin_*.gpx suunto_*.gpx -o all_devices.gpx
```

### Trip Planning
Combine POIs, campsites, and route waypoints:
```bash
python gpx_combiner.py pois.gpx camps.gpx routes.gpx -o trip_plan.gpx \
    -n "Utah Parks Trip" --desc "All waypoints for May 2024 trip"
```

### Backup and Archive
Create a complete backup of all GPX waypoints:
```bash
python gpx_combiner.py -d ~/Documents/GPX -r -o ~/Backups/gpx_backup.gpx \
    -n "GPX Backup" --desc "Complete waypoint backup $(date +%Y-%m-%d)"
```

## Troubleshooting

### No waypoints found
- Ensure your GPX files contain `<wpt>` elements (waypoints), not just tracks or routes
- Check that files are valid GPX format

### Permission denied
- Make sure you have read permissions for input files
- Ensure write permission for the output directory