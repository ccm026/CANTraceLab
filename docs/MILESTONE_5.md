# Milestone 5 — CAN bus timing diagnostics

## Scope

Offline, software-only timing analysis of recorded CAN data frames. The existing
file loader, frame filters, DBC decoder and PyQtGraph signal plots are unchanged
in their behavior. The new Timing diagnostics tab is available **without a DBC**.

## Why this feature is useful

A DBC identifies signal meaning, but a decoded signal can still be stale if its
CAN message arrives too slowly or inconsistently. The timing analyzer helps a
developer review captured message intervals and identify *possible* losses or
violations of a separately supplied expected cycle time.

## Analysis model

- Group frames by `(channel, arbitration_id, is_extended_id)`, avoiding
  accidental mixing of multiple CAN buses or standard/extended formats.
- Ignore CAN error/remote frames and frames with non-finite timestamps.
- Sort each group's timestamps before calculating adjacent gaps. Original
  trace order, stored frames, table filtering, and DBC signal plots are untouched.
- Without an expected cycle, report min/mean/median/max gaps and peak absolute
  deviation from the measured median. **Do not issue timing alerts**.
- When the user enables **Check expected cycle**, use their expected interval
  and a percentage tolerance for that selected CAN stream. Flag gaps as
  `on time`, `early`, `late`, or `possible missing`.
- `possible missing` is an **estimate** based on the approximate number of
  expected periods in a long gap, not proof of a lost message.
- One frame gives no interval; gaps before the first or after the last observed
  frame cannot be detected. Capture pauses, timestamp resolution, and sender
  mode changes can resemble message loss.
- The report is recalculated when the selected CAN stream or thresholds change.
  Unlike the raw frame table, the timing report always uses the full trace.

## Demo procedure (Windows / Git Bash)

```bash
cd /e/Projects/CANTraceLab
source .venv/Scripts/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m cantracelab.gui samples/timing_demo.log --dbc samples/demo.dbc
```

1. Select **Timing diagnostics** in the lower half of the window.
2. Select the `vcan0 · 0x123 (standard)` stream.
3. Check **Check expected cycle**; enter `10.00 ms` and `20.0 %` tolerance.
4. Verify the 20 ms gap between +0.020 s and +0.040 s is classified as
   **possible missing**, estimating **one** missed message.
5. Select `vcan0 · 0x456 (standard)`; its three intervals should be nominal
   10 ms and not trigger an alert.
6. Uncheck **Check expected cycle**; measured statistics remain visible, but
   classifications return to **not configured**, without missing alerts.
7. Filter the raw frame table to CAN ID `456`; the selected timing stream's
   intervals should remain unchanged because analysis uses the full log.
8. Revisit **Signal plots** to verify previously implemented plotting works.

The trace and DBC are synthetic demonstration data, not vehicle recordings.

## Acceptance criteria

- Correct grouping, sorting, non-finite/skipped-frame handling and descriptive
  interval statistics verified through pure Python tests.
- Test expected-cycle thresholds, missing estimates, early/late deviations,
  duplicate timestamps, validation and single-frame/empty data.
- Headless Qt tests cover tab creation, stream selection, expected-cycle
  classification, filter independence and compatibility with DBC plots.
- No CAN hardware or network resources needed by tests or CI.
- Existing Milestone 1–4 tests continue to pass; Ruff and GitHub Actions remain
  green before merging into `main`.

## Future enhancements (out of scope)

- Per-ID persistent timing profiles, expected cycles imported from DBC attributes
  where available, cross-trace comparisons, CSV/HTML reports and live capture.
- Qt `invalidateFilter()` deprecation cleanup and float-value formatting remain
  separate maintenance improvements.
