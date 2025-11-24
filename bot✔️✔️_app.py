# bot_app.py
import os
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from persiantools.jdatetime import JalaliDate
from dotenv import load_dotenv

# این ماژول‌ها باید در پوشه utils شما موجود باشند و نام توابع/رنگ/خروجی‌ها مطابق استفاده زیر باشند.
from utils import astro, healing

# ---------- بارگذاری env ----------
load_dotenv()

# ---------- لاگینگ ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- حالت‌های Conversation ----------
SELECT_LANGUAGE, ENTER_YEAR, ENTER_MONTH, ENTER_DAY = range(4)

# ---------- خواندن ENV (از Render) ----------
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثل https://your-app.onrender.com

if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN در متغیرهای محیطی تنظیم نشده است.")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL در متغیرهای محیطی تنظیم نشده است.")

# ---------- Handler ها ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    استارت: انتخاب زبان (Inline keyboard با callback data)
    """
    # اگر پیام از نوع CallbackQuery بیاید، update.message ممکن است None باشد؛ اما start از طریق /start اجرا می‌شود و پیام وجود دارد.
    keyboard = [
        [InlineKeyboardButton("فارسی 🇮🇷", callback_data="fa")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="en")],
    ]
    await update.message.reply_text(
        "لطفاً زبان مورد نظر را انتخاب کنید:" , reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_LANGUAGE

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    کاربر زبان را انتخاب کرد — این یک CallbackQuery است.
    این هندلر انتخاب زبان را ذخیره کرده و کاربر را به وارد کردن سال هدایت می‌کند.
    """
    query = update.callback_query
    await query.answer()

    lang = query.data
    context.user_data["lang"] = lang

    # پاسخ دادن به کاربر و درخواست سال تولد
    if lang == "fa":
        # از ارسال پیام جدید استفاده می‌کنیم تا پیام inline حفظ شود
        await query.message.reply_text("سال تولد را وارد کنید (مثال: 1375):")
    else:
        await query.message.reply_text("Enter your birth year (e.g., 1996):")

    return ENTER_YEAR

