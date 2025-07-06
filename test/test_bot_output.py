#!/usr/bin/env python3
"""
Test script to see how the bot's new output formatting looks
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.telegram_bot.bot_optimized import OptimizedLiquidityBot

def create_sample_fresh_opportunities():
    """Create sample fresh token opportunities"""
    return [
        {
            'pair_address': 'ABC123fresh1',
            'base_symbol': 'MOONSHOT',
            'quote_symbol': 'SOL',
            'dex_name': 'raydium',
            'liquidity_usd': 12500,
            'volume_24h_usd': 8700,
            'price_usd': 0.0045,
            'price_change_24h': 156.7,
            'txns_24h': 89,
            'market_cap_usd': 125000,
            'age_hours': 0.3,  # 18 minutes old
            'alert_type': 'BRAND_NEW_LAUNCH',
            'opportunity_score': 0.75,
            'safety_score': 0.4,
            'momentum_score': 0.8,
            'freshness_score': 0.7,
            'combined_score': 0.725,
            'volume_to_liquidity_ratio': 0.696,
            'reasoning': 'BRAND_NEW (0.3h old), $12,500 liq, $8,700 vol, 0.7x turnover, 89 txns, +156.7% 24h, HIGH momentum'
        },
        {
            'pair_address': 'DEF456fresh2',
            'base_symbol': 'VIRAL',
            'quote_symbol': 'SOL',
            'dex_name': 'orca',
            'liquidity_usd': 25000,
            'volume_24h_usd': 75000,
            'price_usd': 0.012,
            'price_change_24h': 89.3,
            'txns_24h': 234,
            'market_cap_usd': 300000,
            'age_hours': 4.5,
            'alert_type': 'VIRAL_FRESH_TOKEN',
            'opportunity_score': 0.85,
            'safety_score': 0.6,
            'momentum_score': 0.9,
            'freshness_score': 0.6,
            'combined_score': 0.725,
            'volume_to_liquidity_ratio': 3.0,
            'reasoning': 'VERY_FRESH (4.5h old), $25,000 liq, $75,000 vol, 3.0x turnover, 234 txns, +89.3% 24h, VIRAL momentum'
        },
        {
            'pair_address': 'GHI789fresh3',
            'base_symbol': 'EARLY',
            'quote_symbol': 'SOL',
            'dex_name': 'meteora',
            'liquidity_usd': 8900,
            'volume_24h_usd': 15600,
            'price_usd': 0.0078,
            'price_change_24h': 45.2,
            'txns_24h': 67,
            'market_cap_usd': 89000,
            'age_hours': 11.2,
            'alert_type': 'TRENDING_NEW_TOKEN',
            'opportunity_score': 0.65,
            'safety_score': 0.45,
            'momentum_score': 0.7,
            'freshness_score': 0.45,
            'combined_score': 0.55,
            'volume_to_liquidity_ratio': 1.75,
            'reasoning': 'FRESH (11.2h old), $8,900 liq, $15,600 vol, 1.8x turnover, 67 txns, +45.2% 24h, HIGH momentum'
        },
        {
            'pair_address': 'JKL012fresh4',
            'base_symbol': 'NEWGEM',
            'quote_symbol': 'USDC',
            'dex_name': 'raydium',
            'liquidity_usd': 45000,
            'volume_24h_usd': 32000,
            'price_usd': 1.23,
            'price_change_24h': 12.8,
            'txns_24h': 156,
            'market_cap_usd': 450000,
            'age_hours': 23.7,
            'alert_type': 'FRESH_LAUNCH',
            'opportunity_score': 0.6,
            'safety_score': 0.65,
            'momentum_score': 0.55,
            'freshness_score': 0.25,
            'combined_score': 0.425,
            'volume_to_liquidity_ratio': 0.71,
            'reasoning': 'FRESH (23.7h old), $45,000 liq, $32,000 vol, 0.7x turnover, 156 txns, +12.8% 24h, MEDIUM momentum'
        },
        {
            'pair_address': 'MNO345fresh5',
            'base_symbol': 'MOMENTUM',
            'quote_symbol': 'SOL',
            'dex_name': 'orca',
            'liquidity_usd': 67000,
            'volume_24h_usd': 198000,
            'price_usd': 0.034,
            'price_change_24h': 234.5,
            'txns_24h': 445,
            'market_cap_usd': 670000,
            'age_hours': 15.8,
            'alert_type': 'HIGH_MOMENTUM_TOKEN',
            'opportunity_score': 0.9,
            'safety_score': 0.7,
            'momentum_score': 0.95,
            'freshness_score': 0.4,
            'combined_score': 0.65,
            'volume_to_liquidity_ratio': 2.95,
            'reasoning': 'FRESH (15.8h old), $67,000 liq, $198,000 vol, 3.0x turnover, 445 txns, +234.5% 24h, VIRAL momentum'
        }
    ]

def test_output_formatting():
    """Test the new output formatting"""
    print("🎯 TESTING NEW TOKEN SNIFFER OUTPUT FORMAT")
    print("=" * 60)
    
    # Create a bot instance (no token needed for formatting test)
    bot = OptimizedLiquidityBot("dummy_token")
    
    # Create sample opportunities
    opportunities = create_sample_fresh_opportunities()
    
    # Format the opportunities using the new method
    formatted_output = bot.format_opportunities(opportunities)
    
    print("📱 SAMPLE BOT OUTPUT:")
    print("-" * 40)
    print(formatted_output)
    print("-" * 40)
    
    # Compare with old-style output (what we would have seen before)
    print("\n\n🔄 COMPARISON WITH OLD FORMAT:")
    print("=" * 60)
    
    print("❌ OLD FORMAT would have shown:")
    print("   • Fartcoin/SOL - $8,740,097 liquidity (5763h old)")
    print("   • JLP/USDC - $8,688,888 liquidity (11224h old)")
    print("   • cbBTC/SOL - $11,146,272 liquidity (5764h old)")
    print("   (All established, old tokens)")
    
    print("\n✅ NEW FORMAT shows:")
    print("   • MOONSHOT/SOL - 18 minutes old")
    print("   • VIRAL/SOL - 4.5 hours old")
    print("   • EARLY/SOL - 11.2 hours old")
    print("   (All fresh, new opportunities)")
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("   ✓ Age prominently displayed")
    print("   ✓ Freshness scores shown")
    print("   ✓ Turnover ratios highlighted")
    print("   ✓ Alert types indicate freshness level")
    print("   ✓ Different emojis for different alert types")

def test_settings_comparison():
    """Show before/after settings comparison"""
    print("\n\n⚙️ SETTINGS COMPARISON")
    print("=" * 60)
    
    print("❌ OLD SETTINGS (Blue-chip scanner):")
    print("   • Min Liquidity: $10,000 (excluded early tokens)")
    print("   • Min Volume: $5,000 (excluded initial activity)")
    print("   • Max Age: 168 hours (included week-old tokens)")
    print("   • Max Results: 10")
    print("   • Mode: Safety-first")
    
    print("\n✅ NEW SETTINGS (Fresh token sniffer):")
    print("   • Min Liquidity: $500 (catches very early tokens)")
    print("   • Min Volume: $50 (catches initial activity)")
    print("   • Max Age: 72 hours (fresh tokens only)")
    print("   • Max Results: 15")
    print("   • Mode: Freshness-priority")
    
    print("\n🔄 IMPACT:")
    print("   • 20x lower liquidity threshold")
    print("   • 100x lower volume threshold")
    print("   • 2.3x stricter age limit")
    print("   • 50% more results shown")

def test_alert_types():
    """Test the new alert type system"""
    print("\n\n🚨 NEW ALERT TYPE SYSTEM")
    print("=" * 60)
    
    alert_types = [
        ("🆕 BRAND_NEW_LAUNCH", "< 1 hour old", "Freshest possible finds"),
        ("🚀 VIRAL_FRESH_TOKEN", "< 6 hours + high momentum", "Going viral early"),
        ("📈 TRENDING_NEW_TOKEN", "< 12 hours + volume", "Building momentum"),
        ("🌟 FRESH_LAUNCH", "< 24 hours", "Still very fresh"),
        ("💡 RECENT_OPPORTUNITY", "< 48 hours", "Recent but promising"),
        ("🔥 HIGH_MOMENTUM_TOKEN", "High turnover ratio", "Momentum play"),
        ("💎 EMERGING_OPPORTUNITY", "Basic criteria met", "General opportunity")
    ]
    
    for emoji_type, criteria, description in alert_types:
        print(f"{emoji_type}")
        print(f"   Criteria: {criteria}")
        print(f"   Purpose: {description}")
        print()

def main():
    """Run all output tests"""
    test_output_formatting()
    test_settings_comparison()
    test_alert_types()
    
    print("\n🏁 OUTPUT TEST COMPLETE")
    print("=" * 60)
    print("The bot now shows fresh tokens instead of established ones!")
    print("Users will see completely different results focused on early opportunities.")

if __name__ == "__main__":
    main()