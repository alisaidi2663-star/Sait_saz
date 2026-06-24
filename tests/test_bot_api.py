"""Tests for bot API methods: keyboard, send_message, send_document, api_request."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile

with patch('os.makedirs'), patch('builtins.print'):
    from Sayt_saz_simorgh import SiteBuilderBot


class TestKeyboard:
    """Tests for keyboard utility method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()

    def test_keyboard_returns_inline_keyboard(self):
        buttons = [[{"text": "btn1", "callback_data": "data1"}]]
        result = self.bot.keyboard(buttons)
        assert result == {"inline_keyboard": buttons}

    def test_keyboard_with_multiple_rows(self):
        buttons = [
            [{"text": "btn1", "callback_data": "d1"}],
            [{"text": "btn2", "callback_data": "d2"}]
        ]
        result = self.bot.keyboard(buttons)
        assert len(result["inline_keyboard"]) == 2

    def test_keyboard_empty_buttons(self):
        result = self.bot.keyboard([])
        assert result == {"inline_keyboard": []}


class TestSendMessage:
    """Tests for send_message method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.api_request = MagicMock(return_value={"ok": True})

    def test_send_message_calls_api_request(self):
        self.bot.send_message(123, "hello")
        self.bot.api_request.assert_called_once_with(
            "sendMessage", {"chat_id": 123, "text": "hello"}
        )

    def test_send_message_with_reply_markup(self):
        markup = {"inline_keyboard": [[{"text": "btn", "callback_data": "x"}]]}
        self.bot.send_message(123, "hello", reply_markup=markup)
        self.bot.api_request.assert_called_once_with(
            "sendMessage", {"chat_id": 123, "text": "hello", "reply_markup": markup}
        )

    def test_send_message_returns_api_result(self):
        self.bot.api_request = MagicMock(return_value={"ok": True, "result": {}})
        result = self.bot.send_message(123, "hi")
        assert result == {"ok": True, "result": {}}


class TestSendDocument:
    """Tests for send_document method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.api_request = MagicMock(return_value={"ok": True})
        self.bot.send_message = MagicMock()

    def test_send_document_file_not_found(self):
        result = self.bot.send_document(123, "/nonexistent/path.zip")
        assert result is None
        self.bot.send_message.assert_called()

    def test_send_document_with_valid_file(self):
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            result = self.bot.send_document(123, temp_path, "caption")
            self.bot.api_request.assert_called_once()
            assert result == {"ok": True}
        finally:
            os.unlink(temp_path)

    def test_send_document_large_file_rejected(self):
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            # Write > 50MB
            f.write(b"x" * (51 * 1024 * 1024))
            temp_path = f.name
        
        try:
            result = self.bot.send_document(123, temp_path)
            assert result is None
            self.bot.send_message.assert_called()
        finally:
            os.unlink(temp_path)

    def test_send_document_api_error(self):
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(b"content")
            temp_path = f.name
        
        self.bot.api_request = MagicMock(return_value={"ok": False})
        
        try:
            result = self.bot.send_document(123, temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)


class TestGetUpdates:
    """Tests for get_updates method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.api_request = MagicMock(return_value={"ok": True, "result": []})

    def test_get_updates_without_offset(self):
        self.bot.get_updates()
        self.bot.api_request.assert_called_once_with("getUpdates", {"timeout": 25})

    def test_get_updates_with_offset(self):
        self.bot.get_updates(offset=42)
        self.bot.api_request.assert_called_once_with("getUpdates", {"timeout": 25, "offset": 42})


class TestApiRequest:
    """Tests for api_request method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()

    @patch('urllib.request.urlopen')
    def test_api_request_json_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"ok": True}).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.bot.api_request("testMethod", {"key": "value"})
        assert result == {"ok": True}

    @patch('urllib.request.urlopen')
    def test_api_request_handles_http_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://test", 400, "Bad Request", {}, None
        )
        result = self.bot.api_request("testMethod", {})
        assert result["ok"] is False

    @patch('urllib.request.urlopen')
    def test_api_request_handles_general_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection timeout")
        result = self.bot.api_request("testMethod", {})
        assert result["ok"] is False
        assert "Connection timeout" in result["error"]


class TestResellerApiRequest:
    """Tests for reseller_api_request method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()

    @patch('urllib.request.urlopen')
    def test_reseller_api_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"status": "ok"}).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.bot.reseller_api_request("/test", {"param": "value"})
        assert result == {"status": "ok"}

    @patch('urllib.request.urlopen')
    def test_reseller_api_handles_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")
        result = self.bot.reseller_api_request("/test")
        assert "error" in result


class TestDownloadImageToBase64:
    """Tests for download_image_to_base64 method."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()

    @patch('urllib.request.urlopen')
    def test_successful_image_download(self, mock_urlopen):
        # Simulate a valid image (> 1000 bytes)
        fake_image = b'\x89PNG' + b'\x00' * 2000
        mock_response = MagicMock()
        mock_response.read.return_value = fake_image
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.bot.download_image_to_base64("https://example.com/img.png")
        assert result is not None
        assert result.startswith("data:image/jpeg;base64,")

    @patch('urllib.request.urlopen')
    def test_small_image_returns_none(self, mock_urlopen):
        # Simulate a too-small response (< 1000 bytes)
        fake_image = b'\x89PNG' + b'\x00' * 100
        mock_response = MagicMock()
        mock_response.read.return_value = fake_image
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.bot.download_image_to_base64("https://example.com/tiny.png")
        assert result is None

    @patch('urllib.request.urlopen')
    def test_network_error_returns_none(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Timeout")
        result = self.bot.download_image_to_base64("https://example.com/fail.png")
        assert result is None
