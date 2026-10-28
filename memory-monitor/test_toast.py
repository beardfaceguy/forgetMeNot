import tempfile
import unittest
from pathlib import Path

from toast import ToastSettings, WarningState, load_settings, toast_position


class WarningTests(unittest.TestCase):
    def test_invalid_hex_color_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "#RRGGBB"):
            ToastSettings(background="#nothex")

    def test_default_colors_match_the_requested_palette(self):
        settings = ToastSettings()
        self.assertEqual((settings.background, settings.foreground), ("#FCEE0A", "#000000"))

    def test_custom_hex_pair_is_accepted_from_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "toast.json"
            config.write_text('{"background": "#FCEE0A", "foreground": "#02D7F2"}')
            settings = load_settings(config)
        self.assertEqual((settings.background, settings.foreground), ("#FCEE0A", "#02D7F2"))

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
