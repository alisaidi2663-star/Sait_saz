import os
import html
import base64
import shutil
from datetime import datetime
import time
import ssl
import ftplib

from utils.http_client import http_json_request, http_multipart_request, download_url
from utils.text_parser import parse_lines, parse_customer_info
from utils.html_generator import list_to_html, build_section_html, hex_to_rgb

# غیرفعال کردن بررسی گواهی SSL
ssl._create_default_https_context = ssl._create_unverified_context

# --- تنظیمات ربات باله ---
BOT_TOKEN = "1314583370:BIY4It0mLyF46CoGzb2BQ8PghV-H4Jh8YrI"
API_BASE = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

# --- تنظیمات API Reseller.World ---
# ⚠️ مهم: کلید API خود را از پنل رسلر بگیرید و اینجا قرار دهید
RESSELLER_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjM2NzNlOGY1LTU2M2EtNGE1OS05MWI3LTE4MDM4ZTliOWNjMiJ9.eyJhenAiOiJyZXNlbGxlci1hcGkiLCJvd25lcl9pZCI6MzY4OTM4LCJ1c2VyX2lkIjozNjcxNjcsImlhdCI6MTc3ODg2NzEzMywiZXhwIjoxODEwNDAzMTMzLCJqdGkiOiJjZTk0ZjcwYy1hNTVkLTRiNDEtYjYxMi0zY2NiYmViNTQ4YTkiLCJzaWQiOiJjZTk0ZjcwYy1hNTVkLTRiNDEtYjYxMi0zY2NiYmViNTQ4YTkiLCJ0eXAiOiJCZWFyZXIiLCJpc3MiOiJ1cm46aXJhbnNlcnZlcjphdXRoIiwic2NvcGUiOiJzZXJ2aWNlOnB1cmNoYXNlOmFwaSBzZXJ2aWNlOnJlbmV3OmFwaSBzZXJ2aWNlOmFjdGlvbnM6YXBpIHNlcnZpY2U6dmlldzphcGkifQ.g48ufQXwxsbrrDtQw8ycHehinoR9UgIPHD4PjgUOvm9fOnsFL1lmpqigmXponEFxcY3gVuIjaP-qbGz74cCuc7dukGNBe5b4xXUKzVjLR_MOgN-iyNHOA0IWq5-HgqN3-DBGBf2FErOl_OB-0F9ajyvKU-QK79UQT_w0HR8YDytgex4g8eiahiebWZ1w0UMU16l5NDaN8B9ADH4ePQ0dpsPH28DdNUjfag_G9shxGCW8STdaqoOT5E-aP7GjTGjdNO3qRrxl2IynT9Mnt61I3OTqDQHW52ePSDIJEV_qujEUpECDcPFeWEZjfqt5YZx41hwi_lVAn2GsXnodGfLAag"
RESSELLER_BASE_URL = "https://api.reseller.world/v1.5"

# --- تنظیمات مسیر ذخیره‌سازی موقت ---
HOME_DIR = os.path.expanduser("~")
TEMP_DIR = os.path.join(HOME_DIR, "sitebot_temp")

if not os.path.exists(TEMP_DIR):
    try:
        os.makedirs(TEMP_DIR)
        print(f"Temp directory created at: {TEMP_DIR}")
    except Exception as e:
        print(f"Error creating temp dir: {e}")

print("✅ ربات سایت ساز پیشرفته (با قابلیت خرید دامنه و هاست) روشن شد 🎉🎊")

COLOR_MAP = {
    "آبی": "#007bff", "قرمز": "#dc3545", "سبز": "#28a745", "زرد": "#ffc107",
    "نارنجی": "#fd7e14", "بنفش": "#6f42c1", "صورتی": "#e83e8c",
    "فیروزه‌ای": "#20c997", "مشکی": "#000000", "خاکستری": "#6c754d",
    "سفید": "#ffffff", "قهوه‌ای": "#795548"
}

