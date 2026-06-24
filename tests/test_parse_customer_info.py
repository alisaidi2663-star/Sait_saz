"""Tests for parse_customer_info method."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from unittest.mock import patch

with patch('os.makedirs'), patch('builtins.print'):
    from Sayt_saz_simorgh import SiteBuilderBot


class TestParseCustomerInfo:
    """Tests for customer info parsing logic."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()

    def test_single_line_with_all_info(self):
        text = "علی محمدی 1234567890 09121234567"
        result = self.bot.parse_customer_info(text)
        assert result["national_code"] == "1234567890"
        assert result["phone"] == "09121234567"
        assert "علی" in result["name"] or "محمدی" in result["name"]

    def test_multiline_input(self):
        text = "علی محمدی\n1234567890\n09121234567"
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["national_code"] == "1234567890"
        assert result["phone"] == "09121234567"

    def test_multiline_phone_before_national_code(self):
        text = "علی محمدی\n09121234567\n1234567890"
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["phone"] == "09121234567"
        assert result["national_code"] == "1234567890"

    def test_name_only(self):
        text = "علی محمدی"
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["national_code"] == ""
        assert result["phone"] == ""

    def test_name_with_national_code_only(self):
        text = "علی محمدی\n1234567890"
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["national_code"] == "1234567890"

    def test_name_with_phone_only_multiline(self):
        text = "علی محمدی\n09121234567"
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["phone"] == "09121234567"

    def test_single_line_name_and_national_code(self):
        text = "علی محمدی 1234567890"
        result = self.bot.parse_customer_info(text)
        assert result["national_code"] == "1234567890"
        assert "علی" in result["name"]

    def test_single_line_name_and_phone(self):
        text = "علی محمدی 09121234567"
        result = self.bot.parse_customer_info(text)
        assert result["phone"] == "09121234567"
        assert "علی" in result["name"]

    def test_empty_lines_are_ignored(self):
        text = "علی محمدی\n\n1234567890\n\n09121234567"
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["national_code"] == "1234567890"
        assert result["phone"] == "09121234567"

    def test_whitespace_trimmed(self):
        text = "  علی محمدی  \n  1234567890  \n  09121234567  "
        result = self.bot.parse_customer_info(text)
        assert result["name"] == "علی محمدی"
        assert result["national_code"] == "1234567890"
        assert result["phone"] == "09121234567"

    def test_national_code_fallback_assigns_without_validation(self):
        text = "علی\n12345\n09121234567"
        result = self.bot.parse_customer_info(text)
        # In multiline fallback, non-matching lines[1] is assigned as national_code
        assert result["national_code"] == "12345"
        assert result["phone"] == "09121234567"

    def test_phone_fallback_assigns_without_validation(self):
        text = "علی\n1234567890\n08121234567"
        result = self.bot.parse_customer_info(text)
        # In multiline fallback, non-matching lines[2] is assigned as phone
        assert result["national_code"] == "1234567890"
        assert result["phone"] == "08121234567"

    def test_result_keys_exist(self):
        text = "test"
        result = self.bot.parse_customer_info(text)
        assert "name" in result
        assert "national_code" in result
        assert "phone" in result
