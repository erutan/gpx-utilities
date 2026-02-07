# GPX from Radiacode

A Python script for converting Radiacode `.rctrk` track files to GPX format. Creates a GPX track from radiation measurement data, with an option to include waypoints annotated with count and dose rates.

## Features

- **Track conversion**: Converts Radiacode track markers into a chronologically sorted GPX track
- **Optional waypoints**: Include waypoints with count rate (cps) and dose rate (µSv/h) as names
- **Automatic track naming**: Track name includes date and max readings (e.g., `radiacode 2026-01-28 24.18cps/32.69µSv/h`)
- **Safe processing**: Original files are preserved, overwrite warnings displayed
- **Verbose mode**: See device info, sievert mode, point counts, and max readings
- **Flexible output**: Specify custom output filename or use automatic naming

## Installation

### Requirements

- Python 3.6 or higher
- gpxpy

### Setup

1. Download the script `gpx_from_radiacode.py`
2. Install dependencies:
   ```bash
   pip install gpxpy
   ```
3. Make it executable (Linux/Mac):
   ```bash
   chmod +x gpx_from_radiacode.py
   ```

## Usage

### Basic Usage

Convert a Radiacode track file to a GPX track:
```bash
python gpx_from_radiacode.py track.rctrk
```

This creates `track.gpx` with track points only.

### Include Waypoints

Add waypoints with count/dose rate labels at each measurement point:
```bash
python gpx_from_radiacode.py track.rctrk -w
```

### Specify Output File

```bash
python gpx_from_radiacode.py track.rctrk -o output.gpx
```

### Verbose Output

See device info, sievert mode, and measurement statistics:
```bash
python gpx_from_radiacode.py track.rctrk -v
```

## Command-Line Flags

| Flag | Long Option | Description | Default |
|------|------------|-------------|---------|
| `-o` | `--output` | Output GPX filename | `input_stem.gpx` |
| `-w` | `--waypoints` | Include waypoints with count/dose rate as names | `False` |
| `-v` | `--verbose` | Enable verbose output | `False` |

## Examples

### Example 1: Track Only

Convert a Radiacode track to GPX with just track points (no waypoints):
```bash
python gpx_from_radiacode.py "Track 28 Jan 2026 14-37-02.rctrk"
```
Output: `Track 28 Jan 2026 14-37-02.gpx` with a single track segment.

### Example 2: Track with Measurement Waypoints

Include waypoints labeled with radiation readings at each point:
```bash
python gpx_from_radiacode.py "Track 28 Jan 2026 14-37-02.rctrk" -w -o survey.gpx
```
Each waypoint is named with its readings, e.g., `6.93cps/8.22µSv/h`.

### Example 3: Verbose Conversion

See detailed statistics during conversion:
```bash
python gpx_from_radiacode.py track.rctrk -o output.gpx -v
```
Output:
```
Device: RC-103-006752
Sievert mode: False
Track points: 2187
Max count rate: 24.18 cps
Max dose rate: 32.69 µSv/h

Conversion complete:
  Track name: radiacode 2026-01-28 24.18cps/32.69µSv/h
  Track points: 2187
  Output saved to: output.gpx
```

### Example 4: Batch Processing

Convert multiple track files:
```bash
for file in *.rctrk; do
    python gpx_from_radiacode.py "$file" -w
done
```

## How It Works

1. **Parsing**: Reads the `.rctrk` JSON file containing device info, track periods, and measurement markers
2. **Sorting**: Markers are sorted chronologically by timestamp (they may be unordered in the source file)
3. **Track building**: Creates a GPX track segment with a point for each marker, including latitude, longitude, and timestamp
4. **Track naming**: Generates a name from the start date and maximum count/dose rates found across all markers
5. **Waypoints** (optional): Adds a GPX waypoint at each marker position with the count rate and dose rate as its name
6. **Verification**: Reads back the output file to verify track point and waypoint counts match

## Radiacode .rctrk Format

The `.rctrk` file is JSON with this structure:
```json
{
  "devices": ["RC-103-006752"],
  "sv": false,
  "periods": [
    {"distance": 2314.73, "start": 1769636222, "end": 1769647160}
  ],
  "markers": [
    {
      "lat": 33.875677,
      "lon": -110.983924,
      "date": 1769636251,
      "countRate": 6.93,
      "doseRate": 8.22,
      "acc": 4
    }
  ],
  "start": 1769636222,
  "title": "Track 28 Jan 2026 14:37:02"
}
```

Key fields:
- **`sv`**: Sievert mode flag — `false` for count rate primary, `true` for dose rate primary
- **`markers`**: Array of measurement points with GPS coordinates, unix timestamp, count rate (cps), dose rate (µSv/h), and GPS accuracy
- **`start`**: Unix timestamp of track start (used for track name date)

## GPX Output Structure

### Track only (default)

```xml
<gpx creator="gpx_from_radiacode">
  <trk>
    <name>radiacode 2026-01-28 24.18cps/32.69µSv/h</name>
    <trkseg>
      <trkpt lat="33.875677" lon="-110.983924">
        <time>2026-01-28T14:37:31Z</time>
      </trkpt>
      <!-- ... more track points ... -->
    </trkseg>
  </trk>
</gpx>
```

### With waypoints (`-w`)

```xml
<gpx creator="gpx_from_radiacode">
  <wpt lat="33.875677" lon="-110.983924">
    <time>2026-01-28T14:37:31Z</time>
    <name>6.93cps/8.22µSv/h</name>
  </wpt>
  <!-- ... more waypoints ... -->
  <trk>
    <name>radiacode 2026-01-28 24.18cps/32.69µSv/h</name>
    <trkseg>
      <!-- ... track points ... -->
    </trkseg>
  </trk>
</gpx>
```

## Troubleshooting

### "No markers found in track file"
- The `.rctrk` file has no measurement data — check that the Radiacode recorded marker points during the track

### "Skipping marker with missing coordinates"
- Some markers may lack GPS coordinates (e.g., before a GPS fix was obtained)
- These are skipped; use `-v` to see how many were skipped

### "Warning: No valid track points were generated"
- All markers lacked GPS coordinates — the track file may have been recorded without GPS

### "Warning: Input file does not have .rctrk extension"
- The file will still be processed, but ensure it contains valid Radiacode JSON

## Performance

- Handles track files with thousands of markers efficiently
- The sample 2187-point track converts in under a second
- Memory usage proportional to number of markers

## License

This script is provided as-is for GPS and radiation survey data management purposes.

## Contributing

Feel free to report issues or suggest improvements!