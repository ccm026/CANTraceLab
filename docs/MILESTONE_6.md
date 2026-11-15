# Milestone 6 — Usability, reliability, and submission preparation

## Scope

This milestone makes targeted quality improvements without creating new CAN-analysis features:

1. Make the Signal plots and Timing diagnostics tab labels readable in the dark desktop theme, including inactive and selected states. Style timing controls consistently.
2. Present decoded numeric values with six significant digits, without rounding the underlying signal objects or plot histories.
3. Avoid the deprecated Qt `QSortFilterProxyModel.invalidateFilter()` API: use `beginFilterChange` / `endFilterChange` on compatible Qt versions and `invalidate()` on older versions.
4. Add automated regression tests and update submission documentation.

## Local verification (Windows / Git Bash)

```bash
cd /e/Projects/CANTraceLab
source .venv/Scripts/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m cantracelab.gui samples/timing_demo.log --dbc samples/demo.dbc
```

### Manual checks

- The two analysis tab labels remain readable when selected and unselected.
- The Timing diagnostics tab continues to classify one *possible missing* message for `vcan0 · 0x123` at 10 ms expected cycle and 20% tolerance.
- Selecting the first frame in the demo log shows `VehicleSpeed = 87.21 km/h` without a long floating-point tail.
- Filtering by CAN ID, channel and payload still works and sorting by timestamp remains numeric.
- Switching between the plot and timing tabs does not change the underlying log or DBC.
- The original CLI (`python -m cantracelab samples/demo.log`) still works.
- GitHub Actions tests and Ruff complete on a PR and on the default branch.

## Known limits and planned work

No live CAN capture, streaming/indexed large-log browsing, two-trace comparison, or export/report generator is added here. These remain future work in [ROADMAP.md](../ROADMAP.md). The included sample traces are synthetic and should not be treated as evidence of real vehicle communication.
