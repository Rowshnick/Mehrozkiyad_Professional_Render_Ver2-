import os
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, ConversationHandler, filters
)
from utils import astro, healing

# -----------------------------------
# Load environment variables
# -----------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ BOT_TOKEN یا WEBHOOK_URL در env تنظیم نشده است.")

# -----------------------------------
# Logging
# -----------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------
# Conversation states
# -----------------------------------
SELECT_LANGUAGE, ENTER_YEAR, ENTER_MONTH, ENTER_DAY = range(4)

# -----------------------------------
# /start
# -----------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="fa"),
        InlineKeyboardButton("🇬🇧 English", callback_data="en")
    ]]
    await update.message.reply_text(
        "لطفاً زبان مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_LANGUAGE

# -----------------------------------
# Handle language selection
# (CallbackQuery OR Text fallback)
# -----------------------------------
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # --- If user pressed Inline button ---
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        lang = query.data
        context.user_data["lang"] = lang

        if lang == "fa":
            await query.edit_message_text("زبان انتخاب شد: فارسی\n\nسال تولد را وارد کنید:")
        else:
            await query.edit_message_text("Language selected: English\n\nEnter your birth year:")

        return ENTER_YEAR

    # --- If user typed the language manually (fallback) ---
    text = update.message.text.strip()
    lang = "fa" if "فارسی" in text else "en"
    context.user_data["lang"] = lang

    if lang == "fa":
        await update.message.reply_text("زبان انتخاب شد: فارسی\n\nسال تولد را وارد کنید:")
    else:
        await update.message.reply_text("Language selected.\nEnter your birth year:")

    return ENTER_YEAR

# -----------------------------------
# Enter year
# -----------------------------------
async def enter_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = update.message.text
    lang = context.user_data.get("lang", "fa")

    if lang == "fa":
        await update.message.reply_text("ماه تولد را وارد کنید:")
    else:
        await update.message.reply_text("Enter birth month:")
    return ENTER_MONTH

# -----------------------------------
# Enter month
# -----------------------------------
async def enter_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["month"] = update.message.text
    lang = context.user_data.get("lang", "fa")

    if lang == "fa":
        await update.message.reply_text("روز تولد را وارد کنید:")
    else:
        await update.message.reply_text("Enter birth day:")
    return ENTER_DAY

# -----------------------------------
# Enter day + final calculations
# -----------------------------------
async def enter_day(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["day"] = update.message.text
    lang = context.user_data.get("lang", "fa")

    # Astro + Healing (unchanged)
    astro_result = astro.get_prediction(context.user_data)
    healing_result = healing.suggest_sigil(context.user_data)

    if lang == "fa":
        header = f"🔮 تاریخ ثبت شد: {context.user_data['year']}-{context.user_data['month']}-{context.user_data['day']}\n\n"
    else:
        header = f"🔮 Date received: {context.user_data['year']}-{context.user_data['month']}-{context.user_data['day']}\n\n"

    await update.message.reply_text(header + astro_result + "\n\n" + healing_result)

    return ConversationHandler.END

# -----------------------------------
# /health for testing
# -----------------------------------
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Health OK ✔ Bot is running.")

# -----------------------------------
# MAIN
# -----------------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            SELECT_LANGUAGE: [
                CallbackQueryHandler(language_choice),
                MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice)
            ],
            ENTER_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_year)],
            ENTER_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_month)],
            ENTER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_day)],
        },

        fallbacks=[CommandHandler("start", start)],
        per_message=True    # برای جلوگیری از باگ CallbackQuery
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("health", health))

    # -------------------------
    # Webhook (Render)
    # -------------------------
    PORT = int(os.environ.get("PORT", 8000))
    WEBHOOK_PATH = "/webhook"
    WEBHOOK_FULL_URL = WEBHOOK_URL + WEBHOOK_PATH

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_FULL_URL
    )


if __name__ == "__main__":
    main()
