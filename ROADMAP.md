# CANTraceLab — Development roadmap

Effort estimates are for **real, planned future work**, not work already completed or paid hours. Adjust them based on actual priorities.

## Completed

- **Milestone 1 — Offline trace foundation:** offline loading, CLI statistics, synthetic samples, tests and CI.
- **Milestone 2 — Desktop frame viewer:** filters, sorting, file loading and Qt regression tests.
- **Milestone 3 — DBC signal decoding:** DBC loading, selected-frame engineering signals, explicit error statuses, tests and demo DBC.
- **Milestone 4 — Signal visualization:** unit-aware, interactive plots for multiple numeric DBC signals, time-aligned and isolated by CAN channel, with regression tests.
- **Milestone 5 — Timing diagnostics:** per-channel/ID/format interval statistics, user-configured expected cycles and tolerance, early/late/possible-missing classifications, synthetic timing samples and regression tests.

## Remaining development (planned)

| Workstream | Estimated effort | Goal |
| --- | ---: | --- |
| Large-log streaming/indexing | 8–12 h | Bounded-memory reading, progress/cancel, large-log performance tests |
| Trace comparison | 6–9 h | Compare two traces and identify changed IDs/decoded signals |
| Live CAN acquisition | 8–12 h | Integrate supported interfaces with predictable disconnect handling |
| Reports, testing and release | 5–8 h | Export results and build reproducible QA workflows |
| **Total** | **27–41 h** | |

Do not count completed milestones toward the CC-CLI future-work requirement. Only keep items that are sincerely intended.
