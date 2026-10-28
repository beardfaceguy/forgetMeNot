#!/usr/bin/env python3
"""Show a configurable memory warning. Context: ../CONTEXT.md."""

import argparse
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import sys

from monitor import collect_processes, kib, read_fields, top_applications


POSITIONS = {"top-right", "top-left", "bottom-right", "bottom-left"}


def contrast_ratio(background, foreground):
    def luminance(color):
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    first, second = sorted((luminance(background), luminance(foreground)))
    return (second + 0.05) / (first + 0.05)


@dataclass
class ToastSettings:
    warning_percent: float = 85
    clear_percent: float = 80
    refresh_seconds: float = 2
    position: str = "top-right"
    monitor: object = "primary"
    margin: int = 24
    background: str = "#FCEE0A"
    foreground: str = "#000000"

    def __post_init__(self):
        if self.position not in POSITIONS:
            raise ValueError("position must be top-right, top-left, bottom-right, or bottom-left")
        numbers = (self.warning_percent, self.clear_percent, self.refresh_seconds)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in numbers):
            raise ValueError("thresholds and refresh_seconds must be finite numbers")
        if not 0 <= self.clear_percent < self.warning_percent <= 100:
            raise ValueError("thresholds must satisfy 0 <= clear_percent < warning_percent <= 100")
        if not 0.5 <= self.refresh_seconds <= 60:
            raise ValueError("refresh_seconds must be between 0.5 and 60")
        if type(self.margin) is not int or not 0 <= self.margin <= 200:
            raise ValueError("margin must be an integer between 0 and 200")
        if self.monitor != "primary" and (type(self.monitor) is not int or self.monitor < 0):
            raise ValueError("monitor must be primary or a nonnegative monitor index")
        for color in (self.background, self.foreground):
            if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError("colors must use #RRGGBB format")


def load_settings(path):
    if not path.exists():
        return ToastSettings()
    return ToastSettings(**json.loads(path.read_text()))


def toast_position(position, workarea, size, margin):
    left, top, width, height = workarea
    window_width, window_height = size
    right = max(left, left + width - window_width - margin)
    bottom = max(top, top + height - window_height - margin)
    x = right if position.endswith("right") else min(left + margin, right)
    y = bottom if position.startswith("bottom") else min(top + margin, bottom)
    return x, y


@dataclass
class WarningState:
    warning_percent: float = 85
    clear_percent: float = 80
    visible: bool = False
    dismissed: bool = False

    def update(self, percent):
        if percent < self.clear_percent:
            self.visible = False
            self.dismissed = False
        elif percent >= self.warning_percent and not self.dismissed:
            self.visible = True
        return self.visible

    def dismiss(self):
        self.visible = False
        self.dismissed = True


