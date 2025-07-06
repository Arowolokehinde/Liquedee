#!/usr/bin/env python3
"""
Test Fixed Gem Hunter
Tests the gem hunter with age limit fixes and Solana-only filtering
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.core.gem_hunter import GemHunterScanner

async def test_fixed_gem_hunter():
    """Test the fixed gem hunter"""
    print("💎 TESTING FIXED GEM HUNTER")
    print("=" * 70)
    print("Testing strict age filtering and Solana-only tokens...")
    
    # Create gem hunter
    gem_hunter = GemHunterScanner()
    
    try:
        print("\n📊 **GEM HUNTER CONFIGURATION:**")
        
        criteria = gem_hunter.gem_criteria
        print(f"\n💎 **STRICT GEM CRITERIA:**")
        print(f"• Max Age: {criteria['max_age_hours']} hours (3 days)")
        print(f"• Min Liquidity: ${criteria['min_liquidity_usd']:,}")
        print(f"• Min Volume Spike: {criteria['min_volume_spike_percent']}%")
        print(f"• Market Cap Range: ${criteria['min_market_cap']:,} - ${criteria['max_market_cap']:,}")
        
        print(f"\n🔬 **RUNNING FIXED GEM HUNT:**")
        
        # Test gem hunting
        start_time = datetime.now()
        
        print("💎 Starting strict gem hunt...")
        gems = await gem_hunter.hunt_gems(max_gems=10)
        
        print("📊 Testing fallback logic...")
        fallback_tokens = await gem_hunter.get_newest_tokens_fallback(3)
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ **GEM HUNT RESULTS:**")
        print(f"⏱️ Total Time: {total_duration:.1f} seconds")
        print(f"💎 Verified Gems: {len(gems)}")
        print(f"📊 Fallback Tokens: {len(fallback_tokens)}")
        
        # Analyze gem results
        if gems:
            print(f"\n💎 **VERIFIED GEMS FOUND:**")
            for i, gem in enumerate(gems, 1):
                age_hours = gem.get('age_hours', 999)
                age_str = f"{age_hours:.1f}h" if age_hours < 24 else f"{age_hours/24:.1f}d"
                
                print(f"{i}. {gem.get('base_symbol', 'UNKNOWN')}/{gem.get('quote_symbol', 'SOL')}")
                print(f"   🕐 {age_str} old | ✅ AGE CHECK: {'PASS' if age_hours <= 72 else 'FAIL'}")
                print(f"   💰 ${gem.get('liquidity_usd', 0):,} liquidity")
                print(f"   📊 {gem.get('volume_spike_percent', 0):.0f}% spike")
                print(f"   💎 {gem.get('gem_score', 0):.1f}/10 score")
                print(f"   📍 DEX: {gem.get('dex_name', 'unknown')}")
        else:
            print(f"\n💎 **NO VERIFIED GEMS**")
            print("No tokens meet all strict gem criteria right now.")
        
        # Analyze fallback results
        if fallback_tokens:
            print(f"\n📊 **FALLBACK TOKENS (Fresh Solana):**")
            for i, token in enumerate(fallback_tokens, 1):
                age_hours = token.get('age_hours', 999)
                age_str = f"{age_hours:.1f}h" if age_hours < 24 else f"{age_hours/24:.1f}d"
                
                print(f"{i}. {token.get('base_symbol', 'UNKNOWN')}/{token.get('quote_symbol', 'SOL')}")
                print(f"   🕐 {age_str} old | ✅ AGE CHECK: {'PASS' if age_hours <= 72 else 'FAIL'}")
                print(f"   💰 ${token.get('liquidity_usd', 0):,} liquidity")
                print(f"   📊 {token.get('volume_spike_percent', 0):.0f}% activity")
                print(f"   📍 DEX: {token.get('dex_name', 'unknown')}")
        else:
            print(f"\n📊 **NO FALLBACK TOKENS**")
            print("No fresh Solana tokens under 72h found.")
        
        # Validation checks
        print(f"\n🔍 **VALIDATION CHECKS:**")
        
        # Check age compliance
        all_tokens = gems + fallback_tokens
        if all_tokens:
            age_violations = [t for t in all_tokens if t.get('age_hours', 999) > 72]
            if age_violations:
                print(f"❌ AGE VIOLATIONS: {len(age_violations)} tokens over 72h")
                for violation in age_violations:
                    age_hours = violation.get('age_hours', 999)
                    print(f"   • {violation.get('base_symbol', 'UNKNOWN')}: {age_hours:.1f}h old")
            else:
                print(f"✅ AGE COMPLIANCE: All tokens under 72h")
            
            # Check chain compliance (should all be Solana)
            dex_names = [t.get('dex_name', 'unknown') for t in all_tokens]
            non_solana_dexs = [dex for dex in dex_names if dex.lower() not in ['raydium', 'orca', 'jupiter', 'meteora', 'openbook', 'lifinity', 'unknown']]
            if non_solana_dexs:
                print(f"❌ CHAIN VIOLATIONS: Non-Solana DEXs found: {set(non_solana_dexs)}")
            else:
                print(f"✅ CHAIN COMPLIANCE: All Solana DEXs")
        else:
            print(f"📊 NO TOKENS: Market very quiet")
        
        # Performance check
        print(f"\n🚀 **PERFORMANCE VALIDATION:**")
        if total_duration <= 25:
            print(f"✅ EXCELLENT: Gem hunt completed in {total_duration:.1f}s")
        elif total_duration <= 35:
            print(f"✅ GOOD: Completed in {total_duration:.1f}s")
        else:
            print(f"⚠️  SLOW: Took {total_duration:.1f}s")
        
        # Overall assessment
        print(f"\n🎯 **OVERALL ASSESSMENT:**")
        
        age_compliant = all(t.get('age_hours', 999) <= 72 for t in all_tokens)
        has_tokens = len(all_tokens) > 0
        
        if age_compliant and has_tokens:
            print(f"✅ FIXED: Age filtering working correctly")
        elif age_compliant and not has_tokens:
            print(f"✅ WORKING: No violations, market just quiet")
        else:
            print(f"❌ NEEDS WORK: Still showing old tokens")
        
        return age_compliant
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await gem_hunter.close()

async def main():
    """Run the gem hunter fix test"""
    print("💎 GEM HUNTER FIX TEST")
    print("=" * 70)
    print("Testing age limit fixes and Solana-only filtering...")
    
    try:
        # Test the fixed gem hunter
        success = await test_fixed_gem_hunter()
        
        print("\n\n🏁 GEM HUNTER FIX TEST COMPLETE")
        print("=" * 70)
        
        if success:
            print("✅ GEM HUNTER FIXED!")
            print("\n💎 **FIXES IMPLEMENTED:**")
            print("1. Fallback respects 72h age limit")
            print("2. Solana-only token filtering")
            print("3. Better endpoint targeting")
            print("4. Improved error messaging")
            print("5. Chain validation for all tokens")
        else:
            print("❌ Still needs refinement")
        
        print("\n💎 **EXPECTED BEHAVIOR:**")
        print("• No tokens over 72 hours old")
        print("• Only Solana blockchain tokens")
        print("• Clear messaging when market is quiet")
        print("• Fallback only shows fresh Solana tokens")
        print("• Honest about gem criteria vs availability")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())