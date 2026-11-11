# Milestone 2 — Desktop CAN Trace Viewer

## Implemented

- Native PySide6 CAN frame table backed by `QAbstractTableModel`
- Numeric timestamp sorting, CAN ID/channel/payload filtering
- File open dialog with `.log`, `.asc`, `.blf` support from the existing loader
- Frame count, unique CAN IDs, duration and filtered frame count
- Load-error messages without discarding the previous trace
- Unit tests for filters and model; headless Qt smoke tests in CI

## Running (Windows Git Bash)

```bash
cd /e/Projects/CANTraceLab
source .venv/Scripts/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m cantracelab.gui samples/demo.log
```

Or use `python -m cantracelab.gui` to start with an empty viewer and click **Open CAN Log**.
The original CLI (`python -m cantracelab samples/demo.log`) is unchanged.

### Manual checks

1. Open the synthetic sample and confirm three rows and two CAN IDs.
2. Enter `123` in the ID filter: two matching frames remain.
3. Enter `vcan0` in the channel filter: both remain.
4. Enter `11 22` in the payload filter: one remains.
5. Clear filters and sort the timestamp column ascending/descending.
6. Attempt an invalid file path: the old data should remain loaded.

## Limitations

- Import is synchronous and holds the entire log in memory, so very large files may freeze the UI.
- CAN ID filter is a hexadecimal substring match, not a decimal ID parser.
- A DBC decoder, live hardware capture and timing diagnostics are not yet implemented.
- Input files must be synthetic, public, or personally owned; no confidential vehicle traces.