def run_toast(settings, preview_seconds=0):
    # PyGObject initializes GTK during import, so select Xwayland before importing it.
    os.environ["GDK_BACKEND"] = "x11"
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk

    initialized, _ = Gtk.init_check([])
    if not initialized:
        raise RuntimeError("The toast needs an X11 or Xwayland display and a graphical login session")

    state = WarningState(settings.warning_percent, settings.clear_percent)
    window = Gtk.Window(type=Gtk.WindowType.POPUP)
    window.set_title("forgetMeNot Memory")
    window.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
    window.set_accept_focus(False)
    window.set_focus_on_map(False)
    window.set_resizable(False)
    window.set_name("memory-toast")
    css = Gtk.CssProvider()
    css.load_from_data(f"""
        #memory-toast, #memory-toast * {{ color: {settings.foreground}; }}
        #memory-toast {{ background: {settings.background}; border: 3px solid {settings.foreground}; border-radius: 12px; }}
        #memory-toast .heading {{ font-weight: 800; font-size: 14px; letter-spacing: 1px; }}
        #memory-toast .percentage {{ font-weight: 900; font-size: 46px; }}
        #memory-toast .details {{ font-size: 13px; }}
        #memory-toast button {{ background: transparent; border: none; box-shadow: none; padding: 2px 7px; }}
        #memory-toast progressbar trough {{ background: alpha({settings.foreground}, 0.15); border: none; min-height: 9px; }}
        #memory-toast progressbar progress {{ background: {settings.foreground}; border: none; min-height: 9px; }}
    """.encode())
    Gtk.StyleContext.add_provider_for_screen(window.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    content.set_border_width(18)
    content.set_size_request(360, -1)
    window.add(content)
    header = Gtk.Box(spacing=12)
    content.pack_start(header, False, False, 0)
    title = Gtk.Label(label="MEMORY MONITOR · PREVIEW" if preview_seconds else "MEMORY WARNING")
    title.set_xalign(0)
    title.get_style_context().add_class("heading")
    header.pack_start(title, True, True, 0)
    close = Gtk.Button(label="×")
    close.set_tooltip_text("Dismiss until memory recovers")
    header.pack_end(close, False, False, 0)
    percentage = Gtk.Label(xalign=0)
    percentage.get_style_context().add_class("percentage")
    content.pack_start(percentage, False, False, 0)
    progress = Gtk.ProgressBar()
    content.pack_start(progress, False, False, 0)
    details = Gtk.Label(xalign=0)
    details.get_style_context().add_class("details")
    content.pack_start(details, False, False, 0)
    apps_heading = Gtk.Label(label="TOP APPLICATIONS · APPROXIMATE RAM", xalign=0)
    apps_heading.get_style_context().add_class("details")
    content.pack_start(apps_heading, False, False, 0)
    applications = Gtk.Grid(column_spacing=24, row_spacing=4)
    app_labels = []
    for row in range(3):
        name = Gtk.Label(xalign=0)
        name.set_hexpand(True)
        amount = Gtk.Label(xalign=1)
        applications.attach(name, 0, row, 1, 1)
        applications.attach(amount, 1, row, 1, 1)
        app_labels.append((name, amount))
    content.pack_start(applications, False, False, 0)
    preview_position = None

    def place(*_):
        nonlocal preview_position
        display = window.get_display()
        if settings.monitor == "primary":
            monitor = display.get_primary_monitor() or display.get_monitor(0)
        else:
            monitor = display.get_monitor(settings.monitor)
        if monitor is None:
            raise RuntimeError("The configured monitor does not exist")
        area = monitor.get_workarea()
        size = window.get_size()
        x, y = toast_position(settings.position, (area.x, area.y, area.width, area.height), size, settings.margin)
        window.move(x, y)
        if preview_seconds and window.get_visible() and preview_position != (x, y):
            preview_position = (x, y)
            print(f"Toast preview: {settings.position}, requested=({x}, {y}), actual={tuple(window.get_position())}, size={tuple(size)}", flush=True)

    def refresh():
        memory = read_fields(Path("/proc/meminfo"))
        total = kib(memory, "MemTotal")
        used = total - kib(memory, "MemAvailable")
        percent = 100 * used / total
        if preview_seconds or state.update(percent):
            percentage.set_text(f"{percent:.1f}% RAM")
            progress.set_fraction(percent / 100)
            swap_used = kib(memory, "SwapTotal") - kib(memory, "SwapFree")
            details.set_text(f"{used / 1048576:.1f} / {total / 1048576:.1f} GiB used   ·   Swap {swap_used / 1048576:.1f} GiB")
            leaders = top_applications(collect_processes())
            for row, (name_label, amount_label) in enumerate(app_labels):
                if row < len(leaders):
                    name, resident = leaders[row]
                    name_label.set_text(name)
                    amount_label.set_text(f"{resident / 1048576:.1f} GiB")
                else:
                    name_label.set_text("")
                    amount_label.set_text("")
            window.show_all()
            place()
        else:
            window.hide()
        return GLib.SOURCE_CONTINUE

    def dismiss(*_):
        state.dismiss()
        window.hide()
        if preview_seconds:
            Gtk.main_quit()

    close.connect("clicked", dismiss)
    window.connect("size-allocate", place)
    window.connect("destroy", lambda *_: Gtk.main_quit())
    refresh()
    GLib.timeout_add(int(settings.refresh_seconds * 1000), refresh)
    if preview_seconds:
        def finish_preview():
            Gtk.main_quit()
            return GLib.SOURCE_REMOVE

        GLib.timeout_add_seconds(preview_seconds, finish_preview)
    Gtk.main()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/forgetmenot/memory-toast.json")
    parser.add_argument("--preview", action="store_true", help="Show actual live usage for 20 seconds at any memory level")
    options = parser.parse_args()
    try:
        settings = load_settings(options.config)
        contrast = contrast_ratio(settings.background, settings.foreground)
        if contrast < 4.5:
            print(f"Memory toast: text contrast is {contrast:.1f}:1; using the configured colors.", file=sys.stderr)
        run_toast(settings, preview_seconds=20 if options.preview else 0)
    except (OSError, ValueError, TypeError, ImportError, RuntimeError) as error:
        parser.exit(1, f"Memory toast: {error}\n")


if __name__ == "__main__":
    main()
