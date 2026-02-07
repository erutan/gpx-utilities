# GPX Waypoint Filter

A powerful Python script for filtering waypoints from GPX files based on multiple criteria including text matching, timestamps, and geographic boundaries.

## Features

- **Text-based filtering**: Search waypoint names, symbols, and timestamps
- **Geographic filtering**: Filter by latitude/longitude bounding boxes
- **Flexible logic**: Combine criteria with AND/OR operations
- **Fuzzy matching**: Find partial text matches
- **Duplicate removal**: Automatically removes duplicate waypoints
- **Preserves data**: Maintains all original waypoint attributes

## Installation

### Requirements
- Python 3.6 or higher
- gpxpy library

### Setup
```bash
# Install the required dependency
pip install gpxpy

# Make the script executable (optional)
chmod +x gpx_waypoint_filter.py
```

## Basic Usage

```bash
python gpx_waypoint_filter.py input.gpx output.gpx [OPTIONS]
```

## Command Line Options

### Required Arguments
- `input_file`: Path to the input GPX file
- `output_file`: Path where filtered waypoints will be saved

### Text Filtering Options

#### `--name` (multiple values allowed)
Filter waypoints where the name contains any of the specified strings.
```bash
--name trout salmon "golden pond"
```

#### `--sym` (multiple values allowed)
Filter waypoints where the symbol field contains any of the specified strings.
```bash
--sym fish camping "picnic area"
```

#### `--time` (multiple values allowed)
Filter waypoints where the timestamp contains any of the specified strings.
```bash
--time 2024 "2024-07" "August"
```

### Geographic Filtering Options

#### `--lat-min` (decimal degrees)
Minimum latitude boundary (inclusive).
```bash
--lat-min 37.5
```

#### `--lat-max` (decimal degrees)
Maximum latitude boundary (inclusive).
```bash
--lat-max 38.0
```

#### `--lon-min` (decimal degrees)
Minimum longitude boundary (inclusive).
```bash
--lon-min -119.5
```

#### `--lon-max` (decimal degrees)
Maximum longitude boundary (inclusive).
```bash
--lon-max -118.5
```

### Logic Control Options

#### `--logic` (choices: or, and, bounds-or, bounds-and)
Controls how different criteria groups are combined. Default: `or`

- **`or`**: Match ANY criteria (default)
- **`and`**: Match ALL specified criteria
- **`bounds-or`**: Geographic bounds AND with each other, then OR with text criteria
- **`bounds-and`**: Geographic bounds AND with each other, then AND with text criteria

```bash
--logic bounds-or
```

#### `--bounds-logic` (choices: and, or)
Controls how latitude and longitude bounds are combined. Default: `and`

- **`and`**: Waypoint must be within both lat AND lon bounds
- **`or`**: Waypoint must be within lat OR lon bounds

```bash
--bounds-logic or
```

### Other Options

#### `--case-sensitive`
Enable case-sensitive text matching (default is case-insensitive).
```bash
--case-sensitive
```

#### `--verbose` or `-v`
Display detailed filtering information during processing.
```bash
--verbose
```

## Common Usage Examples

### 1. Filter by Symbol
Find all waypoints with "fish" in the symbol field:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx --sym fish
```

### 2. Filter by Multiple Names
Find waypoints containing any fishing-related terms in the name:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --name trout salmon bass pike "golden pond" brook
```

### 3. Geographic Bounding Box
Get all waypoints within a specific region:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 38.0 \
  --lon-min -119.5 --lon-max -118.5
```

### 4. Combine Geography and Text (AND)
Find camping spots within a specific region:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 38.0 \
  --lon-min -119.5 --lon-max -118.5 \
  --sym camping \
  --logic bounds-and
```

### 5. Combine Geography and Text (OR)
Get waypoints either in the region OR with fishing-related content:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 38.0 \
  --lon-min -119.5 --lon-max -118.5 \
  --sym fish --name trout \
  --logic bounds-or
```

### 6. Filter by Year
Find all waypoints from 2024:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx --time 2024
```

### 7. Complex Multi-Criteria
Waypoints must be in region AND have "camp" in name AND be from 2024:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 38.0 \
  --lon-min -119.5 --lon-max -118.5 \
  --name camp \
  --time 2024 \
  --logic and
```

### 8. Latitude-Only Filtering
Get all waypoints between certain latitudes (any longitude):
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 35.0 --lat-max 40.0
```

