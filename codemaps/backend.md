# Backend Codemap

> Freshness: 2026-02-07 | Source: /Users/erutan/Repos/gpx-utilities

## Module Details

### gpx_waypoint_combiner (237 lines)

**Class: `GPXCombiner`**
- `extract_waypoints(filepath)` — Parse GPX, return list of waypoint Elements
- `create_combined_gpx(all_waypoints, metadata)` — Build combined GPX XML tree
- `indent(elem, level)` — Pretty-print XML indentation
- `combine_files(input_files, output_file, metadata)` — Orchestrate merge

**Function: `collect_input_files(args)`** — Gather files from args (supports dirs, recursive, glob), deduplicate, sort

**Function: `main()`** — argparse CLI: `-o`, `--name`, `--desc`, `-d`, `-r`, `-v`

---

### gpx_waypoint_deduper (205 lines)

**Class: `GPXDeduplicator`**
- `__init__(strategy, precision, verbose, keep_last)` — Config + state init
- `_get_text(element, tag)` — Safe child text extraction
- `_get_unique_key(wpt)` — Generate dedup key per strategy
- `process_gpx(input_file, output_file)` — Read, dedup, write GPX

**Strategies**: `time` | `coords` | `name` | `time-coords` (default) | `hash`

**Function: `main()`** — argparse CLI: `-o`, `-s`, `-p`, `--keep-last`, `-v`

---

### gpx_waypoint_filter (294 lines)

**Class: `WaypointFilter`**
- `__init__(case_sensitive)` — Set case mode
- `fuzzy_match(text, search_terms)` — Substring match against terms
- `check_bounds(value, min_val, max_val)` — Numeric range check
- `evaluate_waypoint(waypoint, criteria, logic_mode, bounds_logic)` — Full filter evaluation

**Function: `filter_waypoints(input_file, output_file, criteria)`** — Parse with gpxpy, apply filter, deduplicate, write

**Function: `validate_args(args)`** — Check CLI arg consistency

**Function: `main()`** — argparse CLI: `--name`, `--sym`, `--time`, `--lat-min/max`, `--lon-min/max`, `--logic`, `--bounds-logic`, `-c`, `-v`

---

### gpx_waypoint_splitter (142 lines)

**Function: `parse_gpx(gpx_file)`** — Parse GPX, return `(waypoints, header, namespace, count)`

**Function: `create_output_files(waypoints, header, namespace, output_prefix, waypoints_per_file)`** — Distribute waypoints across numbered output files

**Function: `main()`** — argparse CLI: `-w`, `-v`

## Import Map (source modules only)

```
combiner.py  ← ET, sys, argparse, datetime, pathlib
deduper.py   ← argparse, sys, ET, pathlib, hashlib
filter.py    ← argparse, copy, sys, pathlib, typing, gpxpy
splitter.py  ← sys, ET, re, argparse, pathlib
```
