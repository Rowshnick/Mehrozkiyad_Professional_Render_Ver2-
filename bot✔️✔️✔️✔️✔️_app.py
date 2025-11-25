import os
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# --- دریافت متغیرهای محیطی ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

# --- ایجاد برنامه تلگرام ---
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- import utils ---
try:
    from utils import astro, healing
except ImportError:
    print("وارد کردن ماژول utils انجام نشد. مطمئن شوید پوشه utils موجود است.")

# --- کیبورد اصلی ---
main_keyboard = [["/horoscope", "/healing"]]
reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

# --- مراحل گفتگو برای هوروسکوپ ---
DAY, MONTH, YEAR = range(3)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! ربات شما فعال شد.\nیک گزینه را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def horoscope_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً روز تولد خود را وارد کنید (عدد):", reply_markup=ReplyKeyboardRemove())
    return DAY

async def horoscope_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text
    await update.message.reply_text("لطفاً ماه تولد خود را وارد کنید (عدد):")
    return MONTH

async def horoscope_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = update.message.text
    await update.message.reply_text("لطفاً سال تولد خود را وارد کنید (میلادی):")
    return YEAR

async def horoscope_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = update.message.text
    day = context.user_data['day']
    month = context.user_data['month']
    year = context.user_data['year']

    # تولید هوروسکوپ با astro
    try:
        birth_date = f"{year}-{month}-{day}"
        horoscope = astro.get_horoscope(birth_date)
        await update.message.reply_text(f"هوروسکوپ شما:\n{horoscope}", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید هوروسکوپ: {e}", reply_markup=reply_markup)
    
    return ConversationHandler.END

async def horoscope_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات هوروسکوپ لغو شد.", reply_markup=reply_markup)
    return ConversationHandler.END

async def healing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = healing.get_healing_text()
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید متن درمانی: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام شما: {update.message.text}")

# --- ثبت Handlers ---
horoscope_conv = ConversationHandler(
    entry_points=[CommandHandler('horoscope', horoscope_start)],
    states={
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_day)],
        MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_month)],
        YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_year)]
    },
    fallbacks=[CommandHandler('cancel', horoscope_cancel)]
)

application.add_handler(CommandHandler("start", start))
application.add_handler(horoscope_conv)
application.add_handler(CommandHandler("healing", healing_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Flask App ---
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است!", 200

if __name__ == "__main__":
    url_path = WEBHOOK_URL.split("/")[-1]
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=url_path,
        webhook_url=WEBHOOK_URL
    )
