# Frontend Codemap

> Freshness: 2026-02-07 | Source: /Users/erutan/Repos/gpx-utilities

## Not Applicable

This project is a collection of CLI tools with no frontend/UI layer. All user interaction is through command-line interfaces using `argparse`.

## CLI Interfaces

Each tool exposes a rich CLI with `-h`/`--help` documentation:

| Tool | Positional Args | Key Flags |
|------|----------------|-----------|
| combiner | `input_files` | `-o`, `--name`, `--desc`, `-d` (dir), `-r` (recursive), `-v` |
| deduper | `input_file` | `-o`, `-s` (strategy), `-p` (precision), `--keep-last`, `-v` |
| filter | `input_file`, `output_file` | `--name`, `--sym`, `--time`, `--lat-min/max`, `--lon-min/max`, `--logic`, `--bounds-logic`, `-c`, `-v` |
| splitter | `gpx_file`, `output_prefix` | `-w` (waypoints per file), `-v` |

## Output

All tools write GPX 1.1 XML files. Verbose mode (`-v`) prints progress/stats to stderr.
