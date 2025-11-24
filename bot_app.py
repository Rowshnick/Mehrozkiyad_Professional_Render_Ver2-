import os
import logging
from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler, CallbackQueryHandler
)
from persiantools.jdatetime import JalaliDate
from pytz import timezone
from dotenv import load_dotenv
from utils import astro, healing

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
SELECT_LANGUAGE, ENTER_YEAR, ENTER_MONTH, ENTER_DAY, SHOW_RESULTS = range(5)

# Load environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ TELEGRAM_TOKEN یا WEBHOOK_URL در فایل env تنظیم نشده است.")

# -------------------------------
# Start command
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("فارسی 🇮🇷", callback_data="fa")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="en")]
    ]
    await update.message.reply_text(
        "لطفاً زبان مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_LANGUAGE

# -------------------------------
# Language selection
# -------------------------------
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data
    context.user_data["lang"] = lang

    if lang == "fa":
        await query.message.reply_text("سال تولد را وارد کنید (مثال: 1375):")
    else:
        await query.message.reply_text("Enter your birth year (e.g., 1996):")

    return ENTER_YEAR

# -------------------------------
# Persian or Gregorian Date Input
# -------------------------------
async def enter_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = int(update.message.text)

    lang = context.user_data.get("lang")
    if lang == "fa":
        await update.message.reply_text("ماه تولد را وارد کنید (1 تا 12):")
    else:
        await update.message.reply_text("Enter your birth month (1-12):")

    return ENTER_MONTH

async def enter_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["month"] = int(update.message.text)

    lang = context.user_data.get("lang")
    if lang == "fa":
        await update.message.reply_text("روز تولد را وارد کنید (1 تا 31):")
    else:
        await update.message.reply_text("Enter your birth day (1-31):")

    return ENTER_DAY

async def enter_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = int(update.message.text)
    year = context.user_data["year"]
    month = context.user_data["month"]
    lang = context.user_data.get("lang")

    try:
        # Convert Jalali → Gregorian automatically for Persian users
        if lang == "fa":
            gregorian = JalaliDate(year, month, day).to_gregorian()
            birth_date = datetime(gregorian.year, gregorian.month, gregorian.day)
        else:
            birth_date = datetime(year, month, day)

        context.user_data["birth_date"] = birth_date

    except Exception:
        if lang == "fa":
            await update.message.reply_text("⚠️ تاریخ نامعتبر است. دوباره وارد کنید.")
        else:
            await update.message.reply_text("⚠️ Invalid date. Please try again.")
        return ENTER_DAY

    # Horoscope calculation
    result = astro.get_horoscope(birth_date)

    if lang == "fa":
        await update.message.reply_text(f"🎯 نتیجه تحلیل:\n\n{result}")
    else:
        await update.message.reply_text(f"🎯 Your horoscope:\n\n{result}")

    return ConversationHandler.END

# -------------------------------
# Main
# -------------------------------
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANGUAGE: [CallbackQueryHandler(language_choice)],   # ✔ اصلاح شد
            ENTER_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_year)],
            ENTER_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_month)],
            ENTER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_day)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    # -----------------------------
    # Correct Webhook configuration for Render
    # -----------------------------
    PORT = int(os.environ.get("PORT", 8000))

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,                    # ✔ استفاده از پورت Render
        webhook_url=WEBHOOK_URL       # ✔ بدون پورت اضافه
    )

if __name__ == "__main__":
    main()
