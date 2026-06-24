"""Tests for the map_color utility function."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch ssl and suppress module-level side effects before import
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from unittest.mock import patch

with patch('os.makedirs'), patch('builtins.print'):
    from Sayt_saz_simorgh import map_color, COLOR_MAP


class TestMapColor:
    """Tests for color mapping function."""

    def test_known_color_blue(self):
        assert map_color("آبی") == "#007bff"

    def test_known_color_red(self):
        assert map_color("قرمز") == "#dc3545"

    def test_known_color_green(self):
        assert map_color("سبز") == "#28a745"

    def test_known_color_yellow(self):
        assert map_color("زرد") == "#ffc107"

    def test_known_color_orange(self):
        assert map_color("نارنجی") == "#fd7e14"

    def test_known_color_purple(self):
        assert map_color("بنفش") == "#6f42c1"

    def test_known_color_pink(self):
        assert map_color("صورتی") == "#e83e8c"

    def test_known_color_teal(self):
        assert map_color("فیروزه‌ای") == "#20c997"

    def test_known_color_black(self):
        assert map_color("مشکی") == "#000000"

    def test_known_color_gray(self):
        assert map_color("خاکستری") == "#6c754d"

    def test_known_color_white(self):
        assert map_color("سفید") == "#ffffff"

    def test_known_color_brown(self):
        assert map_color("قهوه‌ای") == "#795548"

    def test_unknown_color_returns_default(self):
        assert map_color("طلایی") == "#0095ff"

    def test_empty_string_returns_default(self):
        assert map_color("") == "#0095ff"

    def test_whitespace_handling(self):
        assert map_color("  آبی  ") == "#007bff"

    def test_color_map_has_expected_keys(self):
        expected_keys = {"آبی", "قرمز", "سبز", "زرد", "نارنجی", "بنفش",
                         "صورتی", "فیروزه‌ای", "مشکی", "خاکستری", "سفید", "قهوه‌ای"}
        assert set(COLOR_MAP.keys()) == expected_keys
