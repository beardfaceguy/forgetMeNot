# Local memory evidence

Date: 2026-10-28.

_Anchors:_ `memory-monitor/monitor.py::snapshot`, `memory-monitor/monitor.py::application_tree_totals`, `memory-monitor/monitor.py::main`

- **Memory snapshot:** a local evidence record that helps identify memory consumers before a desktop session ends. See `snapshot`.
- **Application tree:** processes attributed through visible parent links to a supported application. See `application_tree_totals`.
- **Resident memory:** memory currently resident in RAM. Shared pages can appear in more than one process counter.
- **Swap:** process memory currently swapped out. It is reported separately from resident memory.
- **User service:** a monitor launched by the systemd user manager, outside the desktop session group. See `memory-monitor/cosmic-memory-monitor.service`.
- **OOM protection:** the system's separate response to memory exhaustion. This monitor records evidence and leaves that policy unchanged.
