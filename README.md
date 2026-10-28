# forgetMeNot

Personal Linux tools and setup instructions that survive an OS reinstall.

## Memory monitor

The [memory monitor](memory-monitor/README.md) records RAM, swap, processes, and application trees in a local Markdown file.
It runs as a systemd user service, separately from the desktop session group.

The tool records evidence and displays a live memory-warning toast.
It does not kill applications or change the system OOM policy.

The toast defaults to background `#FCEE0A` and text `#000000`.
Its JSON configuration controls the screen corner, monitor, margins, colors, thresholds, and refresh interval.

## Install after an OS reinstall

Requirements: Linux, Python 3.9 or later, Git, and a systemd user manager.
The toast also needs GTK 3, PyGObject, and an X11 display or Xwayland.
On CachyOS or Arch, the GUI packages are `gtk3`, `python-gobject`, and `xorg-xwayland`.
Run these commands from the repository root:

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
The service writes snapshots to `~/.local/state/forgetmenot/memory-samples.md`.

Verify it:

```sh
systemctl --user status cosmic-memory-monitor.service
systemctl --user status forgetmenot-memory-toast.service
tail -n 25 "$HOME/.local/state/forgetmenot/memory-samples.md"
```

## Test without installing

```sh
python3 -m unittest discover -s memory-monitor -p 'test_*.py' -v
python3 memory-monitor/monitor.py --once --output /tmp/forgetmenot-memory-sample.md
python3 memory-monitor/toast.py --config memory-monitor/memory-toast.json --preview
```

## Update an installed copy

Run `git pull --ff-only`, then repeat the installation commands.

## Stop the monitor

```sh
systemctl --user disable --now cosmic-memory-monitor.service
systemctl --user disable --now forgetmenot-memory-toast.service
```

## Configure the toast

Edit `~/.config/forgetmenot/memory-toast.json`, then run:

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

To preview the current settings for 20 seconds:

```sh
python3 "$HOME/.local/lib/forgetmenot/toast.py" --preview
```

## Context

See [CONTEXT-MAP.md](CONTEXT-MAP.md) for terminology and source anchors.
