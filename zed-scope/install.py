#!/usr/bin/env python3
"""Install the Zed scope launcher without changing active editor processes.

Context: ../CONTEXT.md, isolated Zed launch. No local ADR governs this installer.
"""
import argparse
import os
import shutil
import sys
import uuid
from pathlib import Path


def install(home: Path) -> None:
    cli = home / ".local/zed-dev.app/bin/zed"
    link = home / ".local/bin/zed"
    wrapper = home / ".local/bin/zed-isolated"
    desktop = home / ".local/share/applications/dev.zed.Zed-Dev.desktop"
    backup = home / ".local/state/forgetmenot/zed-launch-backup"
    if not cli.is_file() or not link.is_symlink() or link.resolve() not in (cli.resolve(), wrapper):
        raise ValueError("The installed Zed launcher does not match the inspected development bundle")
    original = desktop.read_text()
    commands = [line for line in original.splitlines() if line.startswith(("Exec=", "TryExec="))]
    if not commands or any(
        not any(line.split("=", 1)[1].split(" ", 1)[0] == str(path) for path in (cli, wrapper))
        for line in commands
    ):
        raise ValueError("The desktop commands differ from the inspected launcher")
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    saved_link = backup / "zed"
    if not saved_link.is_symlink() and not saved_link.exists():
        if link.resolve() == wrapper:
            raise ValueError("The original launcher backup is missing")
        saved_link.symlink_to(link.readlink())
    if not (backup / desktop.name).exists():
        shutil.copy2(desktop, backup / desktop.name)
    shutil.copyfile(Path(__file__).with_name("launcher.py"), wrapper)
    wrapper.chmod(0o755)
    replacement = link.with_name(f".zed-isolated-{uuid.uuid4().hex}")
    replacement.symlink_to(wrapper.name)
    os.replace(replacement, link)
    desktop.write_text(original.replace(str(cli), str(wrapper)))


def restore(home: Path) -> None:
    backup = home / ".local/state/forgetmenot/zed-launch-backup"
    desktop = home / ".local/share/applications/dev.zed.Zed-Dev.desktop"
    original = backup / "zed"
    if not original.is_symlink() or not (backup / desktop.name).is_file():
        raise ValueError("The original launcher or desktop backup is missing")
    link = home / ".local/bin/zed"
    replacement = link.with_name(f".zed-restore-{uuid.uuid4().hex}")
    replacement.symlink_to(original.readlink())
    os.replace(replacement, link)
    shutil.copy2(backup / desktop.name, desktop)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore the saved terminal launcher and desktop entry")
    arguments = parser.parse_args()
    try:
        if arguments.restore:
            restore(Path.home())
        else:
            install(Path.home())
    except (OSError, ValueError) as error:
        print(f"Zed isolation installation failed: {error}", file=sys.stderr)
        return 1
    print("Restored the saved Zed launch paths" if arguments.restore else "Installed Zed isolation for future terminal and desktop launches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
