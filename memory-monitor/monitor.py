#!/usr/bin/env python3
"""Record local process memory evidence without command arguments or environments.

Context: ../CONTEXT.md.
"""

import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import time


APPLICATION_NAMES = {
    "zed-editor": "Zed", "steam": "Steam", "Outbound": "Outbound", "Outbound.exe": "Outbound",
    "chrome": "Chrome", "chromium": "Chromium", "firefox": "Firefox", "slack": "Slack",
    "cosmic-comp": "COSMIC", "cosmic-files": "Files",
}


def read_fields(path):
    fields = {}
    for line in path.read_text().splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value.strip()
    return fields


def kib(fields, key):
    return int(fields.get(key, "0").split()[0])


def application_owner(process, by_pid, roots):
    ancestor_pid = process[1]
    visited = set()
    while ancestor_pid in by_pid and ancestor_pid not in visited:
        visited.add(ancestor_pid)
        ancestor = by_pid[ancestor_pid]
        if ancestor[3] in roots:
            return ancestor_pid, ancestor[3]
        ancestor_pid = int(ancestor[2])
    return None


def application_tree_totals(processes):
    """Attribute each process to its nearest visible editor, Steam, or game ancestor."""
    by_pid = {process[1]: process for process in processes}
    roots = {"zed-editor", "steam", "Outbound", "Outbound.exe"}
    grouped = {}
    for process in processes:
        owner = application_owner(process, by_pid, roots)
        if owner is not None:
            counters = grouped.setdefault(owner, [0, 0, 0])
            counters[0] += 1
            counters[1] += process[4]
            counters[2] += process[5]
    return grouped


def top_applications(processes, limit=3):
    by_pid = {process[1]: process for process in processes}
    totals = defaultdict(int)
    for process in processes:
        owner = application_owner(process, by_pid, APPLICATION_NAMES)
        name = APPLICATION_NAMES[owner[1]] if owner else process[3]
        totals[name] += process[4]
    return sorted(totals.items(), key=lambda application: application[1], reverse=True)[:limit]


def collect_processes():
    processes = []
    for process_path in Path("/proc").iterdir():
        if not process_path.name.isdigit():
            continue
        try:
            fields = read_fields(process_path / "status")
            name = fields["Name"].replace("|", "/").replace("`", "'")
            resident = kib(fields, "VmRSS")
            swapped = kib(fields, "VmSwap")
            cgroup = (process_path / "cgroup").read_text().strip().splitlines()[0]
            processes.append((resident + swapped, int(process_path.name), fields["PPid"], name, resident, swapped, cgroup))
        except (OSError, KeyError, ValueError, IndexError):
            # Processes can exit between reads. Inaccessible processes are omitted.
            continue
    return processes


def snapshot():
    memory = read_fields(Path("/proc/meminfo"))
    processes = collect_processes()
    totals = defaultdict(lambda: [0, 0, 0])
    for process in processes:
        totals[process[3]][0] += 1
        totals[process[3]][1] += process[4]
        totals[process[3]][2] += process[5]
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [f"\n## {timestamp}\n"]
    lines.append(f"RAM available: {kib(memory, 'MemAvailable') / 1024:.0f} MiB / {kib(memory, 'MemTotal') / 1024:.0f} MiB.")
    swap_used = kib(memory, "SwapTotal") - kib(memory, "SwapFree")
    lines.append(f"Swap used: {swap_used / 1024:.0f} MiB / {kib(memory, 'SwapTotal') / 1024:.0f} MiB.")
    lines.append(f"Processes sampled: {len(processes)}. Boot ID: {Path('/proc/sys/kernel/random/boot_id').read_text().strip()}.")
    lines.extend(["", "Top processes by RSS plus swap:", "", "| PID | Parent | Name | RSS MiB | Swap MiB | Cgroup |", "|---|---|---|---|---|---|"])
    for _, pid, parent, name, resident, swapped, cgroup in sorted(processes, reverse=True)[:15]:
        lines.append(f"| {pid} | {parent} | {name} | {resident / 1024:.1f} | {swapped / 1024:.1f} | `{cgroup.replace('|', '/')}` |")
    lines.extend(["", "Totals by process name:", "", "| Name | Count | RSS MiB | Swap MiB |", "|---|---|---|---|"])
    for name, (count, resident, swapped) in sorted(totals.items(), key=lambda item: item[1][1] + item[1][2], reverse=True)[:10]:
        lines.append(f"| {name} | {count} | {resident / 1024:.1f} | {swapped / 1024:.1f} |")
    lines.extend(["", "Application trees by visible parent links:", "", "| Root PID | Application | Processes | RSS MiB | Swap MiB |", "|---|---|---|---|---|"])
    trees = application_tree_totals(processes)
    for (pid, name), (count, resident, swapped) in sorted(trees.items(), key=lambda item: item[1][1] + item[1][2], reverse=True):
        lines.append(f"| {pid} | {name} | {count} | {resident / 1024:.1f} | {swapped / 1024:.1f} |")
    lines.append("Orphaned helpers cannot be attributed from parent links. Nested application roots have separate totals.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--interval", default=30, type=float)
    parser.add_argument("--once", action="store_true")
    options = parser.parse_args()
    if options.interval < 5:
        parser.error("The interval must be at least five seconds.")
    options.output.parent.mkdir(parents=True, exist_ok=True)
    with options.output.open("a", buffering=1) as report:
        if options.output.stat().st_size == 0:
            report.write("# Local memory snapshots\n\nRSS includes shared pages. Aggregated RSS is not unique physical memory.\n")
            report.write("Snapshots omit command arguments and environment variables. Process reads are not atomic.\n")
        while True:
            if options.output.stat().st_size >= 64 * 1024 * 1024:
                report.write("\nMonitor stopped at the 64 MiB report limit. Restart with a new output path.\n")
                break
            report.write(snapshot())
            report.flush()
            if options.once:
                break
            time.sleep(options.interval)


if __name__ == "__main__":
    main()
