import os
import logging
from datetime import datetime
from telegram import (
    ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler, CallbackQueryHandler
)
from utils import astro, healing  # بدون تغییر

# -------------------------------
# تنظیمات اصلی
# -------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")   # ← از ENV خوانده می‌شود
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # ← از ENV خوانده می‌شود

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN در محیط Render تنظیم نشده است")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL در محیط Render تنظیم نشده است")

# -------------------------------
# حالت‌های گفتگو
# -------------------------------
SELECT_LANGUAGE, ENTER_YEAR, ENTER_MONTH, ENTER_DAY = range(4)

# -------------------------------
# هندلر استارت
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("فارسی", callback_data="fa"),
            InlineKeyboardButton("English", callback_data="en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفا زبان را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_LANGUAGE

# -------------------------------
# انتخاب زبان
# -------------------------------
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data
    context.user_data["lang"] = lang

    if lang == "fa":
        await query.edit_message_text("زبان انتخاب شد: فارسی\n\nلطفا سال تولد را وارد کنید:")
    else:
        await query.edit_message_text("Language selected: English\n\nEnter your birth year:")

    return ENTER_YEAR

# -------------------------------
# سال
# -------------------------------
async def enter_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = update.message.text
    await update.message.reply_text("لطفا ماه را وارد کنید:")
    return ENTER_MONTH

# -------------------------------
# ماه
# -------------------------------
async def enter_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = update.message.text
    await update.message.reply_text("لطفا روز را وارد کنید:")
    return ENTER_DAY

# -------------------------------
# روز + پیشگویی
# -------------------------------
async def enter_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text

    # ساخت تاریخ
    year = context.user_data["year"]
    month = context.user_data["month"]
    day = context.user_data["day"]

    await update.message.reply_text(f"تاریخ شما ثبت شد: {year}-{month}-{day}")

    # پیشگویی اصلی
    result = astro.get_prediction(context.user_data)

    # سیجل هندی / healing
    healing_result = healing.suggest_sigil(context.user_data)

    await update.message.reply_text(f"{result}\n\n{healing_result}")

    return ConversationHandler.END

# -------------------------------
# Main
# -------------------------------
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANGUAGE: [CallbackQueryHandler(language_choice)],
            ENTER_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_year)],
            ENTER_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_month)],
            ENTER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_day)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Health OK - Bot is running ✔")

    application.add_handler(CommandHandler("health", health))

    # -----------------------------
    # Webhook config (Render)
    # -----------------------------
    PORT = int(os.environ.get("PORT", 8000))
    WEBHOOK_PATH = "/webhook"
    WEBHOOK_FULL_URL = WEBHOOK_URL + WEBHOOK_PATH

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_FULL_URL,
    )


if __name__ == "__main__":
    main()
