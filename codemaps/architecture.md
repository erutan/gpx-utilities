# Architecture Codemap

> Freshness: 2026-02-07 | Source: /Users/erutan/Repos/gpx-utilities

## Overview

Python CLI toolkit — 4 independent modules for GPX waypoint manipulation. Each module is a standalone CLI tool with its own package directory. Minimal dependencies (only `gpxpy` for filter module).

## Project Layout

```
gpx-utilities/
├── gpx_waypoint_combiner/   # Merge multiple GPX files
├── gpx_waypoint_deduper/    # Remove duplicate waypoints
├── gpx_waypoint_filter/     # Filter by text/location/time
├── gpx_waypoint_splitter/   # Split large GPX files
├── gpx_from_radiacode/      # Data directory (non-code)
├── tests/                   # pytest suite (79 tests, 92% coverage)
├── requirements.txt         # gpxpy
└── codemaps/                # Architecture docs
```

## Module Pattern

Each module follows identical structure:
```
gpx_waypoint_<name>/
├── __init__.py              # Empty package marker
├── gpx_waypoint_<name>.py   # Main script + CLI entry point
└── readme.md                # Usage docs
```

## Dependency Graph

```
gpx_waypoint_combiner  ──> xml.etree.ElementTree, argparse, pathlib, datetime
gpx_waypoint_deduper   ──> xml.etree.ElementTree, argparse, pathlib, hashlib
gpx_waypoint_filter    ──> gpxpy (EXTERNAL), argparse, pathlib, copy, typing
gpx_waypoint_splitter  ──> xml.etree.ElementTree, argparse, pathlib, re
```

No cross-module dependencies. Modules are fully independent.

## Entry Points

| Module | Entry | CLI Pattern |
|--------|-------|-------------|
| combiner | `gpx_waypoint_combiner:main()` | `python -m gpx_waypoint_combiner.gpx_waypoint_combiner <files> -o out.gpx` |
| deduper | `gpx_waypoint_deduper:main()` | `python -m gpx_waypoint_deduper.gpx_waypoint_deduper input.gpx -o out.gpx` |
| filter | `gpx_waypoint_filter:main()` | `python -m gpx_waypoint_filter.gpx_waypoint_filter input.gpx out.gpx [flags]` |
| splitter | `gpx_waypoint_splitter:main()` | `python -m gpx_waypoint_splitter.gpx_waypoint_splitter input.gpx prefix -w N` |

## Design Patterns

- **Standalone CLI tools**: Each module uses `argparse` with `if __name__ == '__main__': main()`
- **Class-based core logic**: Combiner (`GPXCombiner`) and Deduper (`GPXDeduplicator`) use classes; Filter (`WaypointFilter`) uses a class; Splitter uses functions only
- **XML handling**: 3 of 4 modules use `xml.etree.ElementTree` directly; filter uses `gpxpy` library
- **Namespace-aware**: All tools handle both namespaced and non-namespaced GPX 1.1 files
- **Deterministic output**: Sorted file ordering, consistent deduplication
- **Graceful error handling**: Missing files, invalid XML, parse errors handled with stderr messages
