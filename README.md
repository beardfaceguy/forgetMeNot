# forgetMeNot

Personal Linux tools and setup instructions that survive an OS reinstall.

## Memory monitor

The [memory monitor](memory-monitor/README.md) records RAM, swap, processes, and application trees in a local Markdown file.
It runs as a systemd user service, separately from the desktop session group.

The current tool records evidence. It does not kill applications or change the system OOM policy.
The proposed 85% memory warning and live notification are not implemented yet.

## Install after an OS reinstall

Requirements: Linux, Python 3.9 or later, Git, and a systemd user manager.
Run these commands from the repository root:

```sh
install -Dm755 memory-monitor/monitor.py "$HOME/.local/lib/forgetmenot/memory-monitor.py"
install -Dm644 memory-monitor/cosmic-memory-monitor.service "$HOME/.config/systemd/user/cosmic-memory-monitor.service"
systemctl --user daemon-reload
systemctl --user enable cosmic-memory-monitor.service
systemctl --user restart cosmic-memory-monitor.service
```

The commands install or replace the memory-monitor user service.
The service writes snapshots to `~/.local/state/forgetmenot/memory-samples.md`.

Verify it:

```sh
systemctl --user status cosmic-memory-monitor.service
tail -n 25 "$HOME/.local/state/forgetmenot/memory-samples.md"
```

## Test without installing

```sh
python3 -m unittest discover -s memory-monitor -p 'test_*.py' -v
python3 memory-monitor/monitor.py --once --output /tmp/forgetmenot-memory-sample.md
```

## Update an installed copy

Run `git pull --ff-only`, then repeat the installation commands.

## Stop the monitor

```sh
systemctl --user disable --now cosmic-memory-monitor.service
```

## Context

See [CONTEXT-MAP.md](CONTEXT-MAP.md) for terminology and source anchors.