async def enter_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    کاربر سال را وارد کرد — ذخیره و درخواست ماه
    """
    text = update.message.text.strip()
    try:
        year = int(text)
    except Exception:
        lang = context.user_data.get("lang")
        if lang == "fa":
            await update.message.reply_text("⚠️ سال نامعتبر است. لطفاً فقط عدد وارد کنید (مثال: 1375).")
        else:
            await update.message.reply_text("⚠️ Invalid year. Please enter a number (e.g., 1996).")
        return ENTER_YEAR

    context.user_data["year"] = year
    lang = context.user_data.get("lang")
    if lang == "fa":
        await update.message.reply_text("ماه تولد را وارد کنید (1 تا 12):")
    else:
        await update.message.reply_text("Enter your birth month (1-12):")
    return ENTER_MONTH

async def enter_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        month = int(text)
        if month < 1 or month > 12:
            raise ValueError()
    except Exception:
        lang = context.user_data.get("lang")
        if lang == "fa":
            await update.message.reply_text("⚠️ ماه نامعتبر است. عددی بین 1 تا 12 وارد کنید.")
        else:
            await update.message.reply_text("⚠️ Invalid month. Enter a number between 1 and 12.")
        return ENTER_MONTH

    context.user_data["month"] = month
    lang = context.user_data.get("lang")
    if lang == "fa":
        await update.message.reply_text("روز تولد را وارد کنید (1 تا 31):")
    else:
        await update.message.reply_text("Enter your birth day (1-31):")
    return ENTER_DAY

async def enter_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        day = int(text)
        if day < 1 or day > 31:
            raise ValueError()
    except Exception:
        lang = context.user_data.get("lang")
        if lang == "fa":
            await update.message.reply_text("⚠️ روز نامعتبر است. عددی بین 1 تا 31 وارد کنید.")
        else:
            await update.message.reply_text("⚠️ Invalid day. Enter a number between 1 and 31.")
        return ENTER_DAY

    # خواندن year/month که قبلاً ذخیره شده
    year = context.user_data.get("year")
    month = context.user_data.get("month")
    lang = context.user_data.get("lang", "en")

    # تبدیل تاریخ (اگر زبان فارسی است: Jalali -> Gregorian)
    try:
        if lang == "fa":
            # JalaliDate از persiantools
            gregorian = JalaliDate(year, month, day).to_gregorian()
            birth_date = datetime(gregorian.year, gregorian.month, gregorian.day)
        else:
            birth_date = datetime(year, month, day)
    except Exception:
        if lang == "fa":
            await update.message.reply_text("⚠️ ترکیب تاریخ نامعتبر است. لطفاً دوباره /start را بزنید و تاریخ را اصلاح کنید.")
        else:
            await update.message.reply_text("⚠️ Invalid date combination. Please /start and try again.")
        return ConversationHandler.END

    # ذخیره در user_data
    context.user_data["birth_date"] = birth_date

    # ---------- فراخوانی ماژول پیشگویی (astro) و پیشنهاد sigil (healing) ----------
    # فرض: astro.get_horoscope یا astro.get_prediction تابعی است که با یک datetime یا user_data کار می‌کند.
    try:
        # سعی می‌کنیم تابع‌های متداول را صدا بزنیم؛ اگر نام تابع متفاوت است در utils آن را تغییر دهید.
        # نخست تلاش برای get_horoscope با datetime
        if hasattr(astro, "get_horoscope"):
            result = astro.get_horoscope(birth_date)
        elif hasattr(astro, "get_prediction"):
            result = astro.get_prediction({"birth_date": birth_date})
        else:
            result = "🪄 پیشگویی در دسترس نیست (astro)."

        # healing: پیشنهاد sigil — فرض تابع suggest_sigil یا suggest exists
        if hasattr(healing, "suggest_sigil"):
            healing_result = healing.suggest_sigil({"birth_date": birth_date})
        elif hasattr(healing, "get_sigil"):
            healing_result = healing.get_sigil({"birth_date": birth_date})
        else:
            healing_result = "🪬 پیشنهاد Sigil در دسترس نیست (healing)."

    except Exception as e:
        logger.exception("خطا هنگام اجرای ماژول‌های astro/healing:")
        result = f"⚠️ خطا در تولید پیشگویی: {e}"
        healing_result = ""

    # ارسال نتیجه به زبان مناسب
    if lang == "fa":
        await update.message.reply_text(f"🎯 نتیجه تحلیل:\n\n{result}\n\n🔮 پیشنهاد: {healing_result}")
    else:
        await update.message.reply_text(f"🎯 Your horoscope:\n\n{result}\n\n🔮 Suggestion: {healing_result}")

    return ConversationHandler.END

# Health command (تلگرام)
async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Health OK - Bot is running ✔")

# ---------- تابع main ----------
def main():
    # ساخت اپلیکیشن و استفاده از TOKEN از ENV
    application = ApplicationBuilder().token(TOKEN).build()

    # ConversationHandler: 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # SELECT_LANGUAGE از طریق CallbackQueryHandler (inline keyboard) مدیریت می‌شود
            SELECT_LANGUAGE: [CallbackQueryHandler(language_choice)],
            # بقیه مراحل پیام متنی هستند
            ENTER_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_year)],
            ENTER_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_month)],
            ENTER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_day)],
        },
        fallbacks=[CommandHandler("start", start)],
        # از مقدار پیش‌فرض per_message=False استفاده می‌کنیم تا MessageHandler ها کار کنند.
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("health", health_cmd))

    # ---------- Webhook configuration for Render ----------
    # Render از PORT محیطی استفاده می‌کند. پیش‌فرض 8000.
    PORT = int(os.environ.get("PORT", 8000))

    # مسیر وبهوک در اپ شما
    WEBHOOK_PATH = "/webhook"  # نگه داشتن همان مسیر که در لاگ‌ها نشان داده شده
    # اطمینان از اینکه WEBHOOK_URL بدون اسلش اضافی خاتمه یابد
    webhook_base = WEBHOOK_URL.rstrip("/")
    WEBHOOK_FULL_URL = webhook_base + WEBHOOK_PATH

    logger.info("Setting webhook to: %s", WEBHOOK_FULL_URL)

    # Application.run_webhook: url_path نباید leading slash داشته باشد در بعضی نسخه‌ها، بنابراین بدون / هم می‌دهیم
    url_path_for_ptb = WEBHOOK_PATH.lstrip("/")

    # راه‌اندازی وبهوک
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=url_path_for_ptb,
        webhook_url=WEBHOOK_FULL_URL,
    )

if __name__ == "__main__":
    main()