# --- Configurable step flow to eliminate repetitive step-transition logic ---
# Each entry: (data_key, section_name_or_None, next_step, prompt_message)
SECTION_STEPS = {
    "home": ("description_list", None, "about", "📌 توضیحات بخش درباره ما را ارسال کنید یا رد کردن را بزن:"),
    "about": ("about_list", "about", "services", "💼 توضیحات بخش خدمات را ارسال کنید یا رد کردن را بزن:"),
    "services": ("services_list", "services", "orders", "🛒 متن بخش سفارشات را بفرست یا رد کن:"),
    "orders": ("orders_list", "orders", "logo", "🖼️ لینک عکس لوگو را ارسال کنید یا رد کردن را بزن:"),
}


def map_color(name):
    name = name.strip().lower()
    for k, v in COLOR_MAP.items():
        if k.lower() == name:
            return v
    return "#0095ff"


class SiteBuilderBot:
    def __init__(self):
        self.user_states = {}

    def api_request(self, method, params=None, files=None):
        """ارسال درخواست به API باله"""
        url = f"{API_BASE}/{method}"
        if files:
            return http_multipart_request(url, params=params, files=files, timeout=60)
        return http_json_request(url, payload=params, timeout=40)

    def send_message(self, chat_id, text, reply_markup=None):
        params = {"chat_id": chat_id, "text": text}
        if reply_markup:
            params["reply_markup"] = reply_markup
        return self.api_request("sendMessage", params)

    def send_document(self, chat_id, file_path, caption=""):
        try:
            if not os.path.exists(file_path):
                print(f"File not found error: {file_path}")
                self.send_message(chat_id, "❌ خطایی در ارسال فایل رخ داد. فایل پیدا نشد.")
                return None

            with open(file_path, "rb") as f:
                file_data = f.read()

            if len(file_data) > 50 * 1024 * 1024:
                self.send_message(chat_id, "فایل خیلی بزرگ است!")
                return None

            files = {
                "document": {"filename": os.path.basename(file_path), "content": file_data, "content_type": "application/zip"}
            }
            params = {"chat_id": chat_id}
            if caption:
                params["caption"] = caption

            result = self.api_request("sendDocument", params, files)

            if not result or not result.get("ok"):
                print(f"Server Error sending document: {result}")
                self.send_message(chat_id, "❌ سرور باله خطا داد. لطفاً بعداً دوباره تلاش کنید.")
                return None

            return result
        except Exception as e:
            print("send_document error:", e)
            return None

    def get_updates(self, offset=None):
        params = {"timeout": 25}
        if offset is not None:
            params["offset"] = offset
        return self.api_request("getUpdates", params)

    def keyboard(self, buttons):
        return {"inline_keyboard": buttons}

    def skip_keyboard(self, next_step):
        """Build a standard skip button keyboard for step transitions."""
        return self.keyboard([[{"text": "⏭ رد کردن", "callback_data": f"skip_{next_step}"}]])

    # --- توابع API Reseller.World ---

    def reseller_api_request(self, endpoint, params=None, payload=None):
        """ارسال درخواست به API رسلر"""
        import urllib.parse
        url = f"{RESSELLER_BASE_URL}{endpoint}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"
        headers = {
            "Authorization": f"Bearer {RESSELLER_API_KEY}",
            "Content-Type": "application/json"
        }
        return http_json_request(url, payload=payload, headers=headers, timeout=30)

    def register_domain_and_hosting(self, domain, hosting_plan, customer_info):
        """ثبت دامنه و خرید هاست"""
        payload = {
            "domain": domain,
            "plan": hosting_plan,
            "customer_name": customer_info.get("name", ""),
            "customer_phone": customer_info.get("phone", ""),
            "customer_national_code": customer_info.get("national_code", "")
        }
        return self.reseller_api_request("/multi_registrar/orders", payload=payload)

    def upload_site_to_host(self, ftp_host, ftp_user, ftp_pass, local_folder_path):
        """آپلود فایل‌های سایت روی هاست مشتری"""
        try:
            ftp = ftplib.FTP(ftp_host, ftp_user, ftp_pass)
            ftp.encoding = 'utf-8'

            try:
                ftp.cwd('/')
            except Exception:
                pass

            for filename in os.listdir(local_folder_path):
                filepath = os.path.join(local_folder_path, filename)
                if os.path.isfile(filepath):
                    with open(filepath, 'rb') as file:
                        ftp.storbinary(f'STOR {filename}', file)
                        print(f"Uploaded {filename}")

            ftp.quit()
            return True
        except Exception as e:
            print(f"FTP Upload Error: {e}")
            return False

    def start_flow(self, user_id, chat_id):
        self.user_states[user_id] = {
            "step": "customer_info",
            "data": {
                "sections": [],
                "images": [],
                "description_list": [],
                "about_list": [],
                "services_list": [],
                "orders_list": [],
                "customer_info": {},
                "site_name": "",
                "logo_url": "",
                "domain": "",
                "hosting_plan": "",
                "payment_status": False
            }
        }
        self.send_message(chat_id, "👋 سلام! لطفاً **نام و نام خانوادگی**، **کد ملی** و **شماره تماس** خود را در یک پیام بفرستید.")

    def handle_callback(self, chat_id, user_id, data):
        if data == "newsite":
            self.start_flow(user_id, chat_id)
            return

        skip_map = {
            "skip_home": "name",
            "skip_about": "about",
            "skip_services": "services",
            "skip_orders": "orders",
            "skip_logo": "contact",
            "skip_contact": "finish",
            "skip_domain": "hosting_plan",
            "skip_hosting": "payment"
        }

        if data in skip_map:
            st = self.user_states.get(user_id)
            if not st:
                return
            next_step = skip_map[data]
            st["step"] = next_step

            prompts = {
                "name": "✍️ نام سایت یا فروشگاه خود را ارسال کنید:",
                "about": "📌 متن بخش درباره ما را بفرست یا رد کن:",
                "services": "💼 متن بخش خدمات را بفرست یا رد کن:",
                "orders": "🛒 متن بخش سفارشات را بفرست یا رد کن:",
                "logo": "🖼️ لینک عکس لوگو را بفرست یا رد کن:",
                "contact": "📞 شماره تلفن و ایمیل فروشگاه را بفرست یا رد کن:",
                "domain": "🌐 نام دامنه مورد نظر خود را بنویسید (مثال: myshop.com). یا رد کردن را بزنید.",
                "hosting_plan": "💻 پلن هاست مورد نظر را انتخاب کنید:\n1. اقتصادی (۵۰۰ مگابایت)\n2. استاندارد (۱ گیگابایت)\n3. حرفه‌ای (۲ گیگابایت)\n\nیا رد کردن را بزنید تا از هاست پیش‌فرض استفاده شود.",
                "payment": "💳 لطفاً مبلغ را واریز کنید و کد پیگیری را ارسال کنید. یا رد کردن را بزنید (برای تست)."
            }

            prompt = prompts.get(next_step)
            if prompt:
                kb = self.skip_keyboard(next_step)
                self.send_message(chat_id, prompt, kb)
            else:
                self.finish_site(chat_id, user_id)

    def _handle_section_step(self, chat_id, state, data, text):
        """Generic handler for section-based steps (home, about, services, orders).

        Returns True if it handled the step, False otherwise.
        """
        step = state["step"]
        if step not in SECTION_STEPS:
            return False

        data_key, section_name, next_step, prompt = SECTION_STEPS[step]

        if text.strip():
            lines = parse_lines(text)
            data[data_key] = lines
            if section_name:
                data["sections"].append(section_name)

        state["step"] = next_step
        kb = self.skip_keyboard(next_step)
        self.send_message(chat_id, prompt, kb)
        return True

    def handle_message(self, chat_id, user_id, message):
        text = message.get("text", "")

        if text == "/start":
            kb = self.keyboard([[{"text": "🚀 ساخت سایت جدید", "callback_data": "newsite"}]])
            self.send_message(chat_id, "سلام! برای ساخت سایت روی دکمه زیر بزن.", kb)
            return

        if user_id not in self.user_states:
            kb = self.keyboard([[{"text": "🚀 ساخت سایت جدید", "callback_data": "newsite"}]])
            self.send_message(chat_id, "برای شروع ساخت سایت از دکمه زیر استفاده کن.", kb)
            return

        state = self.user_states[user_id]
        step = state["step"]
        data = state["data"]

        if step == "customer_info":
            if text.strip():
                data["customer_info"] = parse_customer_info(text)
                state["step"] = "name"
                self.send_message(chat_id, "✅ اطلاعات شما ثبت شد.\n\n✍️ نام سایت یا فروشگاه خود را ارسال کنید:")
            else:
                self.send_message(chat_id, "پیام نمی‌تواند خالی باشد. لطفا دوباره بفرست.")
            return

        if step == "name":
            if text.strip():
                data["site_name"] = text.strip()
                state["step"] = "color"
                self.send_message(chat_id, "🎨 رنگ سایت را انتخاب کنید (مثلاً آبی، قرمز، سبز...):")
            else:
                self.send_message(chat_id, "نام سایت نمی‌تواند خالی باشد. لطفا دوباره بفرست.")
            return

        if step == "color":
            if text.strip():
                data["color"] = map_color(text.strip())
                state["step"] = "home"
                kb = self.skip_keyboard("home")
                self.send_message(chat_id, "🧾 توضیحات بخش خانه را ارسال کنید یا رد کردن را بزن:", kb)
            else:
                self.send_message(chat_id, "لطفاً یک رنگ معتبر بنویسید.")
            return

        # Generic handler for home/about/services/orders steps
        if self._handle_section_step(chat_id, state, data, text):
            return

        if step == "logo":
            if text.strip():
                if "http" in text.lower():
                    data["logo_url"] = text.strip()
                    state["step"] = "contact"
                    kb = self.skip_keyboard("contact")
                    self.send_message(chat_id, "📞 شماره تلفن و ایمیل فروشگاه را ارسال کنید یا رد کردن را بزن:", kb)
                else:
                    self.send_message(chat_id, "⚠️ لطفاً یک لینک معتبر بفرستید.")
            else:
                self.send_message(chat_id, "لطفاً لینک را بفرستید یا رد کنید.")
            return

        if step == "contact":
            if text.strip():
                data["contact_text"] = text.strip()
                data["sections"].append("contact")
            state["step"] = "domain"
            kb = self.skip_keyboard("domain")
            self.send_message(chat_id, "🌐 **قدم بعدی: خرید دامنه و هاست**\n\nلطفاً نام دامنه مورد نظر خود را بنویسید (مثال: mysite.com).", kb)
            return

        if step == "domain":
            domain_input = text.strip().lower()
            if domain_input == "رد کردن":
                data["domain"] = ""
                state["step"] = "hosting_plan"
                self.send_message(chat_id, "✅ دامنه ثبت نشد. اکنون پلن هاست خود را انتخاب کنید:\n1. اقتصادی\n2. استاندارد\n3. حرفه‌ای")
                return

            if "." in domain_input:
                data["domain"] = domain_input
                self.send_message(chat_id, f"🔄 در حال بررسی موجودی دامنه {domain_input}...")
                state["step"] = "hosting_plan"
                self.send_message(chat_id, "✅ دامنه موجود است.\n\n💻 پلن هاست مورد نظر خود را انتخاب کنید:\n1. اقتصادی (۵۰۰ مگابایت)\n2. استاندارد (۱ گیگابایت)\n3. حرفه‌ای (۲ گیگابایت)")
            else:
                self.send_message(chat_id, "⚠️ لطفاً یک نام دامنه معتبر با پسوند (مثل .com یا .ir) وارد کنید.")
            return

        if step == "hosting_plan":
            plan_text = text.strip()
            if plan_text == "رد کردن":
                data["hosting_plan"] = "basic"
                state["step"] = "payment"
                self.send_message(chat_id, "✅ هاست پیش‌فرض (اقتصادی) انتخاب شد. لطفاً هزینه را واریز کنید.")
                return

            if "۱" in plan_text or "اقتصادی" in plan_text:
                data["hosting_plan"] = "basic"
                price = "۱۰۰,۰۰۰ تومان"
            elif "۲" in plan_text or "استاندارد" in plan_text:
                data["hosting_plan"] = "standard"
                price = "۲۰۰,۰۰۰ تومان"
            elif "۳" in plan_text or "حرفه‌ای" in plan_text:
                data["hosting_plan"] = "pro"
                price = "۳۵۰,۰۰۰ تومان"
            else:
                data["hosting_plan"] = "basic"
                price = "۱۰۰,۰۰۰ تومان"

            state["step"] = "payment"
            self.send_message(chat_id, f"💰 هزینه انتخابی شما: {price}\n\nلطفاً مبلغ را واریز کرده و کد پیگیری را ارسال کنید. (یا کلمه 'تست' را بفرستید)")
            return

        if step == "payment":
            if text.strip() in ["تست", "پرداخت شد", "رد کردن"]:
                data["payment_status"] = True
                state["step"] = "generating"
                self.send_message(chat_id, "✅ پرداخت دریافت شد (شبیه‌سازی).\n\n🚀 اکنون در حال ساخت سایت، ثبت دامنه و آپلود فایل‌ها هستیم. لطفاً صبر کنید...")
                self.finish_site(chat_id, user_id)
                return
            else:
                data["payment_status"] = True
                state["step"] = "generating"
                self.send_message(chat_id, "✅ کد پیگیری دریافت شد. در حال پردازش سفارش...")
                self.finish_site(chat_id, user_id)
                return

    def finish_site(self, chat_id, user_id):
        data = self.user_states.get(user_id, {}).get("data", {})
        data["user_id"] = user_id

        try:
            zip_path = self.generate_separate_files_site(data)

            domain_name = data.get("domain", "")
            hosting_plan = data.get("hosting_plan", "basic")
            customer_info = data.get("customer_info", {})

            site_url = ""
            ftp_info = {}

            if domain_name:
                self.send_message(chat_id, "🌐 در حال ثبت دامنه و خرید هاست...")
                reg_result = self.register_domain_and_hosting(domain_name, hosting_plan, customer_info)

                if reg_result.get("ok") or "id" in reg_result:
                    self.send_message(chat_id, "✅ دامنه و هاست با موفقیت ثبت شد.")
                    ftp_info = reg_result.get("ftp_info", {})
                    site_url = f"https://{domain_name}"
                else:
                    self.send_message(chat_id, "⚠️ خطا در ثبت دامنه. سایت بدون دامنه اختصاصی ساخته شد.")
                    site_url = "N/A (خطای ثبت دامنه)"
            else:
                self.send_message(chat_id, "ℹ️ دامنه‌ای ثبت نشد. سایت به صورت موقت ساخته شد.")
                site_url = "N/A (بدون دامنه)"

            if ftp_info and domain_name:
                self.send_message(chat_id, "📤 در حال آپلود فایل‌های سایت روی هاست...")
                local_folder = os.path.dirname(zip_path).replace('.zip', '')
                upload_success = self.upload_site_to_host(
                    ftp_info.get("host", ""),
                    ftp_info.get("user", ""),
                    ftp_info.get("pass", ""),
                    local_folder
                )
                if upload_success:
                    self.send_message(chat_id, "✅ فایل‌ها با موفقیت روی هاست آپلود شدند.")
                else:
                    self.send_message(chat_id, "⚠️ خطا در آپلود فایل‌ها. لطفاً فایل‌ها را دستی آپلود کنید.")

            if user_id in self.user_states:
                del self.user_states[user_id]

            self.send_document(chat_id, zip_path, "📄 فایل زیپ سایت شما")

            final_msg = f"""
🎉 **ساخت سایت شما تکمیل شد!**

🌐 آدرس سایت: {site_url}
📦 دامنه: {domain_name if domain_name else "ثبت نشد"}
💻 پلن هاست: {hosting_plan}

📌 **راهنمای آپلود دستی (در صورت نیاز):**
1. فایل زیپ را دانلود کنید.
2. فایل را اکسترکت کنید.
3. وارد پنل هاست خود شوید.
4. فایل‌ها را در public_html آپلود کنید.
            """
            self.send_message(chat_id, final_msg)

        except Exception as e:
            print(f"Error in finish_site: {e}")
            import traceback
            traceback.print_exc()
            self.send_message(chat_id, "❌ مشکلی در تولید یا ثبت سایت پیش آمد. لطفاً با ادمین تماس بگیرید.")

    def download_image_to_base64(self, url):
        image_data = download_url(url, timeout=10)
        if not image_data or len(image_data) < 1000:
            return None
        base64_string = base64.b64encode(image_data).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_string}"

    def generate_separate_files_site(self, data):
        name = html.escape(data.get("site_name", "سایت من"))
        color = html.escape(data.get("color", "#0095ff"))
        description_list = data.get("description_list", [])
        about_list = data.get("about_list", [])
        services_list = data.get("services_list", [])
        orders_list = data.get("orders_list", [])
        contact_text = data.get("contact_text", "")
        sections = data.get("sections", [])
        logo_url = data.get("logo_url", "")
        customer_info = data.get("customer_info", {})

        user_id = data.get("user_id", "unknown")

        processed_logo = ""
        if logo_url:
            b64_logo = self.download_image_to_base64(logo_url)
            if b64_logo:
                processed_logo = f'<img src="{b64_logo}" style="width:150px; margin-bottom:20px; border-radius:10px;" alt="لوگو">'
            else:
                processed_logo = f'<img src="{logo_url}" style="width:150px; margin-bottom:20px; border-radius:10px;" alt="لوگو">'

        description_html = list_to_html(description_list)
        about_html = list_to_html(about_list) if "about" in sections else ""
        services_html = list_to_html(services_list) if "services" in sections else ""
        orders_html = list_to_html(orders_list) if "orders" in sections else ""

        # Build optional sections using shared utility
        about_section = build_section_html("about", "درباره ما", about_html) if "about" in sections else ""
        services_section = build_section_html("services", "خدمات ما", services_html) if "services" in sections else ""

        orders_section = f"""
        <section id="orders" class="card">
            <h2 style="text-align: center; margin-bottom: 30px;">سفارش و تماس با ما</h2>
            <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #e9ecef; text-align: center;">
                <h3 style="margin: 0 0 15px 0; color: {color}; font-size: 1.2em;">اطلاعات تماس و محل سفارش</h3>
                <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;">
                    <div style="flex: 1; min-width: 200px;">
                        <strong>📞 شماره تماس:</strong><br>
                        <span style="direction: ltr; display: inline-block;">{html.escape(contact_text)}</span>
                    </div>
                </div>
            </div>
            <form onsubmit="event.preventDefault(); alert('سفارش شما ثبت شد!');" style="background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee;">
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">نام و نام خانوادگی</label>
                    <input type="text" required placeholder="مثال: علی محمدی" style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">شماره تلفن</label>
                    <input type="tel" required placeholder="مثال: 09123456789" style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">متن سفارش</label>
                    <textarea rows="4" required placeholder="جزئیات سفارش..." style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical;"></textarea>
                </div>
                <button type="submit" style="background-color: {color}; color: white; border: none; padding: 14px 24px; border-radius: 8px; cursor: pointer; font-size: 1.1em; font-weight: bold; width: 100%;">ارسال سفارش</button>
            </form>
        </section>
        """

        contact_html_content = ""
        if contact_text:
            contact_html_content = f"""
            <div style="background: #f8f9fa; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #e9ecef; text-align: center;">
                <h3 style="margin: 0 0 15px 0; color: {color}; font-size: 1.2em;">اطلاعات تماس</h3>
                <p style="direction: ltr; display: inline-block;">{html.escape(contact_text)}</p>
            </div>
            """

        contact_section = f"""
        <section id="contact" class="card">
            <h2 style="text-align: center;">تماس با ما</h2>
            {contact_html_content}
        </section>
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"site_{user_id}_{timestamp}"
        folder_path = os.path.join(TEMP_DIR, folder_name)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)

        color_rgb = hex_to_rgb(color)

        css_template = """
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;700;800&display=swap');

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: 'Vazirmatn', Tahoma, sans-serif;
    background-color: #f0f2f5;
    color: #444;
    line-height: 1.6;
    font-size: 16px;
}}

