# Local memory monitor

Date: 2026-10-28.

## Purpose

Capture process memory before a desktop logout or memory-exhaustion kill.
The monitor writes Markdown snapshots with RAM, swap, process names, parent IDs, and cgroups.
It excludes command arguments and environment variables.
Application totals include visible descendants of each Zed instance, Steam, and Outbound.
Nested game roots have separate totals. The monitor cannot attribute orphaned helpers to their former parents.

## Prerequisites

- Linux with `/proc` and cgroup information.
- Python 3.9 or later.
- A writable local output directory.
- A systemd user manager for monitoring outside the desktop session group.

## Usage

For installation and service setup, see the [repository README](../README.md).

1. Capture one snapshot:

   ```sh
   python3 monitor.py --once --output /path/to/memory-snapshots.md
   ```

2. Capture a snapshot every 30 seconds:

   ```sh
   python3 monitor.py --interval 30 --output /path/to/memory-snapshots.md
   ```

3. For an installed user service, inspect its status:

   ```sh
   systemctl --user status cosmic-memory-monitor.service
   ```

4. Stop an installed monitor:

   ```sh
   systemctl --user disable --now cosmic-memory-monitor.service
   ```

## Expected output and limits

Each timestamp contains memory totals and the largest process memory counters.
Run the application-attribution fixture with `python3 -m unittest -v test_monitor.py`.
Processes can exit during collection. The monitor omits inaccessible or exited processes.
Aggregated RSS can count shared pages more than once.
The monitor stops when its report reaches approximately 64 MiB. Existing evidence remains intact.
Choose a new output file before restarting a full report.
The monitor never terminates applications or changes the system OOM policy.
The user service survives a desktop scope kill while the user manager remains active.
It stops when the user manager stops. An enabled service starts again at the next login.
The monitor does not enable user lingering.
