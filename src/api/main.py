import os
import sys
from threading import Thread

import uvicorn
from fastapi import FastAPI

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

app = FastAPI(title="Liquedee Bot API", version="1.0.0")


@app.get("/")
async def root():
    return {"status": "healthy", "service": "liquedee-bot-api"}


@app.get("/health")
async def health():
    return {"status": "ok", "bot_status": "running"}


@app.get("/api/v1/status")
async def api_status():
    return {"api": "active", "telegram_bot": "running"}


def run_telegram_bot():
    """Run the Telegram bot in a separate thread"""
    try:
        from src.telegram_bot.bot_realtime import RealtimeSnifferBot

        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        if BOT_TOKEN:
            print("🤖 Starting Telegram bot...")
            bot = RealtimeSnifferBot(BOT_TOKEN)
            bot.run()
        else:
            print("⚠️ No TELEGRAM_BOT_TOKEN found, skipping bot startup")
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")
        import traceback
        traceback.print_exc()


# Start bot when module is imported (not just when run as main)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if BOT_TOKEN:
    print("🚀 Starting Telegram bot thread...")
    bot_thread = Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    print("✅ Telegram bot thread started")
else:
    print("⚠️ No TELEGRAM_BOT_TOKEN found")


if __name__ == "__main__":
    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
