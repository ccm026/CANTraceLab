# CANTraceLab

CANTraceLab is an independent Python project for inspecting offline CAN bus logs and, in future milestones, analyzing decoded automotive signals and message timing.

## Current status — Milestone 2

- Offline `candump`/can-utils `.log` loading; `.asc` and `.blf` loading delegated to `python-can`.
- A command-line summary of frame counts, unique identifiers and trace duration.
- **PySide6 desktop viewer** with frame table, numeric timestamp sorting, and filters for hexadecimal CAN ID, channel and payload.
- File import, explicit errors, a readable empty state and filtered frame counts.
- Fabricated sample trace, automated tests, Ruff linting and GitHub Actions CI.

**Not yet implemented:** DBC decoding, real hardware capture, streaming large files, signal plotting and diagnostics. See [ROADMAP.md](ROADMAP.md).

## Requirements and setup (Windows / Git Bash)

- Python 3.13, Git; no CAN adapter is required for offline logs.

```bash
cd /e/Projects/CANTraceLab
py -3.13 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Desktop application

```bash
python -m cantracelab.gui samples/demo.log
```

Alternatively, run `python -m cantracelab.gui` and click **Open CAN Log…**. Enter a hexadecimal CAN ID such as `123` in the filter field; the viewer matches ID text, not decimal input. The channel and payload filters can be combined with it. Click a column heading to sort.

## Command line

```bash
python -m cantracelab samples/demo.log
```

Expected: 3 frames, 2 unique CAN IDs, about 0.02 seconds duration.

## Tests and code quality

```bash
python -m pytest -q
python -m ruff check .
```

CI sets `QT_QPA_PLATFORM=offscreen` so GUI model and basic window tests can run headlessly. On Windows, leave this unset for normal desktop use.

## Architecture

`python-can LogReader` → `Frame` records → `FrameTableModel` → `TraceFilterProxyModel` → `QTableView`.

The GUI reuses the original `trace.load_frames` logic; filters never modify the source frames.

## Licensing and data

This repository uses the root `LICENSE` file for project code. Third-party libraries (including PySide6/Qt) have their own license conditions. Only synthetic, public, or properly licensed CAN recordings should be uploaded; do not publish employer/customer captures, DBCs or personal data.
