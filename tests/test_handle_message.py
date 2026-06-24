"""Tests for handle_message method covering all flow steps."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from unittest.mock import patch, MagicMock

with patch('os.makedirs'), patch('builtins.print'):
    from Sayt_saz_simorgh import SiteBuilderBot


class TestHandleMessageStart:
    """Tests for /start command handling."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200

    def test_start_command_sends_welcome(self):
        msg = {"text": "/start"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        self.bot.send_message.assert_called_once()
        args = self.bot.send_message.call_args[0]
        assert args[0] == self.chat_id
        assert "سلام" in args[1]

    def test_no_state_sends_start_prompt(self):
        msg = {"text": "random text"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        self.bot.send_message.assert_called_once()
        args = self.bot.send_message.call_args[0]
        assert "شروع" in args[1] or "ساخت" in args[1]


class TestHandleMessageCustomerInfo:
    """Tests for customer_info step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "customer_info",
            "data": {"customer_info": {}}
        }

    def test_valid_customer_info_transitions_to_name(self):
        msg = {"text": "علی محمدی 1234567890 09121234567"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "name"

    def test_empty_text_stays_on_customer_info(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "customer_info"

    def test_customer_info_stored_in_data(self):
        msg = {"text": "علی محمدی\n1234567890\n09121234567"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        data = self.bot.user_states[self.user_id]["data"]
        assert data["customer_info"]["name"] == "علی محمدی"
        assert data["customer_info"]["national_code"] == "1234567890"
        assert data["customer_info"]["phone"] == "09121234567"


class TestHandleMessageName:
    """Tests for name step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "name",
            "data": {"site_name": ""}
        }

    def test_valid_name_transitions_to_color(self):
        msg = {"text": "فروشگاه من"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "color"
        assert self.bot.user_states[self.user_id]["data"]["site_name"] == "فروشگاه من"

    def test_empty_name_stays_on_name(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "name"


class TestHandleMessageColor:
    """Tests for color step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "color",
            "data": {}
        }

    def test_valid_color_transitions_to_home(self):
        msg = {"text": "آبی"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "home"
        assert self.bot.user_states[self.user_id]["data"]["color"] == "#007bff"

    def test_unknown_color_uses_default(self):
        msg = {"text": "نامشخص"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "home"
        assert self.bot.user_states[self.user_id]["data"]["color"] == "#0095ff"

    def test_empty_color_stays_on_color(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "color"


class TestHandleMessageHome:
    """Tests for home step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "home",
            "data": {"description_list": []}
        }

    def test_valid_home_text_transitions_to_about(self):
        msg = {"text": "خط اول\nخط دوم"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "about"
        assert self.bot.user_states[self.user_id]["data"]["description_list"] == ["خط اول", "خط دوم"]

    def test_empty_home_stays(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "home"


class TestHandleMessageAbout:
    """Tests for about step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "about",
            "data": {"about_list": [], "sections": []}
        }

    def test_valid_about_text_transitions_to_services(self):
        msg = {"text": "درباره ما"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "services"
        assert "about" in self.bot.user_states[self.user_id]["data"]["sections"]
        assert self.bot.user_states[self.user_id]["data"]["about_list"] == ["درباره ما"]

    def test_empty_about_still_transitions(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "services"


class TestHandleMessageServices:
    """Tests for services step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "services",
            "data": {"services_list": [], "sections": []}
        }

    def test_valid_services_transitions_to_orders(self):
        msg = {"text": "خدمات ما\nخدمت ۲"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "orders"
        assert "services" in self.bot.user_states[self.user_id]["data"]["sections"]

    def test_empty_services_still_transitions(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "orders"


class TestHandleMessageOrders:
    """Tests for orders step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "orders",
            "data": {"orders_list": [], "sections": []}
        }

    def test_valid_orders_transitions_to_logo(self):
        msg = {"text": "سفارش ۱"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "logo"
        assert "orders" in self.bot.user_states[self.user_id]["data"]["sections"]


class TestHandleMessageLogo:
    """Tests for logo step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "logo",
            "data": {"logo_url": ""}
        }

    def test_valid_url_transitions_to_contact(self):
        msg = {"text": "https://example.com/logo.png"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "contact"
        assert self.bot.user_states[self.user_id]["data"]["logo_url"] == "https://example.com/logo.png"

    def test_invalid_url_stays_on_logo(self):
        msg = {"text": "not a url"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "logo"

    def test_empty_text_stays_on_logo(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "logo"


class TestHandleMessageContact:
    """Tests for contact step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "contact",
            "data": {"sections": [], "contact_text": ""}
        }

    def test_valid_contact_transitions_to_domain(self):
        msg = {"text": "09121234567 test@mail.com"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "domain"
        assert "contact" in self.bot.user_states[self.user_id]["data"]["sections"]

    def test_empty_contact_still_transitions(self):
        msg = {"text": ""}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "domain"


class TestHandleMessageDomain:
    """Tests for domain step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "domain",
            "data": {"domain": ""}
        }

    def test_valid_domain_transitions_to_hosting_plan(self):
        msg = {"text": "mysite.com"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "hosting_plan"
        assert self.bot.user_states[self.user_id]["data"]["domain"] == "mysite.com"

    def test_skip_domain_transitions(self):
        msg = {"text": "رد کردن"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "hosting_plan"
        assert self.bot.user_states[self.user_id]["data"]["domain"] == ""

    def test_invalid_domain_stays(self):
        msg = {"text": "nodot"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "domain"


class TestHandleMessageHostingPlan:
    """Tests for hosting_plan step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "hosting_plan",
            "data": {"hosting_plan": ""}
        }

    def test_basic_plan_selected(self):
        msg = {"text": "۱"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "payment"
        assert self.bot.user_states[self.user_id]["data"]["hosting_plan"] == "basic"

    def test_standard_plan_selected(self):
        msg = {"text": "استاندارد"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "payment"
        assert self.bot.user_states[self.user_id]["data"]["hosting_plan"] == "standard"

    def test_pro_plan_selected(self):
        msg = {"text": "حرفه‌ای"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "payment"
        assert self.bot.user_states[self.user_id]["data"]["hosting_plan"] == "pro"

    def test_skip_hosting_defaults_to_basic(self):
        msg = {"text": "رد کردن"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "payment"
        assert self.bot.user_states[self.user_id]["data"]["hosting_plan"] == "basic"

    def test_unknown_plan_defaults_to_basic(self):
        msg = {"text": "چیز عجیب"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["step"] == "payment"
        assert self.bot.user_states[self.user_id]["data"]["hosting_plan"] == "basic"


class TestHandleMessagePayment:
    """Tests for payment step."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.bot.finish_site = MagicMock()
        self.chat_id = 100
        self.user_id = 200
        self.bot.user_states[self.user_id] = {
            "step": "payment",
            "data": {"payment_status": False}
        }

    def test_test_payment_calls_finish(self):
        msg = {"text": "تست"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        assert self.bot.user_states[self.user_id]["data"]["payment_status"] is True
        self.bot.finish_site.assert_called_once()

    def test_skip_payment_calls_finish(self):
        msg = {"text": "رد کردن"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        self.bot.finish_site.assert_called_once()

    def test_tracking_code_calls_finish(self):
        msg = {"text": "123456789"}
        self.bot.handle_message(self.chat_id, self.user_id, msg)
        self.bot.finish_site.assert_called_once()
