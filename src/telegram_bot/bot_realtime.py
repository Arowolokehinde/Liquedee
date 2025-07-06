"""
Enhanced Telegram Bot with Real-time Blockchain Monitoring
Offers both DexScreener scanning and direct blockchain monitoring
"""
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

from src.core.liquidity_analyzer import LiquidityAnalyzer
from src.core.simple_realtime_sniffer import SimpleSnifferFactory
from src.core.lightweight_scanner import FastSnifferBot
from src.core.gem_hunter import GemHunterScanner
from src.core.live_discovery_feed import LiveDiscoveryScanner
from src.core.goodbuy_analyzer import GoodBuyAnalyzer
from src.core.alpha_scanner import AlphaScanner

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RealtimeSnifferBot:
    """Enhanced Token Sniffer Bot with Real-time Blockchain Monitoring"""
    
    def __init__(self, token: str):
        self.token = token
        
        # Build application
        self.application = (Application.builder()
                          .token(token)
                          .concurrent_updates(True)
                          .build())
        
        self.scheduler = AsyncIOScheduler()
        
        # Bot state
        self.is_monitoring = False
        self.realtime_monitoring = False
        self.subscribers = set()
        self.realtime_subscribers = set()
        self.user_settings = {}
        self.last_scan_time = None
        self.last_opportunities = []
        self.fresh_blockchain_pairs = []
        
        # Sniffer components
        self.realtime_sniffer = None
        self.fast_scanner = FastSnifferBot()
        self.gem_hunter = GemHunterScanner()
        self.live_discovery = LiveDiscoveryScanner()
        self.goodbuy_analyzer = GoodBuyAnalyzer()
        self.alpha_scanner = AlphaScanner()
        
        # Enhanced settings
        self.default_settings = {
            'min_liquidity': 500,
            'min_volume': 50,
            'max_age_hours': 72,
            'alert_interval': 15,
            'max_alerts': 15,
            'min_confidence': 0.2,
            'max_scan_pairs': 100,  # Reduced for faster scanning
            'realtime_enabled': False,
            'blockchain_monitoring': False
        }
        
        self.setup_handlers()
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors gracefully"""
        logger.error(f"Exception while handling update: {context.error}")
        
        if isinstance(context.error, TimedOut):
            if update and hasattr(update, 'effective_chat'):
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ **Connection timeout** - Please try again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    logger.error("Failed to send timeout error message")
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Scanning commands
        self.application.add_handler(CommandHandler("quick", self.quick_scan_command))
        self.application.add_handler(CommandHandler("realtime", self.realtime_scan_command))
        self.application.add_handler(CommandHandler("blockchain", self.blockchain_scan_command))
        self.application.add_handler(CommandHandler("goodbuy", self.goodbuy_command))
        self.application.add_handler(CommandHandler("alpha", self.alpha_command))
        
        # Original commands
        self.application.add_handler(CommandHandler("scan", self.scan_disabled_command))
        self.application.add_handler(CommandHandler("alerts", self.alerts_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("token", self.token_command))
        
        # Subscription commands
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("subscribe_realtime", self.subscribe_realtime_command))
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
                    await asyncio.sleep(2 ** attempt)
                else:
                    try:
                        return await update.message.reply_text(
                            text.replace("**", "").replace("*", ""),
                            reply_markup=reply_markup
                        )
                    except Exception as final_error:
                        logger.error(f"Failed to send message after all retries: {final_error}")
                        return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced welcome message with multiple scan options"""
        user_id = update.effective_user.id
        self.user_settings[user_id] = self.default_settings.copy()
        
        welcome_text = """
🔥 **SOL SNIPER BOT - COMPLETE CRYPTO HUNTER**

**🚀 QUICK START (3 Steps):**
1. `/blockchain` - Start monitoring
2. `/subscribe_realtime` - Enable alerts  
3. `/quick` or `/alpha` - Hunt opportunities

**🏆 MAIN COMMANDS:**
💎 `/quick` - **Gem Hunt** (Ultra-strict Solana gems, ~20s)
🚀 `/realtime` - **Fresh Discoveries** (More opportunities, ~15s)
🔥 `/alpha` - **Multi-Chain Trending** (7 chains, volume leaders, ~25s)
🔍 `/goodbuy <address>` - **Safety Analysis** (Rug risk check, ~30s)

**📡 MONITORING & ALERTS:**
🔗 `/blockchain` - Live monitoring (scans every minute)
🔔 `/subscribe_realtime` - Instant fresh token alerts
📊 `/status` - Check your alert settings

**💡 SMART WORKFLOW:**
1. **Discover**: Use `/quick`, `/realtime`, or `/alpha`
2. **Analyze**: Always run `/goodbuy <address>` before investing
3. **Monitor**: Keep `/blockchain` + alerts active
4. **Invest**: Based on safety analysis only

**⚠️ SAFETY FIRST:** Never invest without `/goodbuy` analysis!

**🔥 Hunt smart, invest safer!**
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 Gem Hunt", callback_data="quick_scan")],
            [InlineKeyboardButton("🚀 Discovery Feed", callback_data="realtime_scan")],
            [InlineKeyboardButton("🔥 Alpha Trending", callback_data="alpha_scan")],
            [InlineKeyboardButton("🔍 Safety Analysis", callback_data="goodbuy_help")],
            [InlineKeyboardButton("🔗 Live Monitor", callback_data="blockchain_scan")],
            [InlineKeyboardButton("📚 Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.safe_send_message(update, welcome_text, reply_markup)
    
    async def quick_scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gem hunter scan - strict criteria for finding true gems"""
        user_id = update.effective_user.id
        settings = self.user_settings.get(user_id, self.default_settings)
        
        scan_msg = await self.safe_send_message(
            update,
            "💎 **GEM HUNT ACTIVE**\n\n"
            "🔍 Hunting gems: <72h, ≥$2k liq, 200% spike, $5k-500k cap\n"
            "📊 Scanning: DexScreener + DEX Factory + Pump.fun\n"
            "⏳ ETA: ~20 seconds..."
        )
        
        try:
            # Use gem hunter for strict gem discovery
            gems = await self.gem_hunter.hunt_gems(max_gems=settings['max_alerts'])
            
            if gems:
                result_text = self.format_gem_opportunities(gems, "GemHunt")
                final_text = f"💎 **GEM HUNT COMPLETE**\n\n{result_text}"
                
                await self.safe_edit_message(scan_msg, final_text)
                self.last_opportunities = gems
                self.last_scan_time = datetime.now()
                
            else:
                # Fallback: Show top 3 newest tokens + nudge to /realtime
                newest = await self.gem_hunter.get_newest_tokens_fallback(3)
                if newest:
                    fallback_text = self.format_gem_opportunities(newest, "Newest")
                    final_text = (
                        f"💎 **NO GEMS FOUND**\n\n"
                        f"No tokens met gem criteria (<72h, ≥$2k liq, 200% spike)\n\n"
                        f"**🕐 TOP 3 NEWEST AVAILABLE:**\n{fallback_text}\n\n"
                        f"💡 Try /realtime or /blockchain for fresh monitoring!"
                    )
                else:
                    final_text = (
                        f"💎 **NO GEMS FOUND**\n\n"
                        f"No tokens met gem criteria (<72h, ≥$2k liq, 200% spike)\n\n"
                        f"📊 **No fresh Solana tokens under 72h found**\n"
                        f"Market is quiet right now on Solana.\n\n"
                        f"💡 Try /realtime for more opportunities or /alpha for multi-chain trending!"
                    )
                
                await self.safe_edit_message(scan_msg, final_text)
                
        except Exception as e:
            logger.error(f"Gem hunt error: {e}")
            await self.safe_edit_message(
                scan_msg,
                "❌ **GEM HUNT FAILED**\n\n"
                "Error occurred. Try /realtime or /blockchain methods."
            )
    
    async def realtime_scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Live Discovery Feed - more opportunities with moderate criteria"""
        scan_msg = await self.safe_send_message(
            update,
            "🚀 **LIVE DISCOVERY FEED**\n\n"
            "📡 Scanning: Recent + Pump + DEX + Trending\n"
            "🎯 Criteria: <24h, ≥$1k liq, 100% spike, $1k-1M cap\n"
            "⏳ Finding fresh opportunities (~15s)..."
        )
        
        try:
            # Use live discovery scanner for more opportunities
            discoveries = await self.live_discovery.scan_live_discoveries(max_discoveries=15)
            
            if discoveries:
                result_text = self.format_discovery_opportunities(discoveries, "LiveFeed")
                final_text = f"🚀 **LIVE DISCOVERIES FOUND**\n\n{result_text}"
                
                await self.safe_edit_message(scan_msg, final_text)
                self.fresh_blockchain_pairs = discoveries
                
            else:
                await self.safe_edit_message(
                    scan_msg,
                    "📡 **NO LIVE DISCOVERIES**\n\n"
                    "No tokens met discovery criteria (<24h, ≥$1k liq, 100% spike).\n"
                    "Try /quick for strict gem hunting or /blockchain monitoring."
                )
                
        except Exception as e:
            logger.error(f"Live discovery scan error: {e}")
            await self.safe_edit_message(
                scan_msg,
                "❌ **LIVE DISCOVERY FAILED**\n\n"
                "Error during discovery scan.\n"
                "Use /quick for gem hunting or /blockchain for monitoring."
            )
    
    async def goodbuy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comprehensive safety and quality analysis for token investment"""
        # Check if token address provided
        if not context.args:
            await self.safe_send_message(
                update,
                "🔍 **GOODBUY ANALYSIS**\n\n"
                "Please provide a token address:\n"
                "`/goodbuy <token_address>`\n\n"
                "**Example:**\n"
                "`/goodbuy So11111111111111111111111111111111111111112`\n\n"
                "**What GoodBuy analyzes:**\n"
                "🔒 Safety (rug risk, locks, ownership)\n"
                "📊 Market Health (liquidity, volume, holders)\n"
                "🚀 Momentum (spikes, trends, ratios)\n"
                "👑 Distribution (whales, concentration)"
            )
            return
        
        token_address = context.args[0].strip()
        
        # Validate token address format (basic check)
        if len(token_address) < 40:
            await self.safe_send_message(
                update,
                "❌ **INVALID TOKEN ADDRESS**\n\n"
                "Please provide a valid Solana token address.\n"
                "Address should be 44 characters long."
            )
            return
        
        analysis_msg = await self.safe_send_message(
            update,
            "🔍 **GOODBUY ANALYSIS STARTING**\n\n"
            f"🎯 Token: `{token_address}`\n\n"
            "📊 Running comprehensive analysis:\n"
            "• 🔒 Safety checks (rug risk)\n"
            "• 📊 Market health validation\n"
            "• 🚀 Momentum analysis\n"
            "• 👑 Distribution review\n\n"
            "⏳ ETA: ~30 seconds..."
        )
        
        try:
            # Run comprehensive GoodBuy analysis
            analysis = await self.goodbuy_analyzer.analyze_token_goodbuy(token_address)
            
            # Format the analysis results
            result_text = self.format_goodbuy_analysis(analysis)
            
            await self.safe_edit_message(analysis_msg, result_text)
            
        except Exception as e:
            logger.error(f"GoodBuy analysis error: {e}")
            await self.safe_edit_message(
                analysis_msg,
                "❌ **GOODBUY ANALYSIS FAILED**\n\n"
                "Error occurred during analysis.\n"
                "Please check the token address and try again."
            )
    
    async def blockchain_scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start direct blockchain monitoring"""
        scan_msg = await self.safe_send_message(
            update,
            "🔗 **ENHANCED MONITORING**\n\n"
            "🚀 Starting enhanced fresh token detection...\n"
            "📡 Will scan for tokens < 3 hours old every minute\n"
            "⏳ Setting up monitoring system..."
        )
        
        try:
            if not self.realtime_monitoring:
                # Start blockchain monitoring
                await self.start_blockchain_monitoring()
                
                await self.safe_edit_message(
                    scan_msg,
                    "🔗 **ENHANCED MONITORING ACTIVE**\n\n"
                    "✅ Now scanning for fresh tokens every minute!\n"
                    "📊 Detecting tokens < 3 hours old\n"
                    "🔔 Use /subscribe_realtime for auto-alerts\n\n"
                    "💡 Use /realtime to see fresh discoveries"
                )
            else:
                await self.safe_edit_message(
                    scan_msg,
                    "🔗 **ENHANCED MONITORING ACTIVE**\n\n"
                    "✅ Already scanning for fresh tokens!\n"
                    "📊 Use /realtime to see fresh discoveries\n"
                    "🔔 Use /subscribe_realtime for auto-alerts"
                )
                
        except Exception as e:
            logger.error(f"Blockchain monitoring error: {e}")
            await self.safe_edit_message(
                scan_msg,
                "❌ **BLOCKCHAIN MONITORING FAILED**\n\n"
                "Error starting real-time monitoring.\n"
                "This feature requires stable RPC connection."
            )
    
    async def alpha_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run alpha trending tokens scan across chains"""
        alpha_msg = await self.safe_send_message(
            update,
            "🔥 **ALPHA TRENDING SCAN**\n\n"
            "🌐 Scanning trending tokens across all chains...\n"
            "📊 Analyzing volume leaders, price spikes, social trends\n"
            "🎯 Finding daily curated alpha gems\n\n"
            "⏳ ETA: ~25 seconds..."
        )
        
        try:
            # Run alpha gem scanning
            alpha_gems = await self.alpha_scanner.scan_alpha_gems(max_gems=15)
            
            if alpha_gems:
                # Format results
                result_text = self.format_alpha_results(alpha_gems)
                await self.safe_edit_message(alpha_msg, result_text)
            else:
                await self.safe_edit_message(
                    alpha_msg,
                    "🔥 **ALPHA SCAN COMPLETE**\n\n"
                    "📊 No trending alpha gems found meeting criteria right now.\n"
                    "🌐 Market conditions may be quiet across chains.\n\n"
                    "💡 Try again later or use /realtime for fresh opportunities!"
                )
                
        except Exception as e:
            logger.error(f"Alpha scan error: {e}")
            await self.safe_edit_message(
                alpha_msg,
                "❌ **ALPHA SCAN FAILED**\n\n"
                "Error occurred during multi-chain scanning.\n"
                "Please try again in a few moments."
            )
    
    async def start_blockchain_monitoring(self):
        """Start the real-time blockchain monitoring system"""
        if self.realtime_monitoring:
            return
        
        try:
            # Create simplified realtime sniffer (more reliable)
            self.realtime_sniffer = SimpleSnifferFactory.create_enhanced_sniffer()
            
            # Start monitoring in background
            self.realtime_monitoring = True
            monitoring_task = asyncio.create_task(
                self.realtime_sniffer.start_comprehensive_monitoring(
                    callback=self.handle_fresh_pair_discovery
                )
            )
            
            logger.info("🚀 Real-time blockchain monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting blockchain monitoring: {e}")
            self.realtime_monitoring = False
            raise
    
    async def handle_fresh_pair_discovery(self, pair_info: Dict):
        """Handle discovery of a fresh pair from blockchain monitoring"""
        logger.info(f"🆕 Fresh pair discovered: {pair_info.get('base_symbol', 'UNKNOWN')}")
        
        # Notify realtime subscribers
        if self.realtime_subscribers:
            alert_text = f"🆕 **FRESH PAIR DETECTED**\n\n"
            alert_text += self.format_single_opportunity(pair_info, "Blockchain-Live")
            
            for user_id in self.realtime_subscribers.copy():
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=alert_text,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Failed to send realtime alert to {user_id}: {e}")
                    if "blocked" in str(e).lower():
                        self.realtime_subscribers.discard(user_id)
    
    async def trigger_fresh_realtime_scan(self) -> List[Dict]:
        """Trigger immediate fresh scan for realtime monitoring"""
        try:
            if not self.realtime_sniffer:
                return []
            
            # Force fresh scan instead of using cached data
            from ..core.simple_realtime_sniffer import SimpleSnifferFactory
            temp_sniffer = SimpleSnifferFactory.create_enhanced_sniffer()
            
            # Scan for very recent pairs (< 3 hours)
            fresh_pairs = await temp_sniffer.get_ultra_fresh_pairs()
            
            # Also get any new discoveries
            all_fresh = await temp_sniffer.get_all_fresh_pairs()
            fresh_pairs.extend(all_fresh)
            
            # Remove duplicates and sort by freshness
            unique_pairs = []
            seen_addresses = set()
            
            for pair in fresh_pairs:
                address = pair.get('pair_address', '')
                if address and address not in seen_addresses:
                    seen_addresses.add(address)
                    unique_pairs.append(pair)
            
            # Sort by age (newest first)
            unique_pairs.sort(key=lambda x: x.get('age_hours', 999))
            
            return unique_pairs[:15]
            
        except Exception as e:
            logger.error(f"Error in fresh realtime scan: {e}")
            return []
    
    async def get_realtime_fresh_pairs(self) -> List[Dict]:
        """Get fresh pairs from realtime monitoring (legacy method)"""
        return await self.trigger_fresh_realtime_scan()
    
    async def run_quick_scan(self, settings: Dict) -> List[Dict]:
        """Fast scan using lightweight scanner - completes in 10-15 seconds"""
        try:
            # Use the fast scanner instead of the blocking MassiveDexScreenerClient
            fresh_opportunities = await self.fast_scanner.quick_scan(
                max_results=settings['max_alerts']
            )
            
            return fresh_opportunities
            
        except Exception as e:
            logger.error(f"Fast scan error: {e}")
            return []
    
    def format_opportunities(self, opportunities: List[Dict], source: str) -> str:
        """Format opportunities with source indicator"""
        if not opportunities:
            return f"No opportunities found from {source}."
        
        text = f"**🎯 TOP {len(opportunities)} FROM {source.upper()}:**\n\n"
        
        for i, opp in enumerate(opportunities, 1):
            text += self.format_single_opportunity(opp, source, i)
            text += "\n"
        
        text += f"🕐 Scan completed at {datetime.now().strftime('%H:%M UTC')}"
        return text
    
    def format_gem_opportunities(self, gems: List[Dict], source: str) -> str:
        """Format gem opportunities with enhanced display"""
        if not gems:
            return f"No gems found from {source}."
        
        text = f"**💎 TOP {len(gems)} GEMS FROM {source.upper()}:**\n\n"
        
        for i, gem in enumerate(gems, 1):
            text += self.format_single_gem(gem, source, i)
            text += "\n"
        
        text += f"🕐 Gem hunt completed at {datetime.now().strftime('%H:%M UTC')}"
        return text
    
    def format_discovery_opportunities(self, discoveries: List[Dict], source: str) -> str:
        """Format discovery opportunities with discovery-focused display"""
        if not discoveries:
            return f"No discoveries found from {source}."
        
        text = f"**🚀 TOP {len(discoveries)} DISCOVERIES FROM {source.upper()}:**\n\n"
        
        for i, discovery in enumerate(discoveries, 1):
            text += self.format_single_discovery(discovery, source, i)
            text += "\n"
        
        text += f"🕐 Discovery scan completed at {datetime.now().strftime('%H:%M UTC')}"
        return text
    
    def format_goodbuy_analysis(self, analysis: Dict) -> str:
        """Format comprehensive GoodBuy analysis results"""
        token_address = analysis.get('token_address', 'Unknown')
        overall_score = analysis.get('overall_score', 0)
        recommendation = analysis.get('recommendation', 'UNKNOWN')
        risk_level = analysis.get('risk_level', 'HIGH')
        
        # Header with overall result
        if recommendation == 'STRONG BUY':
            rec_emoji = "🟢"
        elif recommendation == 'BUY':
            rec_emoji = "🟡"
        elif recommendation == 'CAUTION':
            rec_emoji = "🟠"
        else:
            rec_emoji = "🔴"
        
        if risk_level == 'LOW':
            risk_emoji = "🟢"
        elif risk_level == 'MEDIUM':
            risk_emoji = "🟡"
        else:
            risk_emoji = "🔴"
        
        text = f"🔍 **GOODBUY ANALYSIS COMPLETE**\n\n"
        text += f"🎯 **Token:** `{token_address}`\n"
        text += f"📊 **Overall Score:** {overall_score:.1f}/10\n"
        text += f"{rec_emoji} **Recommendation:** {recommendation}\n"
        text += f"{risk_emoji} **Risk Level:** {risk_level}\n\n"
        
        # Detailed scores
        safety_score = analysis.get('safety_score', 0)
        market_score = analysis.get('market_health_score', 0)
        momentum_score = analysis.get('momentum_score', 0)
        distribution_score = analysis.get('distribution_score', 0)
        
        text += f"📋 **DETAILED SCORES:**\n"
        text += f"🔒 Safety: {safety_score:.1f}/10\n"
        text += f"📊 Market Health: {market_score:.1f}/10\n"
        text += f"🚀 Momentum: {momentum_score:.1f}/10\n"
        text += f"👑 Distribution: {distribution_score:.1f}/10\n\n"
        
        # Good signs
        good_signs = analysis.get('good_signs', [])
        if good_signs:
            text += f"✅ **GOOD SIGNS:**\n"
            for sign in good_signs[:5]:  # Show top 5
                text += f"• {sign}\n"
            text += "\n"
        
        # Red flags
        red_flags = analysis.get('red_flags', [])
        if red_flags:
            text += f"🚨 **RED FLAGS:**\n"
            for flag in red_flags[:5]:  # Show top 5
                text += f"• {flag}\n"
            text += "\n"
        
        # Warnings
        warnings = analysis.get('warnings', [])
        if warnings:
            text += f"⚠️ **WARNINGS:**\n"
            for warning in warnings[:3]:  # Show top 3
                text += f"• {warning}\n"
            text += "\n"
        
        # Key metrics summary
        market_health = analysis.get('market_health', {}).get('metrics', {})
        momentum_analysis = analysis.get('momentum_analysis', {}).get('metrics', {})
        
        text += f"📊 **KEY METRICS:**\n"
        
        liquidity = market_health.get('liquidity_usd', 0)
        if liquidity > 0:
            text += f"💧 Liquidity: ${liquidity:,.0f}\n"
        
        market_cap = market_health.get('market_cap_usd', 0)
        if market_cap > 0:
            text += f"💰 Market Cap: ${market_cap:,.0f}\n"
        
        volume_24h = market_health.get('volume_24h_usd', 0)
        if volume_24h > 0:
            text += f"🔄 24h Volume: ${volume_24h:,.0f}\n"
        
        volume_spike = momentum_analysis.get('volume_spike_percent', 0)
        if volume_spike > 0:
            text += f"📈 Volume Spike: {volume_spike:.0f}%\n"
        
        buy_sell_ratio = momentum_analysis.get('buy_sell_ratio', 0)
        if buy_sell_ratio > 0:
            text += f"🟢 Buy/Sell Ratio: {buy_sell_ratio:.1f}:1\n"
        
        # Links for verification
        text += f"\n🔗 **VERIFICATION LINKS:**\n"
        text += f"📊 DexScreener: https://dexscreener.com/solana/{token_address}\n"
        text += f"🔍 Solscan: https://solscan.io/token/{token_address}\n"
        text += f"🐦 Birdeye: https://birdeye.so/token/{token_address}\n"
        
        # Investment recommendation
        text += f"\n💡 **INVESTMENT GUIDANCE:**\n"
        if recommendation == 'STRONG BUY':
            text += f"• High confidence investment opportunity\n"
            text += f"• Low risk with good upside potential\n"
            text += f"• Consider larger position size\n"
        elif recommendation == 'BUY':
            text += f"• Solid investment opportunity\n"
            text += f"• Moderate risk with good potential\n"
            text += f"• Standard position size recommended\n"
        elif recommendation == 'CAUTION':
            text += f"• Proceed with extreme caution\n"
            text += f"• High risk, potential reward uncertain\n"
            text += f"• Small position size only\n"
        else:
            text += f"• Do not invest at this time\n"
            text += f"• Too many risk factors present\n"
            text += f"• Wait for better opportunities\n"
        
        text += f"\n🕐 Analysis completed at {datetime.now().strftime('%H:%M UTC')}"
        text += f"\n\n⚠️ **Disclaimer:** This is analysis only, not financial advice. DYOR!"
        
        return text
    
    def format_alpha_results(self, alpha_gems: List[Dict]) -> str:
        """Format alpha trending tokens results"""
        text = f"🔥 **ALPHA TRENDING GEMS**\n"
        text += f"🌐 Multi-chain curated daily gems\n\n"
        text += f"📊 Found {len(alpha_gems)} trending opportunities\n"
        text += f"🕐 Scanned at {datetime.now().strftime('%H:%M UTC')}\n\n"
        
        # Group by alpha type for better presentation
        mega_alphas = [g for g in alpha_gems if g.get('alpha_type') == 'MEGA_ALPHA']
        strong_alphas = [g for g in alpha_gems if g.get('alpha_type') == 'STRONG_ALPHA']
        solid_alphas = [g for g in alpha_gems if g.get('alpha_type') == 'SOLID_ALPHA']
        emerging_alphas = [g for g in alpha_gems if g.get('alpha_type') == 'EMERGING_ALPHA']
        
        # Show mega alphas first
        if mega_alphas:
            text += f"🌟 **MEGA ALPHA GEMS** ({len(mega_alphas)})\n"
            for i, gem in enumerate(mega_alphas[:3], 1):
                text += self.format_single_alpha_gem(gem, i)
            text += "\n"
        
        # Show strong alphas
        if strong_alphas:
            text += f"🔥 **STRONG ALPHA GEMS** ({len(strong_alphas)})\n"
            for i, gem in enumerate(strong_alphas[:4], 1):
                text += self.format_single_alpha_gem(gem, i)
            text += "\n"
        
        # Show solid alphas
        if solid_alphas:
            text += f"⚡ **SOLID ALPHA GEMS** ({len(solid_alphas)})\n"
            for i, gem in enumerate(solid_alphas[:5], 1):
                text += self.format_single_alpha_gem(gem, i)
            text += "\n"
        
        # Show emerging alphas (if space)
        if emerging_alphas and len(text) < 3500:
            text += f"🌱 **EMERGING ALPHAS** ({len(emerging_alphas)})\n"
            for i, gem in enumerate(emerging_alphas[:3], 1):
                text += self.format_single_alpha_gem(gem, i)
            text += "\n"
        
        # Summary stats
        total_volume = sum(gem.get('volume_24h_usd', 0) for gem in alpha_gems[:10])
        avg_gain = sum(gem.get('price_change_24h', 0) for gem in alpha_gems[:10]) / min(len(alpha_gems), 10)
        
        text += f"📈 **ALPHA SUMMARY:**\n"
        text += f"💰 Total Volume: ${total_volume:,.0f}\n"
        text += f"📊 Avg 24h Gain: {avg_gain:+.1f}%\n"
        text += f"🌐 Chains: {len(set(gem.get('chain', 'unknown') for gem in alpha_gems))}\n"
        
        text += f"\n💡 **ALPHA STRATEGY:**\n"
        text += f"• Focus on volume leaders with momentum\n"
        text += f"• Check social trends and community strength\n"
        text += f"• Diversify across multiple chains\n"
        text += f"• Use /goodbuy <address> for safety analysis\n"
        
        text += f"\n⚠️ **Disclaimer:** Alpha gems are high-risk, high-reward. DYOR!"
        
        return text
    
    def format_single_alpha_gem(self, gem: Dict, index: int) -> str:
        """Format a single alpha gem"""
        alpha_type = gem.get('alpha_type', 'EMERGING_ALPHA')
        if alpha_type == 'MEGA_ALPHA':
            emoji = "🌟"
        elif alpha_type == 'STRONG_ALPHA':
            emoji = "🔥"
        elif alpha_type == 'SOLID_ALPHA':
            emoji = "⚡"
        else:
            emoji = "🌱"
        
        chain = gem.get('chain', 'unknown').upper()
        chain_emoji = self.get_chain_emoji(chain)
        
        age_days = gem.get('age_days', 999)
        if age_days < 1:
            age_str = f"{age_days*24:.0f}h"
        else:
            age_str = f"{age_days:.1f}d"
        
        result = f"{emoji} **{index}. {gem.get('base_symbol', 'UNKNOWN')}/{gem.get('quote_symbol', 'UNKNOWN')}**\n"
        result += f"   {chain_emoji} {chain} | 🕐 {age_str} old | 📍 {gem.get('dex_name', 'unknown')}\n"
        
        # Key metrics
        volume_24h = gem.get('volume_24h_usd', 0)
        if volume_24h > 0:
            result += f"   💰 ${volume_24h:,.0f} volume (24h)\n"
        
        price_change = gem.get('price_change_24h', 0)
        if price_change != 0:
            result += f"   📈 {price_change:+.1f}% (24h)\n"
        
        market_cap = gem.get('market_cap_usd', 0)
        if market_cap > 0:
            result += f"   🏷️ ${market_cap:,.0f} market cap\n"
        
        alpha_score = gem.get('alpha_score', 0)
        if alpha_score > 0:
            result += f"   🔥 {alpha_score:.1f}/10 alpha score\n"
        
        social_mentions = gem.get('social_mentions', 0)
        if social_mentions > 10:
            result += f"   🐦 {social_mentions} social mentions\n"
        
        # Links
        pair_address = gem.get('pair_address', '')
        base_token = gem.get('base_token', '')
        chain_lower = chain.lower()
        
        if pair_address:
            result += f"   📊 [DexScreener](https://dexscreener.com/{chain_lower}/{pair_address})\n"
        
        if base_token:
            result += f"   🔍 Token: `{base_token}`\n"
        
        result += "\n"
        return result
    
    def get_chain_emoji(self, chain: str) -> str:
        """Get emoji for blockchain"""
        chain_emojis = {
            'SOLANA': '☀️',
            'ETHEREUM': '💎',
            'BSC': '🟡',
            'POLYGON': '🟣',
            'ARBITRUM': '🔵',
            'AVALANCHE': '🔴',
            'BASE': '🔷',
            'UNKNOWN': '🌐'
        }
        return chain_emojis.get(chain.upper(), '🌐')
    
    def format_single_opportunity(self, opp: Dict, source: str, index: int = None) -> str:
        """Format a single opportunity"""
        # Emoji based on source and freshness
        if "blockchain" in source.lower():
            emoji = "🆕"
        elif opp.get('age_hours', 999) <= 1:
            emoji = "🚀"
        elif opp.get('age_hours', 999) <= 6:
            emoji = "🌟"
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
        
        result = ""
        if index:
            result += f"{emoji} **{index}. {opp.get('base_symbol', 'UNKNOWN')}/{opp.get('quote_symbol', 'SOL')}**\n"
        else:
            result += f"{emoji} **{opp.get('base_symbol', 'UNKNOWN')}/{opp.get('quote_symbol', 'SOL')}**\n"
        
        result += f"   🕐 **{age_str} old** | 📍 {opp.get('dex_name', 'unknown')}\n"
        result += f"   💰 ${opp.get('liquidity_usd', 0):,.0f} liquidity\n"
        result += f"   📊 ${opp.get('volume_24h_usd', 0):,.0f} volume\n"
        
        # Show scores if available
        freshness_score = opp.get('freshness_score')
        combined_score = opp.get('combined_score')
        if freshness_score and combined_score:
            result += f"   ⚡ {freshness_score:.2f} fresh | 🎯 {combined_score:.2f} total\n"
        
        # Show momentum indicators
        vol_to_liq = opp.get('volume_to_liquidity_ratio', 0)
        if vol_to_liq > 0:
            result += f"   🔥 {vol_to_liq:.1f}x turnover"
        
        price_change = opp.get('price_change_24h')
        if price_change:
            result += f" | 📈 {price_change:+.1f}%"
        
        result += f"\n   🔍 Source: {source.replace('_', '-')}"  # Fix markdown issue
        
        return result
    
    def format_single_gem(self, gem: Dict, source: str, index: int = None) -> str:
        """Format a single gem with enhanced gem-specific info"""
        # Gem emoji based on alert type
        alert_type = gem.get('alert_type', 'EMERGING_TOKEN')
        if alert_type == 'ULTRA_GEM':
            emoji = "💎"
        elif alert_type == 'POTENTIAL_GEM':
            emoji = "✨"
        else:
            emoji = "🌟"
        
        age_hours = gem.get('age_hours', 999)
        if age_hours < 1:
            age_str = f"{age_hours*60:.0f}min"
        elif age_hours < 24:
            age_str = f"{age_hours:.1f}h"
        else:
            age_str = f"{age_hours/24:.1f}d"
        
        result = ""
        if index:
            result += f"{emoji} **{index}. {gem.get('base_symbol', 'UNKNOWN')}/{gem.get('quote_symbol', 'SOL')}**\n"
        else:
            result += f"{emoji} **{gem.get('base_symbol', 'UNKNOWN')}/{gem.get('quote_symbol', 'SOL')}**\n"
        
        result += f"   🕐 **{age_str} old** | 📍 {gem.get('dex_name', 'unknown')}\n"
        result += f"   💰 ${gem.get('liquidity_usd', 0):,.0f} liquidity\n"
        result += f"   📊 ${gem.get('volume_24h_usd', 0):,.0f} volume (24h)\n"
        
        # Show gem-specific metrics
        mcap = gem.get('market_cap_usd', 0)
        if mcap > 0:
            result += f"   🏷️ ${mcap:,.0f} market cap\n"
        
        volume_spike = gem.get('volume_spike_percent', 0)
        if volume_spike > 0:
            result += f"   🔥 {volume_spike:.0f}% volume spike\n"
        
        gem_score = gem.get('gem_score', 0)
        if gem_score > 0:
            result += f"   💎 {gem_score:.1f}/10 gem score\n"
        
        # Show price change if available
        price_change = gem.get('price_change_24h', 0)
        if price_change != 0:
            result += f"   📈 {price_change:+.1f}% (24h)\n"
        
        result += f"   🔍 Source: {source.replace('_', '-')}\n"
        
        # Add critical verification info
        pair_address = gem.get('pair_address', '')
        base_token = gem.get('base_token', '')
        
        if pair_address:
            result += f"   🔗 Pair: `{pair_address}`\n"
            result += f"   📊 [DexScreener](https://dexscreener.com/solana/{pair_address})\n"
        
        if base_token:
            result += f"   🏷️ Token: `{base_token}`\n"
            result += f"   🔍 [Solscan](https://solscan.io/token/{base_token})"
        
        return result
    
    def format_single_discovery(self, discovery: Dict, source: str, index: int = None) -> str:
        """Format a single discovery with discovery-focused metrics"""
        # Discovery emoji based on type and freshness
        discovery_type = discovery.get('discovery_type', 'RECENT_LAUNCH')
        age_hours = discovery.get('age_hours', 999)
        
        if discovery_type == 'HOT_DISCOVERY':
            emoji = "🔥"
        elif discovery_type == 'FRESH_FIND':
            emoji = "🆕"
        elif discovery_type == 'NEW_OPPORTUNITY':
            emoji = "⚡"
        elif age_hours <= 1:
            emoji = "🚀"
        elif age_hours <= 6:
            emoji = "🌟"
        else:
            emoji = "💡"
        
        # Format age for readability
        if age_hours < 1:
            age_str = f"{age_hours*60:.0f}min"
        elif age_hours < 24:
            age_str = f"{age_hours:.1f}h"
        else:
            age_str = f"{age_hours/24:.1f}d"
        
        result = ""
        if index:
            result += f"{emoji} **{index}. {discovery.get('base_symbol', 'UNKNOWN')}/{discovery.get('quote_symbol', 'SOL')}**\n"
        else:
            result += f"{emoji} **{discovery.get('base_symbol', 'UNKNOWN')}/{discovery.get('quote_symbol', 'SOL')}**\n"
        
        result += f"   🕐 **{age_str} old** | 📍 {discovery.get('dex_name', 'unknown')}\n"
        result += f"   💰 ${discovery.get('liquidity_usd', 0):,.0f} liquidity\n"
        result += f"   📊 ${discovery.get('volume_24h_usd', 0):,.0f} volume (24h)\n"
        
        # Show discovery-specific metrics
        mcap = discovery.get('market_cap_usd', 0)
        if mcap > 0:
            if mcap >= 1000000:
                result += f"   🏷️ ${mcap/1000000:.1f}M market cap\n"
            elif mcap >= 1000:
                result += f"   🏷️ ${mcap/1000:.0f}k market cap\n"
            else:
                result += f"   🏷️ ${mcap:,.0f} market cap\n"
        
        # Volume activity (less strict than gem spike)
        volume_activity = discovery.get('volume_spike_percent', 0)
        if volume_activity > 0:
            result += f"   📈 {volume_activity:.0f}% activity spike\n"
        
        # Discovery score
        discovery_score = discovery.get('discovery_score', 0)
        if discovery_score > 0:
            result += f"   🚀 {discovery_score:.1f}/10 discovery score\n"
        
        # Show price change if available
        price_change = discovery.get('price_change_24h', 0)
        if price_change != 0:
            result += f"   💹 {price_change:+.1f}% (24h)\n"
        
        result += f"   🔍 Source: {source.replace('_', '-')}\n"
        
        # Add critical verification info (like gems)
        pair_address = discovery.get('pair_address', '')
        base_token = discovery.get('base_token', '')
        
        if pair_address:
            result += f"   🔗 Pair: `{pair_address}`\n"
            result += f"   📊 [DexScreener](https://dexscreener.com/solana/{pair_address})\n"
        
        if base_token:
            result += f"   🏷️ Token: `{base_token}`\n"
            result += f"   🔍 [Solscan](https://solscan.io/token/{base_token})"
        
        return result
    
    async def safe_edit_message(self, message, text: str, max_retries: int = 3):
        """Safely edit message with retry logic"""
        if not message:
            return None
            
        for attempt in range(max_retries):
            try:
                return await message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            except (TimedOut, NetworkError) as e:
                logger.warning(f"Edit message attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    try:
                        return await message.edit_text(text.replace("**", "").replace("*", ""))
                    except Exception as final_error:
                        logger.error(f"Failed to edit message after all retries: {final_error}")
                        return None
    
    # Additional command implementations (simplified versions)
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced help with multiple scan methods"""
        help_text = """
📚 **CRYPTO GEM HUNTER - HELP**

**🏆 QUAD SYSTEM COMMANDS:**
💎 /quick - **Gem Hunt**: Ultra-strict criteria (~20s)
🚀 /realtime - **Discovery Feed**: Moderate criteria (~15s)
🔥 /alpha - **Trending Alphas**: Multi-chain leaders (~25s)
🔍 /goodbuy - **Safety Analysis**: Comprehensive analysis (~30s)
🔗 /blockchain - **Live Monitor**: Background scanning

**📊 SYSTEM BREAKDOWN:**

**GEM HUNT (/quick):**
• Age: < 72h | Liquidity: ≥ $2k | Spike: ≥ 200%
• Result: Few ultra-quality verified gems

**DISCOVERY FEED (/realtime):**
• Age: < 24h | Liquidity: ≥ $1k | Spike: ≥ 100%  
• Result: More fresh opportunities to explore

**ALPHA TRENDING (/alpha):**
• Multi-chain volume leaders, price spikes, social trends
• Result: Daily curated alpha gems across all chains

**SAFETY ANALYSIS (/goodbuy):**
• Usage: `/goodbuy <token_address>`
• Checks: Rug risk, market health, momentum, distribution
• Result: Investment recommendation with risk assessment

**🔔 ALERT SUBSCRIPTIONS:**
/subscribe - Auto-alerts for discoveries
/subscribe_realtime - Instant fresh alerts

**💡 OPTIMAL STRATEGY:**
1. Find: Use /quick, /realtime, or /alpha
2. Analyze: Use /goodbuy before investing
3. Monitor: Use /blockchain + subscribe
4. Invest: Based on safety analysis

**🔥 Hunt alpha, invest smart!**
        """
        
        await self.safe_send_message(update, help_text)
    
    async def subscribe_realtime_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Subscribe to real-time blockchain alerts"""
        user_id = update.effective_user.id
        self.realtime_subscribers.add(user_id)
        
        await self.safe_send_message(
            update,
            "🚀 **REALTIME ALERTS ENABLED**\n\n"
            "✅ You'll receive instant alerts when fresh pairs are detected via blockchain monitoring!\n\n"
            "📡 Make sure blockchain monitoring is active: /blockchain\n"
            "🔄 Use /realtime to see current discoveries\n"
            "🛑 Use /unsubscribe to stop all alerts"
        )
    
    # Placeholder implementations for other commands
    async def scan_disabled_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.safe_send_message(update, "🔄 Use /quick, /realtime, or /blockchain instead!")
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.safe_send_message(update, "📊 Use /quick or /realtime for fresh results!")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        monitoring_status = "🟢 Active" if self.realtime_monitoring else "🔴 Inactive"
        await self.safe_send_message(
            update,
            f"⚙️ **SNIFFER SETTINGS**\n\n"
            f"💰 Min Liquidity: $500\n"
            f"📊 Min Volume: $50\n"
            f"⏰ Max Age: 72 hours\n"
            f"🔗 Blockchain Monitor: {monitoring_status}\n\n"
            f"🔧 Use /blockchain to start monitoring"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        realtime_count = len(self.fresh_blockchain_pairs)
        monitoring_status = "🟢 Active" if self.realtime_monitoring else "🔴 Inactive"
        
        await self.safe_send_message(
            update,
            f"📊 **REALTIME SNIFFER STATS**\n\n"
            f"🔗 Blockchain Monitor: {monitoring_status}\n"
            f"🆕 Fresh Discoveries: {realtime_count}\n"
            f"📡 Realtime Subscribers: {len(self.realtime_subscribers)}\n"
            f"⚡ DexScreener Subscribers: {len(self.subscribers)}\n\n"
            f"💡 Try /blockchain to start monitoring!"
        )
    
    async def token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.safe_send_message(update, "🔍 Token analysis coming soon! Use /quick for opportunities.")
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.subscribers.add(user_id)
        await self.safe_send_message(update, "🚨 DexScreener alerts enabled!")
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.subscribers.discard(user_id)
        self.realtime_subscribers.discard(user_id)
        await self.safe_send_message(update, "🛑 All alerts disabled!")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        is_subscribed = user_id in self.subscribers
        is_realtime_subscribed = user_id in self.realtime_subscribers
        monitoring_status = "🟢 Active" if self.realtime_monitoring else "🔴 Inactive"
        
        await self.safe_send_message(
            update,
            f"📱 **YOUR STATUS**\n\n"
            f"🚨 DexScreener Alerts: {'🟢' if is_subscribed else '🔴'}\n"
            f"🚀 Realtime Alerts: {'🟢' if is_realtime_subscribed else '🔴'}\n"
            f"🔗 Blockchain Monitor: {monitoring_status}\n\n"
            f"💡 Use /blockchain to start monitoring!"
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard buttons"""
        query = update.callback_query
        await query.answer()
        
        # Create fake update for commands
        fake_update = Update(update_id=query.id, message=query.message)
        
        if query.data == "quick_scan":
            await self.quick_scan_command(fake_update, context)
        elif query.data == "realtime_scan":
            await self.realtime_scan_command(fake_update, context)
        elif query.data == "alpha_scan":
            await self.alpha_command(fake_update, context)
        elif query.data == "blockchain_scan":
            await self.blockchain_scan_command(fake_update, context)
        elif query.data == "goodbuy_help":
            await self.goodbuy_help_callback(fake_update, context)
        elif query.data == "help":
            await self.help_command(fake_update, context)
    
    async def goodbuy_help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show GoodBuy help information"""
        await self.safe_send_message(
            update,
            "🔍 **GOODBUY SAFETY ANALYSIS**\n\n"
            "**Usage:** `/goodbuy <token_address>`\n\n"
            "**Example:**\n"
            "`/goodbuy So11111111111111111111111111111111111111112`\n\n"
            "**What it analyzes:**\n"
            "🔒 **Safety:** Liquidity locks, ownership, contract verification\n"
            "📊 **Market Health:** Liquidity, volume, holders, activity\n"
            "🚀 **Momentum:** Volume spikes, buy/sell ratios, trends\n"
            "👑 **Distribution:** Whale concentration, dev wallets\n\n"
            "**Output:** Investment recommendation with risk level\n"
            "**Time:** ~30 seconds for comprehensive analysis"
        )
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.fast_scanner:
                await self.fast_scanner.close()
            if self.gem_hunter:
                await self.gem_hunter.close()
            if self.live_discovery:
                await self.live_discovery.close()
            if self.goodbuy_analyzer:
                await self.goodbuy_analyzer.close()
            if self.alpha_scanner:
                await self.alpha_scanner.close()
            if self.realtime_sniffer:
                self.realtime_sniffer.stop_monitoring()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def run(self):
        """Start the enhanced bot"""
        logger.info("🚀 Starting Realtime Token Sniffer Bot...")
        logger.info("⚡ Multiple detection methods available")
        logger.info("🔗 Blockchain monitoring capable")
        
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
    print("🤖 REALTIME TOKEN SNIFFER BOT STARTUP")
    print("=" * 50)
    
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("📝 Enter your Telegram Bot Token:")
        try:
            BOT_TOKEN = input("Token: ").strip()
        except KeyboardInterrupt:
            print("\n🛑 Canceled by user")
            sys.exit(0)
    
    if not BOT_TOKEN:
        print("❌ Bot token is required!")
        sys.exit(1)
    
    print(f"✅ Token received: {BOT_TOKEN[:10]}...")
    print("🚀 Starting enhanced bot with blockchain monitoring...")
    
    try:
        bot = RealtimeSnifferBot(BOT_TOKEN)
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")