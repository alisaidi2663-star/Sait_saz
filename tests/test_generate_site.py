"""Tests for generate_separate_files_site method."""
import sys
import os
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from unittest.mock import patch, MagicMock

with patch('os.makedirs'), patch('builtins.print'):
    from Sayt_saz_simorgh import SiteBuilderBot, TEMP_DIR


class TestGenerateSeparateFilesSite:
    """Tests for HTML/CSS/JS site generation."""

    def setup_method(self):
        with patch('builtins.print'):
            self.bot = SiteBuilderBot()
        self.bot.download_image_to_base64 = MagicMock(return_value=None)
        # Ensure TEMP_DIR exists
        os.makedirs(TEMP_DIR, exist_ok=True)

    def teardown_method(self):
        # Clean up generated files
        if os.path.exists(TEMP_DIR):
            for item in os.listdir(TEMP_DIR):
                item_path = os.path.join(TEMP_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif item.endswith('.zip'):
                    os.remove(item_path)

    def _make_data(self, **overrides):
        data = {
            "site_name": "سایت تست",
            "color": "#007bff",
            "description_list": ["توضیح اول", "توضیح دوم"],
            "about_list": ["درباره ما"],
            "services_list": ["خدمت ۱"],
            "orders_list": ["سفارش ۱"],
            "contact_text": "09121234567",
            "sections": ["about", "services", "orders", "contact"],
            "logo_url": "",
            "customer_info": {"name": "تست", "national_code": "1234567890", "phone": "09121234567"},
            "user_id": "test_user_123",
        }
        data.update(overrides)
        return data

    def test_generates_zip_file(self):
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        assert zip_path.endswith('.zip')
        assert os.path.exists(zip_path)

    def test_zip_contains_index_html(self):
        import zipfile
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert 'index.html' in names

    def test_zip_contains_style_css(self):
        import zipfile
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert 'style.css' in names

    def test_zip_contains_script_js(self):
        import zipfile
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert 'script.js' in names

    def test_zip_contains_customer_info_txt(self):
        import zipfile
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert 'customer_info.txt' in names

    def test_html_contains_site_name(self):
        import zipfile
        data = self._make_data(site_name="فروشگاه تست")
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert "فروشگاه تست" in html_content

    def test_html_contains_description_items(self):
        import zipfile
        data = self._make_data(description_list=["آیتم اول", "آیتم دوم"])
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert "آیتم اول" in html_content
            assert "آیتم دوم" in html_content

    def test_html_contains_about_section_when_included(self):
        import zipfile
        data = self._make_data(sections=["about"], about_list=["متن درباره ما"])
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert "درباره ما" in html_content
            assert "متن درباره ما" in html_content

    def test_html_excludes_about_section_when_not_included(self):
        import zipfile
        data = self._make_data(sections=[], about_list=["something"])
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert 'id="about"' not in html_content

    def test_css_contains_color(self):
        import zipfile
        data = self._make_data(color="#dc3545")
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            css_content = zf.read('style.css').decode('utf-8')
            assert "#dc3545" in css_content

    def test_html_is_rtl(self):
        import zipfile
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert 'dir="rtl"' in html_content

    def test_html_has_proper_charset(self):
        import zipfile
        data = self._make_data()
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert 'charset="UTF-8"' in html_content

    def test_customer_info_file_contains_name(self):
        import zipfile
        data = self._make_data(customer_info={"name": "حسین", "national_code": "1234567890", "phone": "09121234567"})
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            info_content = zf.read('customer_info.txt').decode('utf-8')
            assert "حسین" in info_content

    def test_empty_description_shows_placeholder(self):
        import zipfile
        data = self._make_data(description_list=[])
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert "توضیحاتی درج نشده" in html_content

    def test_logo_url_embedded_when_provided(self):
        import zipfile
        data = self._make_data(logo_url="https://example.com/logo.png")
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert "https://example.com/logo.png" in html_content

    def test_services_section_included(self):
        import zipfile
        data = self._make_data(sections=["services"], services_list=["خدمت تست"])
        zip_path = self.bot.generate_separate_files_site(data)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            html_content = zf.read('index.html').decode('utf-8')
            assert "خدمت تست" in html_content
