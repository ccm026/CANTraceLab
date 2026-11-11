# CANTraceLab Roadmap

All time estimates below are for **genuine planned future work**, not completed or paid hours.

## Completed

### Milestone 1 — Offline trace foundation
- CLI trace loading and summary statistics
- Synthetic sample, basic tests, Ruff and Python CI

### Milestone 2 — PySide6 trace viewer
- Desktop frame table, filtering, sorting, error messages, and Qt tests

## Planned development

- **Milestone 3 — DBC decoding (6–10 h):** decode messages, unknown IDs, multiplexed signals; fixture-based tests.
- **Milestone 4 — Signal plotting (5–8 h):** select decoded signals, preserve timestamps, manage scaling and legends.
- **Milestone 5 — Timing diagnostics (6–10 h):** expected periods, timing gaps, jitter, missing message reports.
- **Large-log streaming/indexing (8–12 h):** bounded memory, asynchronous file loading, progress/cancel, performance tests.
- **Trace comparison (6–9 h):** compare recordings, detect changed IDs and signal behavior.
- **Live CAN acquisition (8–12 h):** supported hardware adapters, error recovery, simulation and tests.
- **Reports and further QA (5–8 h):** export reports, test coverage, reproducible releases.

Keep and revise these plans only if they reflect development you actually intend to do.
