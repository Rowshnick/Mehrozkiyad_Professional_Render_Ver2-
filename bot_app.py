import os
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from persiantools.jdatetime import JalaliDate

# --- دریافت متغیرهای محیطی ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

# --- ایجاد برنامه تلگرام ---
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- import utils شما ---
try:
    from utils import astro, healing
except ImportError:
    print("ماژول utils یافت نشد.")

# --- حالت‌های conversation ---
SELECT_CALENDAR, SELECT_YEAR, SELECT_MONTH, SELECT_DAY = range(4)

# --- منوهای پیش‌فرض ---
shamsi_years = [str(y) for y in range(1350, 1406)]  # نمونه سال‌ها
miladi_years = [str(y) for y in range(1970, 2026)]
months = [str(m) for m in range(1, 13)]
days = [str(d) for d in range(1, 32)]

# --- تابع شروع /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("هجری شمسی"), KeyboardButton("میلادی")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("سلام! لطفا نوع تقویم خود را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_CALENDAR

# --- انتخاب تقویم ---
async def select_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calendar = update.message.text
    context.user_data['calendar'] = calendar
    if calendar == "هجری شمسی":
        keyboard = [shamsi_years[i:i+5] for i in range(0, len(shamsi_years), 5)]
    else:
        keyboard = [miladi_years[i:i+5] for i in range(0, len(miladi_years), 5)]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("سال تولد خود را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_YEAR

# --- انتخاب سال ---
async def select_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = int(update.message.text)
    keyboard = [months[i:i+3] for i in range(0, len(months), 3)]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("ماه تولد خود را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_MONTH

# --- انتخاب ماه ---
async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['month'] = int(update.message.text)
    keyboard = [days[i:i+7] for i in range(0, len(days), 7)]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("روز تولد خود را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_DAY

# --- انتخاب روز و نمایش هوروسکوپ ---
async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = int(update.message.text)
    cal = context.user_data['calendar']
    y, m, d = context.user_data['year'], context.user_data['month'], context.user_data['day']
    
    # تبدیل شمسی به میلادی
    if cal == "هجری شمسی":
        try:
            g_date = JalaliDate(y, m, d).to_gregorian()
            y, m, d = g_date.year, g_date.month, g_date.day
        except Exception as e:
            await update.message.reply_text(f"خطا در تبدیل تاریخ: {e}")
            return ConversationHandler.END
    
    try:
        horoscope = astro.get_horoscope(f"{y}-{m}-{d}")
        await update.message.reply_text(f"هوروسکوپ شما:\n{horoscope}")
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید هوروسکوپ: {e}")
    
    return ConversationHandler.END

# --- cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# --- handler هوروسکوپ ---
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('horoscope', start)],
    states={
        SELECT_CALENDAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_calendar)],
        SELECT_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_year)],
        SELECT_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_month)],
        SELECT_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_day)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
application.add_handler(conv_handler)

# --- healing و echo ---
async def healing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = healing.get_healing_text()
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید متن درمانی: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام شما: {update.message.text}")

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

# --- اجرای webhook ---
if __name__ == "__main__":
    url_path = WEBHOOK_URL.split("/")[-1]
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=url_path,
        webhook_url=WEBHOOK_URL
    )
