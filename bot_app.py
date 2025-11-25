import os
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, CallbackContext
from utils import astro, healing  # ماژول‌های شما بدون تغییر

# -----------------------
# تنظیمات پایه
# -----------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # حتما توکن در Render ENV قرار بگیرد
if not TOKEN:
    raise ValueError("توکن ربات در متغیر محیطی TELEGRAM_BOT_TOKEN تعریف نشده است!")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dp = Dispatcher(bot=bot, update_queue=None, use_context=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------
# دستورها و هندلرها
# -----------------------

def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! ربات آماده است.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("راهنما: از دستورات موجود استفاده کنید.")

def handle_text(update: Update, context: CallbackContext):
    text = update.message.text
    # اینجا می‌توانید تابع astro یا healing را صدا بزنید
    response = f"پیام شما دریافت شد: {text}"
    update.message.reply_text(response)

# ثبت هندلرها
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help_command))
dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# -----------------------
# Webhook Flask
# -----------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dp.process_update(update)
        return "ok", 200

# -----------------------
# مسیر تست ساده
# -----------------------
@app.route('/')
def index():
    return "Bot is running", 200

# -----------------------
# اجرای برنامه
# -----------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
