# Local memory evidence

Date: 2026-10-28.

_Anchors:_ `memory-monitor/monitor.py::snapshot`, `memory-monitor/monitor.py::application_tree_totals`, `memory-monitor/monitor.py::top_applications`, `memory-monitor/toast.py::ToastSettings`, `memory-monitor/toast.py::WarningState`, `memory-monitor/toast.py::toast_position`, `memory-monitor/toast.py::run_toast`, `zed-scope/launcher.py::scope_command`, `zed-scope/launcher.py::launch_detached`, `zed-scope/install.py::install`, `zed-scope/install.py::restore`

- **Memory snapshot:** a local evidence record that helps identify memory consumers before a desktop session ends. See `snapshot`.
- **Application tree:** processes attributed through visible parent links to a supported application. See `application_tree_totals`.
- **Resident memory:** memory currently resident in RAM. Shared pages can appear in more than one process counter.
- **Swap:** process memory currently swapped out. It is reported separately from resident memory.
- **User service:** a monitor launched by the systemd user manager, outside the desktop session group. See `memory-monitor/cosmic-memory-monitor.service`.
- **OOM protection:** the system's separate response to memory exhaustion. This monitor records evidence and leaves that policy unchanged.
- **Warning toast:** a separate popup that provides a visible warning without changing OOM protection. See `run_toast`.
- **Toast colors:** configurable six-digit hex values for the background and text. Valid color pairs remain usable even with low contrast. See `ToastSettings`.
- **Warning state:** a threshold crossing that remains active until memory recovers. Dismissal lasts until recovery. See `WarningState`.
- **Toast position:** a configurable corner within a monitor's work area. Xwayland permits direct placement on COSMIC. See `toast_position`.
- **Application memory estimate:** resident memory attributed through visible parent links and grouped across recognized application instances. Shared pages can appear repeatedly. See `top_applications`.
- **Isolated Zed launch:** a new independent development editor placed in a delegated systemd user scope with a temporary approved memory budget. See `scope_command`.
- **Instance memory budget:** soft RAM, hard RAM, and swap settings applied to an editor scope and its contained helpers. See `scope_command` for the approved values.
- **Launch-path backup:** the original terminal symlink and desktop entry retained for rollback. See `install` and `restore`.
