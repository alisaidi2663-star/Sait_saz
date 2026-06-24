"""Tests for handle_callback method and state transitions."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from unittest.mock import patch, MagicMock

with patch('os.makedirs'), patch('builtins.print'):
    from Sayt_saz_simorgh import SiteBuilderBot


class TestHandleCallback:
    """Tests for callback handling and state transitions."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()
        self.bot.finish_site = MagicMock()
        self.chat_id = 12345
        self.user_id = 67890

    def test_newsite_callback_starts_flow(self):
        self.bot.handle_callback(self.chat_id, self.user_id, "newsite")
        assert self.user_id in self.bot.user_states
        assert self.bot.user_states[self.user_id]["step"] == "customer_info"

    def test_skip_home_transitions_to_name(self):
        self.bot.user_states[self.user_id] = {"step": "home", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_home")
        assert self.bot.user_states[self.user_id]["step"] == "name"

    def test_skip_about_transitions_to_about(self):
        self.bot.user_states[self.user_id] = {"step": "about", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_about")
        assert self.bot.user_states[self.user_id]["step"] == "about"

    def test_skip_services_transitions_to_services(self):
        self.bot.user_states[self.user_id] = {"step": "services", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_services")
        assert self.bot.user_states[self.user_id]["step"] == "services"

    def test_skip_orders_transitions_to_orders(self):
        self.bot.user_states[self.user_id] = {"step": "orders", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_orders")
        assert self.bot.user_states[self.user_id]["step"] == "orders"

    def test_skip_logo_transitions_to_contact(self):
        self.bot.user_states[self.user_id] = {"step": "logo", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_logo")
        assert self.bot.user_states[self.user_id]["step"] == "contact"

    def test_skip_contact_calls_finish_site(self):
        self.bot.user_states[self.user_id] = {"step": "contact", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_contact")
        self.bot.finish_site.assert_called_once_with(self.chat_id, self.user_id)

    def test_skip_domain_transitions_to_hosting_plan(self):
        self.bot.user_states[self.user_id] = {"step": "domain", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_domain")
        assert self.bot.user_states[self.user_id]["step"] == "hosting_plan"

    def test_skip_hosting_transitions_to_payment(self):
        self.bot.user_states[self.user_id] = {"step": "hosting", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_hosting")
        assert self.bot.user_states[self.user_id]["step"] == "payment"

    def test_callback_with_no_user_state_does_nothing(self):
        # user_id is not in user_states
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_home")
        # Should not raise, just return

    def test_unknown_callback_data_does_nothing(self):
        self.bot.user_states[self.user_id] = {"step": "home", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "unknown_data")
        # State should remain unchanged
        assert self.bot.user_states[self.user_id]["step"] == "home"

    def test_send_message_called_on_skip(self):
        self.bot.user_states[self.user_id] = {"step": "home", "data": {}}
        self.bot.handle_callback(self.chat_id, self.user_id, "skip_home")
        self.bot.send_message.assert_called()


class TestStartFlow:
    """Tests for the start_flow method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.send_message = MagicMock()

    def test_start_flow_initializes_state(self):
        user_id = 123
        chat_id = 456
        self.bot.start_flow(user_id, chat_id)
        
        assert user_id in self.bot.user_states
        state = self.bot.user_states[user_id]
        assert state["step"] == "customer_info"
        assert "data" in state

    def test_start_flow_data_has_required_fields(self):
        user_id = 123
        chat_id = 456
        self.bot.start_flow(user_id, chat_id)
        
        data = self.bot.user_states[user_id]["data"]
        assert "sections" in data
        assert "images" in data
        assert "description_list" in data
        assert "about_list" in data
        assert "services_list" in data
        assert "orders_list" in data
        assert "customer_info" in data
        assert "site_name" in data
        assert "logo_url" in data
        assert "domain" in data
        assert "hosting_plan" in data
        assert "payment_status" in data

    def test_start_flow_sends_message(self):
        user_id = 123
        chat_id = 456
        self.bot.start_flow(user_id, chat_id)
        self.bot.send_message.assert_called_once()
        args = self.bot.send_message.call_args[0]
        assert args[0] == chat_id

    def test_start_flow_overrides_existing_state(self):
        user_id = 123
        chat_id = 456
        self.bot.user_states[user_id] = {"step": "old_step", "data": {}}
        self.bot.start_flow(user_id, chat_id)
        assert self.bot.user_states[user_id]["step"] == "customer_info"
