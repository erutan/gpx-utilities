# Data Models Codemap

> Freshness: 2026-02-07 | Source: /Users/erutan/Repos/gpx-utilities

## GPX 1.1 Schema (core data format)

All tools operate on GPX 1.1 XML files:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <name>string</name>
    <desc>string</desc>
    <time>ISO-8601</time>
  </metadata>
  <wpt lat="float" lon="float">
    <name>string</name>
    <sym>string</sym>
    <time>ISO-8601</time>
    <desc>string</desc>
    <!-- extensions preserved on copy -->
  </wpt>
</gpx>
```

**Namespace**: `http://www.topografix.com/GPX/1/1` (optional — tools handle both)

## Internal Data Structures

### Combiner — Metadata Dict
```python
metadata: dict = {
    'name': str | None,   # GPX <metadata><name>
    'desc': str | None    # GPX <metadata><desc>
}
```

### Deduper — Unique Key (str)
Generated per strategy:
- `time`: `"<time_text>"`
- `coords`: `"<rounded_lat>,<rounded_lon>"` (precision configurable)
- `name`: `"<name_text>"`
- `time-coords`: `"<time>_<lat>,<lon>"`
- `hash`: SHA256 hex digest of waypoint XML

### Filter — Criteria Dict
```python
criteria: dict = {
    'name_contains': list[str] | None,
    'sym_contains': list[str] | None,
    'time_contains': list[str] | None,
    'lat_min': float | None,
    'lat_max': float | None,
    'lon_min': float | None,
    'lon_max': float | None,
    'case_sensitive': bool,
    'logic_mode': str,    # 'or' | 'and' | 'bounds-or' | 'bounds-and'
    'bounds_logic': str   # 'and' | 'or'
}
```

### Splitter — Parse Result Tuple
```python
(waypoints: list[Element], header: str, namespace: str, count: int)
```

## XML Representations

- **Combiner, Deduper, Splitter**: `xml.etree.ElementTree.Element` objects
- **Filter**: `gpxpy.gpx.GPXWaypoint` objects (with `.latitude`, `.longitude`, `.name`, `.symbol`, `.time` attrs)

## File I/O

All tools read/write UTF-8 encoded GPX XML. The combiner and deduper use `ET.write()` with `xml_declaration=True`. The filter uses `gpxpy`'s built-in serialization.