header {{
    background: linear-gradient(135deg, {color}, {color}dd);
    color: #fff;
    padding: 40px 20px;
    text-align: center;
    border-radius: 0 0 20px 20px;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}}

header h1 {{
    margin: 10px 0 0 0;
    font-size: 2.5em;
    font-weight: 800;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}}

.container {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 20px;
}}

.card {{
    background: #fff;
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    border: 1px solid #eee;
}}

h2 {{
    color: {color};
    margin-top: 0;
    font-weight: 700;
    font-size: 1.8em;
    margin-bottom: 20px;
    border-bottom: 2px solid #f0f0f0;
    padding-bottom: 10px;
}}

ul {{
    padding-right: 20px;
    margin: 15px 0;
}}

li {{
    margin-bottom: 10px;
    font-size: 1.05em;
    line-height: 1.5;
}}

footer {{
    text-align: center;
    padding: 40px 20px;
    background: linear-gradient(135deg, {color}, {color}dd);
    color: white;
    margin-top: 40px;
    border-radius: 20px 20px 0 0;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
}}

footer h3 {{
    margin: 0 0 10px 0;
    font-size: 1.5em;
}}

footer p {{
    margin: 0;
    font-size: 1.1em;
    opacity: 0.9;
}}

footer a {{
    color: #ffd700;
    text-decoration: none;
    font-weight: bold;
    display: inline-block;
    margin-top: 10px;
    background: rgba(255,255,255,0.2);
    padding: 5px 15px;
    border-radius: 20px;
}}
"""
        css_content = css_template.format(color=color, color_rgb=color_rgb)

        with open(os.path.join(folder_path, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)

        js_content = """
