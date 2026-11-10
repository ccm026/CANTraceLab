# CANTraceLab

Offline CAN bus log analysis and diagnostics studio, written in Python.

## Current status — Milestone 1

- Reads `candump`/can-utils `.log` files, and delegates `.asc`/`.blf` parsing to `python-can`.
- Normalizes CAN frames with timestamps, channel, identifier and payload.
- Provides a CLI summary of frame count, unique IDs, and recording duration.
- Includes fabricated sample data, automated tests, and GitHub Actions CI.

**Not yet implemented:** desktop GUI, DBC decoding, timing diagnostics, real CAN hardware support. See [ROADMAP.md](ROADMAP.md).

## Setup (Windows / Git Bash)

```bash
py -3.13 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Try a synthetic CAN trace

```bash
python -m cantracelab samples/demo.log
```

Expected summary: 3 frames, 2 unique identifiers, about 0.02 seconds of recording duration.

## Quality checks

```bash
python -m pytest -q
python -m ruff check .
```

Both commands are also configured in `.github/workflows/python-ci.yml`.

## Licensing

See the repository `LICENSE` file for the license covering CANTraceLab source. Third-party dependencies are governed by their own licenses, including PySide6/Qt's LGPL/GPL/commercial terms.

## Project ownership and data policy

Independent personal project; example traces are synthetic. Do not commit confidential employer/client CAN logs, customer data, or proprietary DBC files.
