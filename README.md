# Flaw Nozzle Calculator (Python)

Compute flawed nozzle indices from CSV drop coordinates, mirroring the original WL script. Supports GUI file picking, interactive confirmations, and detailed debug output.

## Features
- Load CSV with `Label, X, Y` columns; labels grouped per image (A/T/C/G/ACT and variants).
- Rotate each label’s points to vertical using small-tilt correction (`atan2(dy, dx)`).
- Infer nozzle indices assuming 636 nozzles and 0.25-step tolerance (overrides via flags).
- Interactive flow: confirm each stage, prompt for machine suffix if not provided.
- Debug print: total labels/points; per-label point count and indices, with out-of-range count if any.
- Export result alongside CSV as `flaw_nozzle_<YYYYMMDD>_680k_<machine>.txt`.

## Requirements
- Python 3.7+.
- `tkinter` (only needed if you rely on the GUI file picker; otherwise provide the CSV path on CLI).

## Usage
CLI with path:
```bash
python3 flaw_nozzle_finder.py path/to/data.csv -m 04
```

GUI to pick file (omit path):
```bash
python3 flaw_nozzle_finder.py -m 04
```

No `-m` flag: you’ll be prompted for the machine identifier during export.

Optional flags:
- `--nozzles N` (default 636)
- `--tolerance T` (default 0.25)

## Interactive Flow
1) Select file (GUI or provided path) → press Enter to load.
2) Labels and point counts displayed → press Enter to compute.
3) Debug info displayed:
   - Total labels/points.
   - Per label: point count, indices, and out-of-range count if present.
   - Combined nozzle list.
4) Press Enter to export; if machine not provided, input it when prompted.
5) Output written next to the CSV.

## Docs and References
- `calculation_process.md`: step-by-step calculation description.
- `rotation_debug_20251122六号机680KResults.md`: rotation debug sample for provided CSV.

## Notes
- Out-of-range points are excluded from indices but reported.
- Rotation uses small-angle correction to avoid swapping X/Y; adjust if your data orientation differs.
