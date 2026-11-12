# CANTraceLab

CANTraceLab is an independently developed Python tool for inspecting offline CAN bus logs, filtering frames, and decoding signals using DBC definitions. It is intended for learning and automotive/embedded diagnostics workflows.

## Current status — Milestone 4

- CAN log reading via `python-can` (`.log`, `.asc`, `.blf`).
- CLI trace statistics (frame count, distinct IDs, trace duration).
- PySide6 frame table with CAN ID, channel and payload filtering plus numeric sorting.
- **DBC import** and a decoded-signal panel for the selected frame, showing the message name, scaled values and units.
- Clear handling of unknown CAN IDs, wrong frame format, invalid payload sizes, and remote/error frames.
- **Milestone 4:** interactive PyQtGraph signal trends from the entire decoded CAN trace. Multiple signals are displayed in separate charts so each retains its own engineering-unit axis; mouse wheel zooms, dragging pans, and clicking plot points reports the exact value and relative time.
- A synthetic DBC and CAN log, regression tests, Ruff and GitHub Actions CI.

**Not yet implemented:** cycle-time/jitter diagnostics, background indexing of large files, live CAN hardware capture and categorical-signal plotting. See [ROADMAP.md](ROADMAP.md).

## Setup (Windows / Git Bash)

Requires Python 3.13 and Git. A CAN adapter is **not** required for offline logs.

```bash
cd /e/Projects/CANTraceLab
py -3.13 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Start the desktop viewer with a synthetic trace and DBC

```bash
python -m cantracelab.gui samples/demo.log --dbc samples/demo.dbc
```

Alternatively, launch the viewer alone (`python -m cantracelab.gui`), then click **Open CAN Log…** and **Load DBC…**. Click a frame in the upper table to see the decoded signals in the details panel. Below it, check multiple numeric signals in **Signal trends** and click **Update plots**. Each selected signal has its own chart and units.

The sample files are completely synthetic; for instance CAN ID `0x123` has a `VehicleSpeed` signal (scaled by 0.01 km/h per bit), and CAN ID `0x456` has an `EngineSpeed` signal (scaled by 0.25 rpm per bit). These values are only demonstration data.

You can also run the original CLI:

```bash
python -m cantracelab samples/demo.log
```

## Milestone 4: decoded signal plots

After opening both `samples/demo.log` and `samples/demo.dbc`, CANTraceLab offers numeric signals such as `VehicleSpeed`, `CoolantTemperature` and `EngineSpeed`. Speed signals are selected by default. Check or uncheck any number of available signals and choose **Update plots**; **Clear plots** removes the plots without changing the raw trace or loaded DBC.

- Plots represent the **entire imported trace** independently of table filters or the selected row. Filtering the raw-frame table changes neither the signal history nor the timestamps.
- Horizontal axes show seconds relative to the earliest valid timestamp in the complete trace. Out-of-order frames are sorted chronologically, preserving same-time ordering.
- Each signal appears in **its own** scrollable chart with a y-axis labeled using its DBC engineering unit. This avoids mixing km/h, rpm and temperature on one numeric axis.
- Use the mouse wheel to zoom, drag to pan, and click an individual plotted marker to read the value and relative time in the status bar.
- Unknown CAN IDs, error/remote frames, invalid payload lengths, non-finite measurements and categorical DBC choices are not plotted. Different CAN channels with the same ID are kept separate.
- The current implementation rebuilds plotted histories from an in-memory trace after a successful file/DBC load. Background processing for very large files remains future work.

## Tests and lint

```bash
python -m pytest -q
python -m ruff check .
```

The CI workflow runs on Ubuntu with `QT_QPA_PLATFORM=offscreen` and installs the Qt Linux libraries required for PySide6. It does not require a physical CAN adapter.

## How the software works

1. `python-can` parses the original log into immutable `Frame` records.
2. `FrameTableModel` presents those records; `TraceFilterProxyModel` applies non-destructive filters and sorting.
3. `DbcDecoder` loads a DBC file and decodes the currently selected frame using `cantools`.
4. The decoded-signal panel displays a message name, signal names, values and units. Unknown or invalid frames remain visible in the raw table.
5. `plot_series.extract_signal_series()` constructs finite numeric histories for all supported signals and channels, without changing the raw trace. PyQtGraph renders selected histories in unit-specific interactive charts.

Milestone notes: [Milestone 1](docs/MILESTONE_1.md) · [Milestone 2](docs/MILESTONE_2.md) · [Milestone 3](docs/MILESTONE_3.md) · [Milestone 4](docs/MILESTONE_4.md).

## License and data

This project's own source is distributed under the root `LICENSE` (MIT). Dependencies such as PySide6, Qt and cantools have separate license requirements. Do not publish private employer CAN traces, proprietary DBC files or sensitive vehicle data. The included samples are fictional.
