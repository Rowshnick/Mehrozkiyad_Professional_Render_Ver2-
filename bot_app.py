import os
from datetime import datetime
import swisseph as swe
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from dotenv import load_dotenv
from persiantools.jdatetime import JalaliDate
import requests

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8443))  # Render پورت اختصاصی خودش را می‌دهد

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ BOT_TOKEN یا WEBHOOK_URL تنظیم نشده است!")

# Conversation states
SELECT_LANGUAGE, GET_YEAR, GET_MONTH, GET_DAY, SHOW_HOROSCOPE = range(5)
user_data_store = {}

# دکمه‌های زبان
LANG_KEYBOARD = [
    [InlineKeyboardButton("فارسی", callback_data="fa")],
    [InlineKeyboardButton("English", callback_data="en")]
]

# هوروسکوپ
def generate_horoscope_text(birth_date: datetime, lang="fa") -> str:
    jd = swe.julday(birth_date.year, birth_date.month, birth_date.day)
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO
    }
    horoscope = ""
    for name, code in planets.items():
        lon, lat, _ = swe.calc(jd, code)[:3]
        horoscope += f"{name}: Longitude={lon:.2f}, Latitude={lat:.2f}\n"
    horoscope += "\nپیشنهاد: روی خودشناسی و روابط تمرکز کنید.\n" if lang=="fa" else "\nSuggestion: Focus on self-awareness and relationships.\n"
    return horoscope

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(LANG_KEYBOARD)
    await update.message.reply_text(
        "لطفاً زبان خود را انتخاب کنید / Please select your language:", 
        reply_markup=keyboard
    )
    return SELECT_LANGUAGE

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    user_data_store[query.from_user.id] = {"lang": lang}
    await query.message.reply_text(
        "زبان انتخاب شد: {}\nلطفاً سال تولد خود را وارد کنید (مثال: 1402 یا 1983):".format(lang)
    )
    return GET_YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("لطفاً فقط عدد وارد کنید.")
        return GET_YEAR
    user_data_store[update.message.from_user.id]["year"] = int(text)
    await update.message.reply_text("لطفاً ماه تولد خود را وارد کنید (1-12):")
    return GET_MONTH

async def get_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or not (1 <= int(text) <= 12):
        await update.message.reply_text("لطفاً ماه را بین 1 تا 12 وارد کنید.")
        return GET_MONTH
    user_data_store[update.message.from_user.id]["month"] = int(text)
    await update.message.reply_text("لطفاً روز تولد خود را وارد کنید (1-31):")
    return GET_DAY

async def get_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or not (1 <= int(text) <= 31):
        await update.message.reply_text("لطفاً روز را بین 1 تا 31 وارد کنید.")
        return GET_DAY

    uid = update.message.from_user.id
    user_data_store[uid]["day"] = int(text)

    # تبدیل تاریخ شمسی به میلادی اگر لازم باشد
    year = user_data_store[uid]["year"]
    month = user_data_store[uid]["month"]
    day = user_data_store[uid]["day"]

    if year > 1700:
        try:
            birth_date = JalaliDate(year, month, day).to_gregorian()
        except:
            await update.message.reply_text("تاریخ وارد شده نامعتبر است.")
            return GET_YEAR
    else:
        birth_date = datetime(year, month, day)

    user_data_store[uid]["birth_date"] = birth_date
    horoscope = generate_horoscope_text(birth_date, user_data_store[uid]["lang"])
    await update.message.reply_text(horoscope)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END

# Application
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        SELECT_LANGUAGE: [CallbackQueryHandler(language_choice, per_message=True)],
        GET_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
        GET_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_month)],
        GET_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_day)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

# حذف webhook قبلی و ست کردن جدید
requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")

if __name__ == "__main__":
    print("🚀 Bot running with Webhook on Render...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,             # Render پورت اختصاصی خودش را می‌دهد
        webhook_url=WEBHOOK_URL
    )
