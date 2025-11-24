import os
import logging
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from utils import astro, healing  # همان ماژول‌های اصلی شما

# ------------------ Logging ------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------ TELEGRAM TOKEN ------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN در متغیرهای محیطی تنظیم نشده است.")

# ------------------ Flask App ------------------
app = Flask(__name__)

# ------------------ Telegram Bot Application ------------------
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ------------------ ConversationHandler States ------------------
CHOOSING, TYPING = range(2)

# ----- Entry Point -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("گزینه ۱", callback_data='1')],
        [InlineKeyboardButton("گزینه ۲", callback_data='2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! یک گزینه انتخاب کنید یا پیام خود را ارسال کنید:",
        reply_markup=reply_markup
    )
    return CHOOSING

# ----- CallbackQueryHandler برای انتخاب گزینه -----
async def handle_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selection = query.data
    # پاسخ هوشمند بر اساس گزینه
    response_text = f"شما گزینه {selection} را انتخاب کردید. پاسخ هوشمند: ..."
    await query.edit_message_text(response_text)
    return CHOOSING

# ----- MessageHandler برای متن آزاد -----
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # پاسخ هوشمند بر اساس متن
    response_text = f"شما پیام فرستادید: {text}\nپاسخ هوشمند: ..."
    await update.message.reply_text(response_text)
    return CHOOSING

# ----- Cancel / fallback -----
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 گفتگو خاتمه یافت.")
    return ConversationHandler.END

# ------------------ ConversationHandler ------------------
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING: [
            CallbackQueryHandler(handle_option),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    per_message=False
)

application.add_handler(conv_handler)

# ------------------ Webhook Route ------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    """دریافت آپدیت از تلگرام و پردازش آن"""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return Response("ok", status=200)
    else:
        return Response("Method not allowed", status=405)

# ------------------ Start Flask + Telegram ------------------
if __name__ == "__main__":
    WEBHOOK_URL = os.environ.get(
        "WEBHOOK_URL",
        "https://mehrozkiyad-professional-render-ver2.onrender.com/webhook"
    )

    # ثبت webhook در تلگرام
    import asyncio

    async def set_webhook():
        await application.bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook set to: {WEBHOOK_URL}")

    asyncio.run(set_webhook())

    # شروع background task برای پردازش آپدیت‌ها
    from threading import Thread
    Thread(target=lambda: application.run_polling(), daemon=True).start()

    # اجرا Flask روی Render
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
