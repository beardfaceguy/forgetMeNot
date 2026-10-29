# Isolated Zed launches

Date: 2026-10-28.

## Purpose

Keep independent Zed editor instances outside the COSMIC desktop-session cgroup.
Each launch receives a separate delegated systemd user scope.
Delegation lets the local Zed fork place helper cgroups beneath its application scope.
The source is `launcher.py`. The installer and rollback entry point are in `install.py`.

## Prerequisites

- Linux with systemd user scopes and Python 3.9 or later.
- The inspected Zed development bundle installed under `~/.local/zed-dev.app/`.
- The original `~/.local/bin/zed` symlink and the development desktop entry.
- A graphical session for editor launches.

Stable Zed builds can reuse an existing editor or reject an independent launch.
The launcher rejects those builds rather than silently losing isolation.
It also rejects `--zed` overrides. The inspected development build keeps existing profiles and settings.

## Install

1. Run the unit tests from the repository root:

   ```sh
   python3 -m unittest discover -s zed-scope -v
   ```

2. Install the launcher and route future terminal and desktop launches through it:

   ```sh
   python3 zed-scope/install.py
   update-desktop-database ~/.local/share/applications
   ```

The installer saves the original terminal symlink and desktop entry under `~/.local/state/forgetmenot/zed-launch-backup/`.
It preserves that first backup during later installations.
It does not move, restart, or stop existing editors.
A Zed bundle update can replace the desktop entry or terminal symlink. Inspect those paths after updates and reinstall when necessary.

## Usage and inspection

Use the usual terminal command or desktop entry:

```sh
zed --new /path/to/project
```

Use `zed-isolated` to select the isolated launcher explicitly.
Normal launches return after the scope becomes active.
Explicit `--wait` and `--foreground` launches remain attached to the caller.
Help, version, and completion requests use the original CLI without an application scope.

Inspect active application scopes:

```sh
systemctl --user list-units 'app-forgetmenot-zed-*.scope'
```

Scope startup does not prove that an editor window finished opening.
Inspect its process membership and private startup log when a window does not appear.
Detached startup logs live under `~/.local/state/forgetmenot/zed-scopes/`.
The launcher does not rotate or remove those logs.
It reports startup failures and never retries outside a scope.

## Temporary memory budgets

`scope_command` in `launcher.py` defines the approved per-instance soft RAM threshold, hard RAM ceiling, and swap ceiling.
The scope includes the editor and its contained helper groups.
These temporary budgets provide headroom above a short workload sample. They are not proven peak requirements.
File-backed cache contributes to cgroup RAM accounting. It is not equivalent to application heap usage.

New launches receive all three settings from the launcher.
Changing the source requires tests and reinstallation before future launches use the changed policy.
Existing scopes require a separate staged update. Apply the soft threshold first and observe reclamation before imposing hard ceilings.
Do not lower a hard ceiling below current usage without a separate safety assessment.

Inspect effective limits:

```sh
systemctl --user show UNIT -p MemoryHigh -p MemoryMax -p MemorySwapMax
```

A hard-limit event can kill an editor or helper without saving work.
Individual limits do not reserve capacity for COSMIC or establish a shared ceiling across all editors.
The global warning toast and system-wide OOM policy remain separate.

## Bounded helper probe

Run the containment probe in a disposable delegated scope:

```sh
systemd-run --user --scope --collect --slice=app.slice \
  --unit=app-forgetmenot-probe-helpers \
  --property=MemoryAccounting=yes --property=Delegate=yes \
  python3 zed-scope/probe_cgroup.py
```

The probe verifies inherited and nested cgroup membership with a small sleep process.
It terminates only that probe process. It never targets an editor or triggers memory exhaustion.

## Boundaries

Windows within one editor process share its scope.
New independent launches receive separate scopes but share the existing Zed profile unless CLI arguments select another profile.
Ordinary descendants inherit the scope. The local fork can create nested helper cgroups through delegation.
A helper that explicitly starts another systemd unit needs separate containment verification.

This launcher applies the temporary user-approved budgets defined by `scope_command`.
It does not change system-wide OOM policy or prevent every combined memory-exhaustion event.
Direct use of the bundle's original CLI bypasses this launcher.

## Rollback

Clear the three memory settings on an existing scope without stopping it:

```sh
systemctl --user set-property --runtime UNIT \
  MemoryHigh=infinity MemoryMax=infinity MemorySwapMax=infinity
```

On this laptop, the pre-budget isolated wrapper is retained at `~/.local/state/forgetmenot/zed-launch-backup/zed-isolated-before-budgets.py`.
Restoring that file to `~/.local/bin/zed-isolated` preserves isolation but removes the new budgets from future launches.
The repository source still defines the approved budgets. Reinstallation reapplies them.

Alternatively, restore the original terminal symlink and desktop entry:

```sh
python3 zed-scope/install.py --restore
update-desktop-database ~/.local/share/applications
```

Rollback restores the pre-install desktop entry, including its original metadata.
Preserve any later manual edits before restoring that backup.
Rollback does not stop existing scopes or move their processes.
The explicit `zed-isolated` command and its logs remain available.
