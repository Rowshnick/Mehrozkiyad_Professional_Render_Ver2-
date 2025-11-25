import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# --- دریافت متغیرهای محیطی ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # مثال: https://yourapp.onrender.com/webhook
PORT = int(os.environ.get("PORT", 10000))

# --- ایجاد برنامه تلگرام ---
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- import utils شما ---
try:
    from utils import astro, healing
except ImportError:
    print("وارد کردن ماژول utils انجام نشد. مطمئن شوید پوشه utils موجود است.")

# --- تعریف Handler ها ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات شما فعال شد.")

async def horoscope_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # مثال گرفتن هوروسکوپ از utils
    birth_date = update.message.text  # اینجا می‌توانید تاریخ را از پیام بگیرید
    try:
        horoscope = astro.get_horoscope(birth_date)
        await update.message.reply_text(horoscope)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید هوروسکوپ: {e}")

async def healing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # مثال گرفتن متن درمانی از utils
    try:
        message = healing.get_healing_text()
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید متن درمانی: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام شما: {update.message.text}")

# --- ثبت Handler ها ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("horoscope", horoscope_handler))
application.add_handler(CommandHandler("healing", healing_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Flask App برای Webhook ---
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    """مسیر webhook تلگرام"""
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است!", 200

# --- اجرای webhook ---
if __name__ == "__main__":
    # نام مسیر webhook برای run_webhook
    url_path = WEBHOOK_URL.split("/")[-1]
    
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=url_path,
        webhook_url=WEBHOOK_URL
    )
