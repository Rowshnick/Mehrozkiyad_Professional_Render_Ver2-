import os
from telegram.ext import ApplicationBuilder, CommandHandler
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("ربات با وبهوک فعال است!")

app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))

async def webhook_handler(request):
    data = await request.json()
    await app_bot.update_queue.put(data)
    return web.Response(text="OK")

async def main():
    await app_bot.initialize()
    await app_bot.start()
    await app_bot.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        url_path=TOKEN,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )

    app = web.Application()
    app.add_routes([web.post(f"/{TOKEN}", webhook_handler)])
    return app

if __name__ == "__main__":
    web.run_app(main())
