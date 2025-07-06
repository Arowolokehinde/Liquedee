#!/usr/bin/env python3
"""
Launch the Liquidity Sniffer Telegram Bot
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.telegram_bot.bot import LiquiditySnifferBot

if __name__ == "__main__":
    print("🚀 LIQUIDITY SNIFFER TELEGRAM BOT")
    print("=" * 50)

    # Get bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("📝 Enter your Telegram Bot Token:")
        print("   (Get it from @BotFather on Telegram)")
        bot_token = input("Token: ").strip()

    if not bot_token:
        print("❌ Bot token is required!")
        sys.exit(1)

    # Start bot
    try:
        bot = LiquiditySnifferBot(bot_token)
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
