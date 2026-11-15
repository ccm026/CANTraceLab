# CANTraceLab — CC-CLI v2 project submission checklist

This checklist is for the **project selection form**, not a declaration that future engineering is already complete.

## Required repository checks

- [ ] Public GitHub repository is under the contributor's actual account; URL points to the repository root.
- [ ] Original development history and email attribution are preserved; no squashed/reuploaded replacement history.
- [ ] Root MIT `LICENSE` matches the license selected in the project form; review third-party dependency license obligations.
- [ ] README describes what the software does, the technologies, installation, and both GUI/CLI launch commands.
- [ ] Genuine own commits show development over time, and the default branch has merged Milestones 1–6.
- [ ] Current working tree is clean, tests and Ruff pass on Windows, and the default-branch GitHub Actions run is green.
- [ ] No secrets, confidential CAN traffic, customer information, or proprietary DBC files in files **or Git history**; samples are synthetic.
- [ ] The planned work in `ROADMAP.md` is still realistic and contains **at least 20 hours of work the contributor personally intends to do**.
- [ ] Project is independently owned and not developed for an employer, client, school, or other ineligible entity.
- [ ] Project selection and contributor certification forms are answered accurately, and any extra license approvals are awaited before paid sessions.

## Optional but valuable evidence

- [ ] Add sanitized screenshots of the trace table, decoded signals, plots and timing diagnostics to `screenshots/`, link them in README.
- [ ] Open GitHub Issues for genuinely planned work; avoid padding the repository with fictional commits or artificial tasks.
- [ ] Include PR and CI links in the optional submission-form comments.

## Example honest description

> CANTraceLab is my independently developed, open-source Python desktop application for offline CAN log analysis. It uses PySide6, python-can, cantools and PyQtGraph to inspect recorded traffic, filter CAN frames, decode DBC signals, display trends, and analyze message timing. The application includes synthetic sample logs, automated tests, Ruff checks and GitHub Actions CI. Future work planned in the roadmap includes large-log streaming/indexing, trace comparison, live CAN acquisition and report export.

## Planned work remains

The estimate in the roadmap is **27–41 hours** of future work, provided it remains a sincere personal plan. Do not count Milestone 6 or other completed tasks toward the remaining-work total. Approval is determined by CC-CLI reviewers and is not guaranteed.