### 9. Case-Sensitive Search
Find waypoints with exact case match:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --name "Eagle Lake" "Bear Creek" \
  --case-sensitive
```

### 10. Multiple Symbol Types
Find waypoints with various outdoor activity symbols:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --sym camping fishing hiking "scenic viewpoint" swimming
```

## Advanced Examples

### Fishing Spots in Multiple Regions
Find fishing locations in either of two regions:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 37.5 \
  --lon-min -119.5 --lon-max -119.0 \
  --sym fish \
  --logic bounds-and \
  --bounds-logic or
```

### High Sierra Lakes
Find lakes above a certain latitude with specific names:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.5 \
  --name lake pond reservoir "alpine lake" \
  --logic and
```

### Recent Waypoints in Region
Waypoints from 2023-2024 within bounds:
```bash
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 36.5 --lat-max 38.5 \
  --lon-min -120.0 --lon-max -118.0 \
  --time 2023 2024 \
  --logic bounds-and
```

## Logic Mode Examples

### Understanding `--logic or` (default)
Any single criteria matches:
```bash
# Matches if: has "camp" OR has "fish" OR in bounds
python gpx_waypoint_filter.py input.gpx output.gpx \
  --name camp --sym fish \
  --lat-min 37.0 --lat-max 38.0
```

### Understanding `--logic and`
All specified criteria must match:
```bash
# Matches if: has "camp" AND has "fish" AND in bounds
python gpx_waypoint_filter.py input.gpx output.gpx \
  --name camp --sym fish \
  --lat-min 37.0 --lat-max 38.0 \
  --logic and
```

### Understanding `--logic bounds-or`
Bounds are evaluated together, then OR'd with text:
```bash
# Matches if: (in lat bounds AND in lon bounds) OR has "camp" OR has "fish"
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 38.0 \
  --lon-min -119.0 --lon-max -118.0 \
  --name camp --sym fish \
  --logic bounds-or
```

### Understanding `--logic bounds-and`
Bounds are evaluated together, then AND'd with text:
```bash
# Matches if: (in lat bounds AND in lon bounds) AND (has "camp" OR has "fish")
python gpx_waypoint_filter.py input.gpx output.gpx \
  --lat-min 37.0 --lat-max 38.0 \
  --lon-min -119.0 --lon-max -118.0 \
  --name camp --sym fish \
  --logic bounds-and
```

## Tips and Best Practices

1. **Start broad, then narrow**: Test with lenient criteria first, then add restrictions
2. **Use verbose mode**: Add `-v` to see what's being filtered
3. **Partial matches work**: Searching for "camp" will match "camping", "campground", "basecamp"
4. **Combine criteria thoughtfully**: Understanding the logic modes helps create precise filters
5. **Check your bounds**: Latitude increases going north, longitude increases going east
6. **Remember decimal degrees**: 
   - Latitude: -90 to +90 (negative = south)
   - Longitude: -180 to +180 (negative = west)

## Troubleshooting

### No waypoints in output
- Check if criteria are too restrictive
- Use `--verbose` to see filtering details
- Try broader search terms or larger geographic bounds
- Verify logic mode is appropriate for your query

### Too many waypoints in output
- Add more specific criteria
- Switch from `--logic or` to `--logic and`
- Use exact phrases with `--case-sensitive`
- Narrow geographic bounds

### Script errors
- Ensure input file exists and is valid GPX format
- Check that gpxpy is installed: `pip install gpxpy`
- Verify Python version is 3.6 or higher: `python --version`

## Example Workflow

Filtering a large GPX file for a fishing trip:

```bash
# Step 1: See all fishing-related waypoints
python gpx_waypoint_filter.py all_waypoints.gpx fishing_spots.gpx \
  --sym fish --name trout bass salmon -v

# Step 2: Narrow to specific region
python gpx_waypoint_filter.py all_waypoints.gpx regional_fishing.gpx \
  --sym fish --name trout bass salmon \
  --lat-min 37.2 --lat-max 37.8 \
  --lon-min -119.3 --lon-max -118.7 \
  --logic bounds-and

# Step 3: Filter for recent visits only
python gpx_waypoint_filter.py regional_fishing.gpx recent_fishing.gpx \
  --time 2024

# Step 4: Find specific type with exact name
python gpx_waypoint_filter.py all_waypoints.gpx exact_spots.gpx \
  --name "Golden Trout Lake" --case-sensitive
```

## License

This script is provided as-is for personal and commercial use.

## Contributing

Feel free to suggest improvements or report issues with the script.