# Script Reference

## Launchers

- `run.sh`: Linux and generic POSIX shell launcher. Creates `.venv`, installs dependencies, warns if Qobuz auth is missing, then runs Streamlit.
- `run.command`: macOS Finder-friendly wrapper around `run.sh`.
- `run.bat`: Windows launcher with the same dependency/bootstrap flow as `run.sh`.

## Hosting Helper

- `setup-hbd.sh`: Provisioning helper for HostingByDesign-style boxes. Creates a userland virtualenv, installs dependencies, writes a user `systemd` unit, stores the chosen port, and optionally starts the service.

## Export Helpers

The app generates these on demand in the repo root after export actions:

- `run_rip.sh`
- `run_rip.bat`

Those helper scripts read the per-export Qobuz batch files from `exports/`.
