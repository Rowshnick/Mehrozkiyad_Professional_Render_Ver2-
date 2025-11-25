import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from persiantools.jdatetime import JalaliDate

# --- دریافت متغیرهای محیطی ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

# --- import utils ---
try:
    from utils import astro, healing
except ImportError:
    print("وارد کردن ماژول utils انجام نشد. مطمئن شوید پوشه utils موجود است.")

# --- تعریف مراحل ConversationHandler ---
CALENDAR, YEAR, MONTH, DAY = range(4)
calendar_type = {}  # ذخیره انتخاب کاربر
birth_data = {}     # ذخیره سال/ماه/روز انتخابی

# --- کیبورد ها ---
sh_years = [[str(y)] for y in range(1350, 1406)]
gr_years = [[str(y)] for y in range(1920, 2026)]
months = [[str(i)] for i in range(1, 13)]
days = [[str(i)] for i in range(1, 32)]
calendar_keyboard = ReplyKeyboardMarkup([["شمسی", "میلادی"]], one_time_keyboard=True, resize_keyboard=True)
sh_year_keyboard = ReplyKeyboardMarkup(sh_years, one_time_keyboard=True, resize_keyboard=True)
gr_year_keyboard = ReplyKeyboardMarkup(gr_years, one_time_keyboard=True, resize_keyboard=True)
month_keyboard = ReplyKeyboardMarkup(months, one_time_keyboard=True, resize_keyboard=True)
day_keyboard = ReplyKeyboardMarkup(days, one_time_keyboard=True, resize_keyboard=True)

# --- تبدیل شمسی به میلادی ---
def sh_to_gr(year, month, day):
    return JalaliDate(year=int(year), month=int(month), day=int(day)).to_gregorian()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! برای دریافت هوروسکوپ، ابتدا تقویم خود را انتخاب کنید:", reply_markup=calendar_keyboard)
    return CALENDAR

async def calendar_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    calendar_type[user_id] = update.message.text
    if calendar_type[user_id] == "شمسی":
        await update.message.reply_text("سال تولد خود را انتخاب کنید:", reply_markup=sh_year_keyboard)
    else:
        await update.message.reply_text("سال تولد خود را انتخاب کنید:", reply_markup=gr_year_keyboard)
    return YEAR

async def year_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    birth_data[user_id] = {"year": update.message.text}
    await update.message.reply_text("ماه تولد خود را انتخاب کنید:", reply_markup=month_keyboard)
    return MONTH

async def month_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    birth_data[user_id]["month"] = update.message.text
    await update.message.reply_text("روز تولد خود را انتخاب کنید:", reply_markup=day_keyboard)
    return DAY

async def day_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    birth_data[user_id]["day"] = update.message.text

    # تبدیل به میلادی در صورت نیاز
    if calendar_type[user_id] == "شمسی":
        g_date = sh_to_gr(int(birth_data[user_id]["year"]),
                          int(birth_data[user_id]["month"]),
                          int(birth_data[user_id]["day"]))
    else:
        g_date = (int(birth_data[user_id]["year"]),
                  int(birth_data[user_id]["month"]),
                  int(birth_data[user_id]["day"]))

    # تولید هوروسکوپ
    try:
        horoscope = astro.get_horoscope(g_date)
    except Exception as e:
        horoscope = f"خطا در تولید هوروسکوپ: {e}"

    await update.message.reply_text(f"هوروسکوپ شما:\n{horoscope}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

async def healing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = healing.get_healing_text()
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"خطا در تولید متن درمانی: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام شما: {update.message.text}")

# --- ایجاد Application ---
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- ثبت ConversationHandler ---
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('horoscope', start)],
    states={
        CALENDAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, calendar_choice)],
        YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year_choice)],
        MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, month_choice)],
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, day_choice)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("healing", healing_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Flask App ---
from flask import Flask, request, jsonify
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
