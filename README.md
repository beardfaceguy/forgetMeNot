# forgetMeNot

Personal Linux tools and setup instructions that survive an OS reinstall.

## Memory monitor

The [memory monitor](memory-monitor/README.md) records RAM, swap, processes, and application trees in a local Markdown file.
It runs as a systemd user service, separately from the desktop session group.

The tool records evidence and displays a live memory-warning toast.
It does not kill applications or change the system OOM policy.

The toast defaults to background `#FCEE0A` and text `#000000`.
Its JSON configuration controls the screen corner, monitor, margins, colors, thresholds, and refresh interval.

## Installation and setup on CachyOS or Arch Linux

Requirements: Linux, Python 3.9 or later, Git, and a systemd user manager.
The toast also needs GTK 3, PyGObject, and an X11 display or Xwayland.
Run the package command with `sudo`. Run all other commands as your normal desktop user.

### 1. Install dependencies

```sh
sudo pacman -Syu --needed git python python-gobject gtk3 xorg-xwayland
```

### 2. Clone the repository

```sh
git clone https://github.com/beardfaceguy/forgetMeNot.git
cd forgetMeNot
```

If you already cloned the repository, enter that directory and continue with step 3.

### 3. Install the tool and enable startup

Run these commands from the repository root in a terminal within your desktop session:

```sh
install -Dm755 memory-monitor/monitor.py "$HOME/.local/lib/forgetmenot/monitor.py"
install -Dm755 memory-monitor/toast.py "$HOME/.local/lib/forgetmenot/toast.py"
if ! test -e "$HOME/.config/forgetmenot/memory-toast.json"; then
  install -Dm644 memory-monitor/memory-toast.json "$HOME/.config/forgetmenot/memory-toast.json"
fi
install -Dm644 memory-monitor/cosmic-memory-monitor.service "$HOME/.config/systemd/user/cosmic-memory-monitor.service"
install -Dm644 memory-monitor/forgetmenot-memory-toast.service "$HOME/.config/systemd/user/forgetmenot-memory-toast.service"
systemctl --user daemon-reload
systemctl --user enable cosmic-memory-monitor.service
systemctl --user enable forgetmenot-memory-toast.service
systemctl --user restart cosmic-memory-monitor.service
systemctl --user restart forgetmenot-memory-toast.service
```

The commands install or replace both user services and preserve an existing toast configuration.
The logger writes snapshots to `~/.local/state/forgetmenot/memory-samples.md` every 30 seconds.
The services start automatically at future logins. They run while your user session manager is active.

### 4. Verify the installation

```sh
systemctl --user status cosmic-memory-monitor.service
systemctl --user status forgetmenot-memory-toast.service
tail -n 25 "$HOME/.local/state/forgetmenot/memory-samples.md"
```

Both services should report `active (running)`.
The toast normally stays hidden below its warning threshold.
Show a 20-second preview with actual live memory use:

```sh
python3 "$HOME/.local/lib/forgetmenot/toast.py" --preview
```

The preview should appear in the upper-right corner with a yellow background and black text.
It displays RAM use, swap use, and the top three application estimates.

## Test without installing

```sh
python3 -m unittest discover -s memory-monitor -p 'test_*.py' -v
python3 memory-monitor/monitor.py --once --output /tmp/forgetmenot-memory-sample.md
python3 memory-monitor/toast.py --config memory-monitor/memory-toast.json --preview
```

## Update an installed copy

From your existing checkout, run:

```sh
git pull --ff-only
```

Then repeat installation step 3 to copy the updated scripts and restart the services.
Your existing toast configuration remains intact.

## Stop the monitor

```sh
systemctl --user disable --now cosmic-memory-monitor.service
systemctl --user disable --now forgetmenot-memory-toast.service
```

## Configure the toast

Edit `~/.config/forgetmenot/memory-toast.json` in your text editor.
The [default configuration](memory-monitor/memory-toast.json) provides a complete example.

| Setting | Purpose |
|---|---|
| `warning_percent` | RAM percentage that makes the toast appear. |
| `clear_percent` | Recovery threshold below which the toast clears and rearms. |
| `refresh_seconds` | Interval between live updates. |
| `position` | Screen corner: `top-right`, `top-left`, `bottom-right`, or `bottom-left`. |
| `monitor` | `primary` or a zero-based monitor index. |
| `margin` | Distance from the selected screen edges, in logical pixels. |
| `background` | Background color as a `#RRGGBB` hex string. |
| `foreground` | Text color as a `#RRGGBB` hex string. |

Keep `clear_percent` lower than `warning_percent`.
Apply your changes:

```sh
systemctl --user restart forgetmenot-memory-toast.service
```

The default position is `top-right`. Other positions are `top-left`, `bottom-right`, and `bottom-left`.
`monitor` accepts `primary` or a zero-based monitor index. `margin` sets the inset in logical pixels.
`background` and `foreground` accept configurable `#RRGGBB` colors.
The tool reports low text contrast in its service log and applies the configured colors.

By default, the toast appears at 85% RAM use and remains until use drops below 80%.
It refreshes every two seconds. The percentage uses `MemAvailable` to account for reclaimable cache.
The top three application totals include visible helpers and all recognized instances.
Those RSS totals can count shared pages more than once. They are approximate RAM estimates.

The close button dismisses the current warning until RAM recovers below the clearing threshold.
The toast uses Xwayland on COSMIC so its placement and colors remain independent of the desktop notification theme.
It does not appear in COSMIC's notification history or obey notification do-not-disturb settings.

To check the current settings visually, run the preview command from installation step 4.

## Troubleshooting

If a service fails, inspect its logs:

```sh
journalctl --user -u forgetmenot-memory-toast.service -b -n 50 --no-pager
journalctl --user -u cosmic-memory-monitor.service -b -n 50 --no-pager
```

If the toast cannot connect to a display, run it from your graphical desktop session.
On Wayland, ensure Xwayland is installed and enabled.
If an import fails for `gi` or GTK, install the dependencies from step 1.

If no warning appears during normal use, check the threshold or run the preview.
If a configuration change has no effect, restart the toast service after saving the file.

The logger stops when its report reaches approximately 64 MiB.
Archive that report under a new filename, then restart `cosmic-memory-monitor.service` to start a fresh report.

## Installed files

| Path | Purpose |
|---|---|
| `~/.local/lib/forgetmenot/` | Installed Python scripts. |
| `~/.config/forgetmenot/memory-toast.json` | Your toast settings. |
| `~/.config/systemd/user/cosmic-memory-monitor.service` | Logger startup and resource limits. |
| `~/.config/systemd/user/forgetmenot-memory-toast.service` | Toast startup and resource limits. |
| `~/.local/state/forgetmenot/memory-samples.md` | Local memory evidence. |

## Context

See [CONTEXT-MAP.md](CONTEXT-MAP.md) for terminology and source anchors.