// Placeholder for JS if needed
"""
        with open(os.path.join(folder_path, 'script.js'), 'w', encoding='utf-8') as f:
            f.write(js_content)

        logo_html = f'<div style="text-align:center; margin-bottom:20px;">{processed_logo}</div>' if processed_logo else ""

        footer_html = """
        <footer>
            <h3 style="margin: 0 0 10px 0; font-size: 1.5em;">آکادمی سیمرغ ایرانی</h3>
            <p style="margin: 0; font-size: 1.1em; opacity: 0.9;">ربات سایت‌ساز محصول آکادمی سیمرغ ایرانی</p>
            <a href="https://t.me/cimorgh_irani" style="color: #ffd700; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px;">@cimorgh_irani</a>
        </footer>
        """

        html_content = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  {logo_html}
  <h1>{name}</h1>
</header>
<div class="container">
  <section id="home" class="card">
    <h2>خانه</h2>
    {description_html if description_html else '<p style="color:#888;">توضیحاتی درج نشده است.</p>'}
  </section>

  {about_section}
  {services_section}
  {orders_section}
  {contact_section}
</div>
{footer_html}
<script src="script.js"></script>
</body>
</html>"""

        with open(os.path.join(folder_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)

        customer_info_text = f"""اطلاعات مشتری ثبت شده:
--------------------------------
نام و نام خانوادگی: {customer_info.get('name', 'نامشخص')}
کد ملی: {customer_info.get('national_code', 'نامشخص')}
شماره تماس: {customer_info.get('phone', 'نامشخص')}
--------------------------------
تاریخ ثبت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        with open(os.path.join(folder_path, 'customer_info.txt'), 'w', encoding='utf-8') as f:
            f.write(customer_info_text)

        zip_filename = os.path.join(TEMP_DIR, f"site_{user_id}_{timestamp}")
        shutil.make_archive(zip_filename, 'zip', folder_path)

        final_zip_path = f"{zip_filename}.zip"
        return final_zip_path


def main():
    bot = SiteBuilderBot()
    offset = None
    print("Bot started... Waiting for messages.")
    print(f"Temp directory: {TEMP_DIR}")

    while True:
        try:
            updates = bot.get_updates(offset)
            if not updates or "result" not in updates:
                continue
            for update in updates["result"]:
                offset = update["update_id"] + 1

                # مدیریت کال‌بک‌ها (دکمه‌ها)
                if "callback_query" in update:
                    cq = update["callback_query"]
                    user_id = cq["from"]["id"]
                    chat_id = cq["message"]["chat"]["id"]
                    callback_data = cq.get("data", "")
                    try:
                        bot.api_request("answerCallbackQuery", {"callback_query_id": cq["id"]})
                    except Exception:
                        pass
                    bot.handle_callback(chat_id, user_id, callback_data)
                    continue

                # مدیریت پیام‌های متنی
                msg = update.get("message")
                if not msg:
                    continue

                chat_id = msg["chat"]["id"]
                user_id = msg["from"]["id"] if "from" in msg else chat_id
                bot.handle_message(chat_id, user_id, msg)

        except Exception as e:
            print(f"Main loop error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
