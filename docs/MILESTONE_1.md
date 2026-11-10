# Milestone 1 — Offline trace foundation

First software-only slice. Goal: read a CAN-utility trace and summarize frames without hardware.

## Acceptance criteria
- Read local `.log` files using python-can
- Support reader dispatch for `.asc` and `.blf` files through python-can
- Normalize arbitration IDs, timestamps, channel and bytes
- Report total frames, unique IDs, duration
- Reject missing and unsupported files with helpful messages
- Automated tests pass and CI is green

## Limitations
- CLI only; desktop GUI planned separately
- Loading all frames in memory is not suitable for very large recordings yet
- No customer data or proprietary DBCs included
