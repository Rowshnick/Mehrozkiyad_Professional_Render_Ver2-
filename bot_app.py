import os
import logging
from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler, CallbackQueryHandler
)
from utils import astro, healing  # فرض بر این است که پوشه utils کامل و بدون تغییر باشد

# -------------------------------
# تنظیمات اصلی
# -------------------------------
BOT_TOKEN = "8555233519:AAFeKZgy4xGYjl_ibUEmVuC7HHv-Eo0FCww"
WEBHOOK_URL = "https://mehrozkiyad-professional-render-ver2.onrender.com"

# -------------------------------
# حالت‌های گفتگو
# -------------------------------
SELECT_LANGUAGE, ENTER_YEAR, ENTER_MONTH, ENTER_DAY = range(4)

# -------------------------------
# هندلرها
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # نمونه کد انتخاب زبان
    keyboard = [["فارسی", "English"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("لطفا زبان را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_LANGUAGE

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=f"زبان انتخاب شد: {user_choice}")
    return ENTER_YEAR

async def enter_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = update.message.text
    await update.message.reply_text("لطفا ماه را وارد کنید:")
    return ENTER_MONTH

async def enter_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = update.message.text
    await update.message.reply_text("لطفا روز را وارد کنید:")
    return ENTER_DAY

async def enter_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text
    await update.message.reply_text(
        f"تاریخ شما ثبت شد: {context.user_data['year']}-{context.user_data['month']}-{context.user_data['day']}"
    )
    # فراخوانی توابع astro و healing برای پیشگویی
    result = astro.get_prediction(context.user_data)
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

    # Health check
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
        webhook_url=WEBHOOK_FULL_URL
    )


if __name__ == "__main__":
    main()
