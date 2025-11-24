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
import pytz

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL is missing!")


# -----------------------------
# Conversation States
# -----------------------------
SELECT_LANGUAGE, GET_BIRTHDATE, SHOW_HOROSCOPE = range(3)

# temp storage
user_data_store = {}


LANG_KEYBOARD = [
    [InlineKeyboardButton("فارسی", callback_data="fa")],
    [InlineKeyboardButton("English", callback_data="en")]
]


# -----------------------------
# Horoscope Generator
# -----------------------------
def generate_horoscope_text(birth_date: datetime, lang="fa") -> str:
    jd = swe.julday(birth_date.year, birth_date.month, birth_date.day)
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO
    }

    horoscope = ""
    for name, code in planets.items():
        lon, lat, dist = swe.calc(jd, code)[:3]
        horoscope += f"{name}: Longitude={lon:.2f}, Latitude={lat:.2f}\n"

    if lang == "fa":
        horoscope += "\nپیشنهاد: امروز روی خودشناسی و روابط خود تمرکز کنید.\n"
    else:
        horoscope += "\nSuggestion: Focus on self-awareness and your relationships today.\n"

    return horoscope


# -----------------------------
# Conversation Handlers
# -----------------------------
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

    await query.message.reply_text(f"زبان انتخاب شد: {lang}")
    return GET_BIRTHDATE


async def get_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        birth_date = datetime.strptime(text, "%Y-%m-%d")
        user_data_store[update.message.from_user.id]["birth_date"] = birth_date

        horoscope = generate_horoscope_text(
            birth_date,
            user_data_store[update.message.from_user.id]["lang"]
        )

        await update.message.reply_text(horoscope)
    except:
        await update.message.reply_text(
            "❌ فرمت تاریخ اشتباه است.\nمثال: 1998-05-21"
        )
    return SHOW_HOROSCOPE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


# -----------------------------
# Build Telegram Application
# -----------------------------
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        SELECT_LANGUAGE: [
            CallbackQueryHandler(language_choice)
        ],
        GET_BIRTHDATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)
        ],
        SHOW_HOROSCOPE: []
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=True   # ← رفع warning PTB
)

app.add_handler(conv_handler)


# -----------------------------
# Webhook Runner (Render-compatible)
# -----------------------------
if __name__ == "__main__":
    print("🚀 Starting Telegram Bot using Webhook...")

    PORT = int(os.environ.get("PORT", "10000"))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
