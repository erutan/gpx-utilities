# GPX Utilities

A collection of standalone Python command-line tools for working with GPX files and GPS data. Each module handles a specific task and can be used independently or chained together in workflows.

## Requirements

- Python 3.6 or higher
- [gpxpy](https://pypi.org/project/gpxpy/)

```bash
pip install -r requirements.txt
```

## Modules

### GPX Waypoint Splitter

Need to import a massive GPX file into a service that limits uploads to 1,000 waypoints? The splitter takes a large GPX file and breaks it into smaller files with a configurable number of waypoints each, preserving all metadata from the original. Just point it at your file and it handles the rest.

See [gpx_waypoint_splitter/readme.md](gpx_waypoint_splitter/readme.md) for details.

### GPX Waypoint Combiner

The opposite of splitting — this merges waypoints from multiple GPX files into a single file. It can process individual files, entire directories, or use wildcards, and supports recursive searching. Handy for consolidating waypoints collected across multiple trips or devices into one file.

See [gpx_waypoint_combiner/readme.md](gpx_waypoint_combiner/readme.md) for details.

### GPX Waypoint Filter

A flexible tool for narrowing down waypoints by text, timestamps, or geographic bounding boxes. You can search names and symbols with fuzzy matching, define lat/lon boundaries, and combine multiple criteria with AND/OR logic. Useful for pulling out just the waypoints you care about from a large collection.

See [gpx_waypoint_filter/readme.md](gpx_waypoint_filter/readme.md) for details.

### GPX Waypoint Deduplicator

Cleans up duplicate waypoints using several strategies — matching by timestamp, coordinates, name, a combination of time and coordinates, or a full content hash. You can tune coordinate precision and choose whether to keep the first or last occurrence of duplicates.

See [gpx_waypoint_deduper/readme.md](gpx_waypoint_deduper/readme.md) for details.

### GPX from Radiacode

Converts Radiacode `.rctrk` radiation survey track files into standard GPX format. It sorts measurement points chronologically and builds a GPX track, automatically naming it with the date and peak count/dose rates. You can optionally include waypoints labeled with the count rate (cps) and dose rate (µSv/h) at each measurement point for easy visualization on a map.

See [gpx_from_radiacode/readme.md](gpx_from_radiacode/readme.md) for details.

## Testing

The project includes a comprehensive test suite across all modules.

```bash
pip install pytest
python -m pytest tests/ -v
```