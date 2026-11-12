# Milestone 3 — DBC signal decoding

This milestone adds a **read-only DBC decoder** on top of Milestone 2's raw CAN trace viewer.
The raw trace loader, sorting and filters are preserved.

## Scope

- Load `.dbc` files via `cantools.database.load_file` using strict validation.
- Select a frame in the existing table to display its DBC message, scaled engineering values and units.
- Show clear statuses for missing definitions, wrong standard/extended frame format, invalid payload sizes, error frames and remote frames.
- Preserve the previous good DBC if a new DBC fails to load.
- Use a small synthetic DBC file (`samples/demo.dbc`) that matches the existing `samples/demo.log`.
- Add deterministic decoding tests and offscreen Qt integration tests.

## Reproduce on Windows

```bash
cd /e/Projects/CANTraceLab
source .venv/Scripts/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m cantracelab.gui samples/demo.log --dbc samples/demo.dbc
```

Select a row in the CAN table. The lower panel should show decoded values; selecting `0x456` should show `PowertrainStatus`. The Time/ID/channel/payload filters remain available.

## Acceptance criteria

1. The sample DBC loads, and CAN IDs `0x123` and `0x456` decode with documented scaling and units.
2. Unknown CAN IDs do not crash the viewer and keep the raw frame visible.
3. Standard/extended frame format mismatches and invalid DLC/data length are explicitly reported.
4. Remote/error frames do not attempt signal decoding.
5. Invalid DBC imports leave a previously valid database active.
6. The existing CLI and Milestone 1–2 tests continue to pass.
7. GitHub CI completes lint and headless tests on Ubuntu with the Qt dependencies already configured in Milestone 2.

## Current limitations

- DBC decoding only; no live CAN hardware acquisition and no automatic signal graphing yet.
- An offline trace is loaded into memory; large-log streaming comes later.
- Container-style messages, and overlapping standard/extended definitions with the same ID, are not fully supported in this version.
- Use synthetic or otherwise legally shareable DBC data only.
