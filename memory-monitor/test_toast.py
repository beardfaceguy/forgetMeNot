import tempfile
import unittest
from pathlib import Path

from toast import ToastSettings, WarningState, load_settings, toast_position


class WarningTests(unittest.TestCase):
    def test_unreadable_color_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contrast"):
            ToastSettings(background="#111111", foreground="#121212")

    def test_warning_persists_until_recovery_and_dismissal_rearms_after_recovery(self):
        warning = WarningState(warning_percent=85, clear_percent=80)
        self.assertFalse(warning.update(84))
        self.assertTrue(warning.update(85))
        self.assertTrue(warning.update(82))
        warning.dismiss()
        self.assertFalse(warning.update(90))
        self.assertFalse(warning.update(79))
        self.assertTrue(warning.update(86))

    def test_configured_corner_and_margin_use_the_selected_monitor_workarea(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "toast.json"
            config.write_text('{"position": "bottom-left", "margin": 36}')
            settings = load_settings(config)
        self.assertEqual(
            toast_position(settings.position, (100, 50, 1600, 900), (360, 200), settings.margin),
            (136, 714),
        )


if __name__ == "__main__":
    unittest.main()
