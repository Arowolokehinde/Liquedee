import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TimedOut, NetworkError, RetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.core.dexscreener_massive import MassiveDexScreenerClient
from src.core.liquidity_analyzer import LiquidityAnalyzer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OptimizedLiquidityBot:
    """Optimized Telegram Bot with proper error handling and /quick focus"""
    
    def __init__(self, token: str):
        self.token = token
        
        # Build application with timeout settings
        self.application = (Application.builder()
                          .token(token)
                          .concurrent_updates(True)
                          .build())
        
        self.scheduler = AsyncIOScheduler()
        
        # Bot state
        self.is_monitoring = False
        self.subscribers = set()
        self.user_settings = {}
        self.last_scan_time = None
        self.last_opportunities = []
        
        # SNIFFER settings - optimized for fresh tokens
        self.default_settings = {
            'min_liquidity': 500,        # $500 - catch very early tokens
            'min_volume': 50,            # $50 - initial activity
            'max_age_hours': 72,         # 72 hours - fresh tokens only
            'alert_interval': 15,
            'max_alerts': 15,            # More results for sniffer
            'min_confidence': 0.2,       # Lower threshold for fresh tokens
            'max_scan_pairs': 500,       # Scan more pairs
            'quick_scan': True,
            'prioritize_fresh': True     # New flag for freshness priority
        }
        
        self.setup_handlers()
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors gracefully"""
        logger.error(f"Exception while handling update: {context.error}")
        
        # If it's a timeout, try to inform the user
        if isinstance(context.error, TimedOut):
            if update and hasattr(update, 'effective_chat'):
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ **Connection timeout** - Please try /quick again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    logger.error("Failed to send timeout error message")
        
        # If it's a retry after error, wait and retry
        elif isinstance(context.error, RetryAfter):
            logger.info(f"Rate limited, waiting {context.error.retry_after} seconds")
            await asyncio.sleep(context.error.retry_after)
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("quick", self.quick_scan_command))
        self.application.add_handler(CommandHandler("scan", self.scan_disabled_command))
        self.application.add_handler(CommandHandler("alerts", self.alerts_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("token", self.token_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def safe_send_message(self, update: Update, text: str, reply_markup=None, max_retries: int = 3):
        """Safely send message with retry logic"""
        for attempt in range(max_retries):
            try:
                return await update.message.reply_text(
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except (TimedOut, NetworkError) as e:
                logger.warning(f"Send message attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Final attempt without markdown
                    try:
                        return await update.message.reply_text(
                            text.replace("**", "").replace("*", ""),
                            reply_markup=reply_markup
                        )
                    except Exception as final_error:
                        logger.error(f"Failed to send message after all retries: {final_error}")
                        return None
    
    async def safe_edit_message(self, message, text: str, max_retries: int = 3):
        """Safely edit message with retry logic"""
        for attempt in range(max_retries):
            try:
                return await message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            except (TimedOut, NetworkError) as e:
                logger.warning(f"Edit message attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    # Final attempt without markdown
                    try:
                        return await message.edit_text(text.replace("**", "").replace("*", ""))
                    except Exception as final_error:
                        logger.error(f"Failed to edit message after all retries: {final_error}")
                        return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message focused on /quick"""
        user_id = update.effective_user.id
        self.user_settings[user_id] = self.default_settings.copy()
        
        welcome_text = """
🎯 **TOKEN SNIFFER BOT**

Hunt for FRESH Solana tokens before they moon!

**🔥 WHAT I DO:**
• Find tokens < 72 hours old
• Detect early volume spikes
• Score by freshness + momentum
• Skip established tokens

**⚡ MAIN COMMANDS:**
/quick - Fresh token hunt ⭐ START HERE
/alerts - Latest fresh finds
/help - Full help

**🎯 Ready to snipe alpha? Try /quick now!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Hunt Fresh Tokens", callback_data="quick_scan")],
            [InlineKeyboardButton("📚 Help", callback_data="help")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.safe_send_message(update, welcome_text, reply_markup)
    
    async def quick_scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fresh token sniffer scan with robust error handling"""
        user_id = update.effective_user.id
        settings = self.user_settings.get(user_id, self.default_settings)
        
        # Send initial message
        scan_msg = await self.safe_send_message(
            update,
            "🎯 **TOKEN SNIFFER SCAN STARTING...**\n\n"
            "🔍 Hunting for fresh tokens (<72h old)...\n"
            "🚀 Looking for early opportunities...\n"
            "⏳ ETA: ~45 seconds..."
        )
        
        try:
            # Run the scan
            opportunities = await self.run_quick_scan(settings)
            
            if opportunities:
                result_text = self.format_opportunities(opportunities[:settings['max_alerts']])
                final_text = f"🎯 **SNIFFER SCAN COMPLETE**\n\n{result_text}"
                
                # Try to edit, fallback to new message
                if scan_msg:
                    success = await self.safe_edit_message(scan_msg, final_text)
                    if not success:
                        await self.safe_send_message(update, final_text)
                else:
                    await self.safe_send_message(update, final_text)
                
                self.last_opportunities = opportunities
                self.last_scan_time = datetime.now()
                
            else:
                no_results_text = (
                    "😔 **NO FRESH TOKENS FOUND**\n\n"
                    "No new tokens (<72h) with activity right now.\n"
                    "Fresh launches happen frequently - try again soon!"
                )
                
                if scan_msg:
                    success = await self.safe_edit_message(scan_msg, no_results_text)
                    if not success:
                        await self.safe_send_message(update, no_results_text)
                else:
                    await self.safe_send_message(update, no_results_text)
                
        except Exception as e:
            logger.error(f"Quick scan error: {e}")
            error_text = (
                "❌ **SNIFFER SCAN FAILED**\n\n"
                "Something went wrong. Please try /quick again.\n"
                "If the problem persists, the bot may be under heavy load."
            )
            
            if scan_msg:
                success = await self.safe_edit_message(scan_msg, error_text)
                if not success:
                    await self.safe_send_message(update, error_text)
            else:
                await self.safe_send_message(update, error_text)
    
    async def run_quick_scan(self, settings: Dict) -> List[Dict]:
        """Fresh token sniffer scan - prioritize new opportunities"""
        scanner = MassiveDexScreenerClient()
        analyzer = LiquidityAnalyzer()
        
        try:
            # Get all pairs for comprehensive sniffer analysis
            pairs = await scanner.get_latest_pairs()
            
            # Use full analyzer for better fresh token detection
            fresh_opportunities = []
            
            for raw_pair in pairs[:settings['max_scan_pairs']]:
                parsed = scanner.parse_pair_data(raw_pair)
                if not parsed:
                    continue
                
                # Age filter - only fresh tokens
                age_hours = parsed.get('age_hours')
                if age_hours is not None and age_hours > settings['max_age_hours']:
                    continue
                
                # Basic liquidity/volume filter
                if (parsed['total_liquidity_usd'] >= settings['min_liquidity'] and
                    parsed['volume_24h_usd'] >= settings['min_volume']):
                    
                    # Use full analyzer for proper scoring
                    alert = await analyzer.analyze_pair(parsed)
                    if alert and alert.get('combined_score', 0) >= settings['min_confidence']:
                        fresh_opportunities.append(alert)
            
            # Sort by combined score (opportunity + freshness)
            fresh_opportunities.sort(
                key=lambda x: x.get('combined_score', 0), 
                reverse=True
            )
            
            return fresh_opportunities
            
        except Exception as e:
            logger.error(f"Error in run_quick_scan: {e}")
            return []
        finally:
            await scanner.close()
    
    def calculate_freshness_priority_score(self, parsed: Dict) -> float:
        """Freshness-priority scoring for sniffer mode"""
        score = 0.0
        age_hours = parsed.get('age_hours')
        
        # Age is the primary factor
        if age_hours is not None:
            if age_hours <= 1:      # Brand new
                score += 0.5
            elif age_hours <= 6:    # Very fresh
                score += 0.4
            elif age_hours <= 12:   # Fresh
                score += 0.3
            elif age_hours <= 24:   # New
                score += 0.2
            elif age_hours <= 48:   # Recent
                score += 0.1
            elif age_hours <= 72:   # Still acceptable
                score += 0.05
        
        # Volume-to-liquidity ratio (momentum indicator)
        vol_to_liq = parsed.get('volume_to_liquidity_ratio', 0)
        if vol_to_liq >= 5.0:       # High momentum
            score += 0.3
        elif vol_to_liq >= 2.0:     # Good momentum
            score += 0.2
        elif vol_to_liq >= 1.0:     # Some momentum
            score += 0.1
        
        # Activity level
        txns = parsed['txns_24h']
        if txns >= 100:
            score += 0.2
        elif txns >= 50:
            score += 0.15
        elif txns >= 20:
            score += 0.1
        elif txns >= 10:
            score += 0.05
        
        return min(score, 1.0)
    
    def format_opportunities(self, opportunities: List[Dict]) -> str:
        """Format fresh token opportunities for Telegram"""
        if not opportunities:
            return "No fresh opportunities found matching your criteria."
        
        text = f"**🎯 TOP {len(opportunities)} FRESH TOKENS:**\n\n"
        
        for i, opp in enumerate(opportunities, 1):
            # Emoji based on freshness and alert type
            alert_type = opp.get('alert_type', '')
            if 'BRAND_NEW' in alert_type:
                emoji = "🆕"
            elif 'VIRAL' in alert_type or 'TRENDING' in alert_type:
                emoji = "🚀"
            elif 'FRESH' in alert_type:
                emoji = "🌟"
            elif opp.get('combined_score', 0) >= 0.6:
                emoji = "📈"
            else:
                emoji = "💡"
            
            age_hours = opp.get('age_hours')
            if age_hours is not None:
                if age_hours < 1:
                    age_str = f"{age_hours*60:.0f}min"
                else:
                    age_str = f"{age_hours:.1f}h"
            else:
                age_str = "unknown"
            
            # Show key sniffer metrics
            text += f"{emoji} **{i}. {opp['base_symbol']}/{opp['quote_symbol']}**\n"
            text += f"   🕐 **{age_str} old** | 📍 {opp['dex_name']}\n"
            text += f"   💰 ${opp['liquidity_usd']:,.0f} liquidity\n"
            text += f"   📊 ${opp['volume_24h_usd']:,.0f} volume\n"
            
            # Show freshness and combined scores
            freshness_score = opp.get('freshness_score', 0)
            combined_score = opp.get('combined_score', 0)
            text += f"   ⚡ {freshness_score:.2f} fresh | 🎯 {combined_score:.2f} total\n"
            
            # Show momentum indicators
            vol_to_liq = opp.get('volume_to_liquidity_ratio', 0)
            if vol_to_liq > 0:
                text += f"   🔥 {vol_to_liq:.1f}x turnover"
            
            if opp.get('price_change_24h'):
                text += f" | 📈 {opp['price_change_24h']:+.1f}%"
            text += "\n\n"
        
        text += f"🕐 Sniffer scan at {datetime.now().strftime('%H:%M UTC')}"
        return text
    
    async def scan_disabled_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Redirect /scan to /quick"""
        await self.safe_send_message(
            update,
            "🔄 **REDIRECTING TO QUICK SCAN**\n\n"
            "/scan has been replaced with /quick for better performance!\n"
            "Starting quick scan now..."
        )
        # Automatically run quick scan
        await self.quick_scan_command(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help message"""
        help_text = """
📚 **TOKEN SNIFFER BOT - HELP**

**🎯 WHAT I DO:**
• Hunt for tokens < 72 hours old
• Find early volume spikes & momentum
• Skip old, established tokens
• Score by freshness + growth potential

**⚡ MAIN COMMANDS:**
/quick - Fresh token hunt (~45 sec) ⭐
/alerts - Show latest fresh finds
/start - Welcome message

**🚨 COMING SOON:**
/subscribe - Auto-alerts for fresh launches
/settings - Configure age/volume thresholds
/token <address> - Deep dive analysis

**💡 SNIFFER TIPS:**
- Focuses on tokens under 3 days old
- Higher scores = fresher + more momentum
- Look for high turnover ratios (volume/liquidity)
- Brand new tokens (<1h) get priority

**🎯 SNIFFER WORKFLOW:**
1. /quick (hunt fresh opportunities)
2. Check age & momentum scores
3. Research promising finds
4. Act fast on early opportunities

**🚀 Ready to snipe? Try /quick now!**
        """
        
        await self.safe_send_message(update, help_text)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard buttons"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "quick_scan":
            # Create fake update for quick scan
            fake_update = Update(
                update_id=query.id,
                message=query.message
            )
            await self.quick_scan_command(fake_update, context)
        elif query.data == "help":
            await query.edit_message_text(
                "📚 **HELP**\n\nUse /quick for fast scans!\n"
                "Type /help for full command list.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif query.data == "settings":
            await query.edit_message_text(
                "⚙️ **SETTINGS**\n\n"
                "Current: Smart defaults active\n"
                "Custom settings coming soon!",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # Stub methods for other commands
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show latest alerts"""
        if self.last_opportunities:
            count = len(self.last_opportunities)
            scan_time = self.last_scan_time.strftime('%H:%M UTC') if self.last_scan_time else "unknown"
            await self.safe_send_message(
                update,
                f"📊 **LATEST SCAN RESULTS**\n\n"
                f"🔥 Found {count} opportunities\n"
                f"🕐 Last scan: {scan_time}\n\n"
                f"💡 Use /quick for fresh results!"
            )
        else:
            await self.safe_send_message(
                update,
                "📊 **NO RECENT SCANS**\n\n"
                "⚡ Use /quick to scan for opportunities!"
            )
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Subscribe to alerts"""
        await self.safe_send_message(
            update,
            "🚨 **AUTO-ALERTS COMING SOON!**\n\n"
            "For now, use /quick for manual scans.\n"
            "🔄 Each scan finds fresh opportunities!"
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show sniffer settings"""
        await self.safe_send_message(
            update,
            "⚙️ **SNIFFER SETTINGS**\n\n"
            "💰 Min Liquidity: $500 (catch early)\n"
            "📊 Min Volume: $50 (initial activity)\n"
            "⏰ Max Age: 72 hours (fresh only)\n"
            "🎯 Max Results: 15\n"
            "🚀 Freshness Priority: Enabled\n\n"
            "🔧 Custom thresholds coming soon!"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show sniffer stats"""
        scan_count = "recent" if self.last_scan_time else "none"
        fresh_count = len([o for o in self.last_opportunities if o.get('age_hours', 999) <= 24]) if self.last_opportunities else 0
        
        await self.safe_send_message(
            update,
            f"📊 **SNIFFER STATS**\n\n"
            f"🎯 Status: Hunting fresh tokens\n"
            f"🕐 Last Hunt: {scan_count}\n"
            f"⚡ Hunt Speed: ~45 seconds\n"
            f"🆕 Fresh Finds (<24h): {fresh_count}\n"
            f"🚀 Mode: Freshness priority\n\n"
            f"💡 Try /quick to hunt for alpha!"
        )
    
    async def token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze token"""
        await self.safe_send_message(
            update,
            "🔍 **TOKEN ANALYSIS**\n\n"
            "Feature coming soon!\n"
            "📊 Use /quick to see all opportunities."
        )
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unsubscribe"""
        await self.safe_send_message(update, "🛑 **UNSUBSCRIBED**\n\nNo active subscriptions.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show status"""
        await self.safe_send_message(
            update,
            "📱 **BOT STATUS**\n\n"
            "🟢 Online and ready\n"
            "⚡ Quick scan available\n"
            "🔄 Use /quick to start scanning!"
        )
    
    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting Optimized Liquidity Sniffer Bot...")
        logger.info("⚡ Primary command: /quick")
        logger.info("🔧 Enhanced error handling enabled")
        
        # Start polling with reasonable timeouts
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            timeout=20,
            read_timeout=25,
            write_timeout=25,
            connect_timeout=10,
            pool_timeout=5
        )

# Main execution
if __name__ == "__main__":
    print("🤖 LIQUIDITY SNIFFER BOT STARTUP")
    print("=" * 50)
    
    # Try to get token from environment first
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("📝 Bot token not found in environment.")
        print("💡 You can:")
        print("   1. Set TELEGRAM_BOT_TOKEN environment variable")
        print("   2. Add it to your .env file")
        print("   3. Enter it below")
        print()
        print("🔑 Enter your Telegram Bot Token:")
        try:
            BOT_TOKEN = input("Token: ").strip()
        except KeyboardInterrupt:
            print("\n🛑 Canceled by user")
            sys.exit(0)
    
    if not BOT_TOKEN:
        print("❌ Bot token is required!")
        print("💡 Get your token from @BotFather on Telegram")
        sys.exit(1)
    
    print(f"✅ Token received: {BOT_TOKEN[:10]}...")
    print("🚀 Starting bot with enhanced error handling...")
    
    try:
        bot = OptimizedLiquidityBot(BOT_TOKEN)
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")