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

# -----------------------------
#  دریافت متغیرهای محیطی Render
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

# -----------------------------
#  ساخت اپلیکیشن تلگرام (بدون Dispatcher)
# -----------------------------
application = ApplicationBuilder().token(BOT_TOKEN).build()

# -----------------------------
#  ایمپورت utils (بدون تغییر)
# -----------------------------
try:
    from utils import astro, healing
except Exception as e:
    print("خطا در ایمپورت utils:", e)

# -----------------------------
#  تعریف هندلرها
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! ربات شما فعال شد.\n"
        "می‌توانید پیام بفرستید یا از فرمان‌ها استفاده کنید."
    )

async def horoscope_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        birth_text = update.message.text.strip()
        result = astro.get_horoscope(birth_text)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید هوروسکوپ: {e}")

async def healing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = healing.get_healing_text()
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید پیام درمانی: {e}")

# --- پیام آزاد + انتخاب گزینه و همزمان پاسخ هوشمند ---
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"پیام شما دریافت شد:\n{user_text}")

# -----------------------------
#  ثبت هندلرها
# -----------------------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("horoscope", horoscope_handler))
application.add_handler(CommandHandler("healing", healing_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# -----------------------------
#  Flask → Webhook endpoint
# -----------------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        print("خطا در پردازش وب‌هوک:", e)
    return jsonify({"ok": True})

# -----------------------------
#  اجرای Webhook روی Render
# -----------------------------
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )
