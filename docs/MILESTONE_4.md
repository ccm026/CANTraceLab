# Milestone 4 — Interactive decoded CAN signal plots

This milestone extends the existing DBC-enabled viewer. It does **not** change raw CAN frame parsing, filtering, sorting, or the DBC selected-frame details panel.

## Implemented

- New pure, tested `plot_series.py` module converts DBC decoded frames to time/value arrays.
- Standard and extended frames, different channels, and distinct DBC signals are kept separate.
- Invalid/unknown/remote/error frames and non-finite or categorical values do not create numeric plot points.
- Frame timestamps are normalized to the earliest finite timestamp in the full trace and sorted chronologically.
- The GUI lists available numeric signals with checkboxes and renders one PyQtGraph chart per selected signal.
- Each chart has its own engineering-unit y-axis and signal legend, with pan, zoom and clickable markers for point inspection.
- Plots use the full trace: table filters and row selection do not change plot data.
- PyQtGraph plots are refreshed after successful trace or DBC loading; invalid file uploads preserve the previous data and charts.

## Run on Windows

```bash
cd /e/Projects/CANTraceLab
source .venv/Scripts/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m cantracelab.gui samples/demo.log --dbc samples/demo.dbc
```

## Manual acceptance checklist

1. Raw table, frame filters, sorting, and the decoded-signals panel continue to work.
2. Two speed charts appear by default when the sample log and DBC are loaded.
3. Check VehicleSpeed, EngineSpeed and CoolantTemperature and click **Update plots**. Three independently labeled unit-specific charts appear.
4. Zoom and pan each chart. Click a marker and confirm the status bar shows its exact time and value.
5. Filter to CAN ID `456`; the raw table narrows but plotted series still represent the full trace.
6. Click **Clear plots** and confirm the raw trace and DBC remain loaded.
7. Load an invalid DBC or trace; the last valid plot data remains intact.
8. Automated tests and Ruff pass locally and in GitHub Actions.

## Limitations / future work

- Offline, memory-resident logs; enormous traces will eventually need background indexing and rendering decimation.
- Categorical DBC choices (for example, Mode=Sport) are shown in the selected-frame details but not plotted on numeric axes.
- Signals are displayed in separate plots rather than combined on a multi-axis chart; this avoids confusing mixed engineering units.
- No hardware interface, trigger engine, timing diagnostics, or export yet.
- Keep the known Qt `invalidateFilter()` deprecation cleanup as a distinct maintenance task.
