#!/usr/bin/env python3
"""
Test script to verify the token sniffer refactor works correctly
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.core.dexscreener_massive import MassiveDexScreenerClient
from src.core.liquidity_analyzer import LiquidityAnalyzer


def create_test_token_data(
    age_hours: float, liquidity: float, volume: float, txns: int = 50
) -> dict:
    """Create test token data with specific parameters"""
    created_time = datetime.now() - timedelta(hours=age_hours)

    return {
        "pair_address": f"test_pair_{age_hours}h_{liquidity}_{volume}",
        "base_token": "TestToken123",
        "quote_token": "So11111111111111111111111111111111111111112",
        "base_symbol": f"TEST{int(age_hours)}H",
        "quote_symbol": "SOL",
        "dex_name": "raydium",
        "pool_address": f"test_pool_{age_hours}h",
        "age_hours": age_hours,
        "total_liquidity_usd": liquidity,
        "base_liquidity": liquidity * 0.5,
        "quote_liquidity": liquidity * 0.5,
        "volume_24h_usd": volume,
        "price_usd": 0.001,
        "price_change_24h": 10.5,
        "txns_24h": txns,
        "buyers_24h": txns // 2,
        "sellers_24h": txns // 2,
        "fdv_usd": liquidity * 10,
        "market_cap_usd": liquidity * 8,
        "volume_to_liquidity_ratio": volume / max(liquidity, 1),
        "raw_data": {},
        "timestamp": datetime.utcnow(),
    }


async def test_analyzer_behavior():
    """Test that the analyzer now prioritizes fresh tokens"""
    print("🧪 TESTING TOKEN SNIFFER ANALYZER")
    print("=" * 50)

    analyzer = LiquidityAnalyzer()

    # Test cases: [age_hours, liquidity, volume, expected_behavior]
    test_cases = [
        # Fresh tokens with various sizes
        (0.5, 1000, 500, "should_accept_brand_new"),
        (2, 5000, 2000, "should_accept_very_fresh"),
        (12, 10000, 5000, "should_accept_fresh"),
        (48, 25000, 10000, "should_accept_recent"),
        (71, 50000, 20000, "should_accept_just_under_limit"),
        # Old tokens (should be rejected regardless of size)
        (100, 1000000, 500000, "should_reject_old_despite_high_liquidity"),
        (200, 5000000, 1000000, "should_reject_very_old"),
        # Edge cases
        (73, 100000, 50000, "should_reject_just_over_age_limit"),
        (24, 400, 40, "should_reject_too_small"),
    ]

    results = []

    for age_hours, liquidity, volume, expected in test_cases:
        token_data = create_test_token_data(age_hours, liquidity, volume)
        result = await analyzer.analyze_pair(token_data)

        accepted = result is not None
        score = result.get("combined_score", 0) if result else 0
        freshness_score = result.get("freshness_score", 0) if result else 0

        print(f"\n📊 Test: {age_hours}h old, ${liquidity:,.0f} liq, ${volume:,.0f} vol")
        print(f"   Expected: {expected}")
        print(f"   Result: {'✅ ACCEPTED' if accepted else '❌ REJECTED'}")

        if accepted:
            print(f"   Combined Score: {score:.3f}")
            print(f"   Freshness Score: {freshness_score:.3f}")
            print(f"   Alert Type: {result.get('alert_type', 'unknown')}")

        results.append(
            {
                "age_hours": age_hours,
                "liquidity": liquidity,
                "volume": volume,
                "expected": expected,
                "accepted": accepted,
                "score": score,
                "freshness_score": freshness_score,
            }
        )

    return results


def analyze_test_results(results):
    """Analyze test results to see if behavior matches expectations"""
    print("\n\n🔍 TEST RESULT ANALYSIS")
    print("=" * 50)

    # Check age filtering
    fresh_tokens = [r for r in results if r["age_hours"] <= 72]
    old_tokens = [r for r in results if r["age_hours"] > 72]

    fresh_accepted = [r for r in fresh_tokens if r["accepted"]]
    old_accepted = [r for r in old_tokens if r["accepted"]]

    print(f"📈 Fresh tokens (<= 72h): {len(fresh_tokens)}")
    print(f"   Accepted: {len(fresh_accepted)}/{len(fresh_tokens)}")

    print(f"📉 Old tokens (> 72h): {len(old_tokens)}")
    print(f"   Accepted: {len(old_accepted)}/{len(old_tokens)} (should be 0)")

    # Check freshness scoring
    if fresh_accepted:
        avg_freshness = sum(r["freshness_score"] for r in fresh_accepted) / len(
            fresh_accepted
        )
        newest_token = min(fresh_accepted, key=lambda x: x["age_hours"])
        oldest_accepted = max(fresh_accepted, key=lambda x: x["age_hours"])

        print(f"\n🌟 Freshness Analysis:")
        print(f"   Average freshness score: {avg_freshness:.3f}")
        print(
            f"   Newest accepted: {newest_token['age_hours']}h (score: {newest_token['freshness_score']:.3f})"
        )
        print(
            f"   Oldest accepted: {oldest_accepted['age_hours']}h (score: {oldest_accepted['freshness_score']:.3f})"
        )

    # Overall assessment
    print(f"\n✅ SUCCESS CRITERIA:")
    print(f"   ✓ Rejects old tokens (>72h): {'✅' if len(old_accepted) == 0 else '❌'}")
    print(f"   ✓ Accepts some fresh tokens: {'✅' if len(fresh_accepted) > 0 else '❌'}")
    print(
        f"   ✓ Higher scores for newer tokens: {'✅' if check_freshness_correlation(fresh_accepted) else '❌'}"
    )


def check_freshness_correlation(accepted_tokens):
    """Check if newer tokens generally get higher freshness scores"""
    if len(accepted_tokens) < 2:
        return True

    # Sort by age and check if freshness scores generally decrease
    sorted_by_age = sorted(accepted_tokens, key=lambda x: x["age_hours"])

    violations = 0
    for i in range(len(sorted_by_age) - 1):
        current = sorted_by_age[i]
        next_token = sorted_by_age[i + 1]

        # Newer token should have higher or equal freshness score
        if current["freshness_score"] < next_token["freshness_score"]:
            violations += 1

    # Allow some violations due to other factors
    return violations <= len(sorted_by_age) // 3


async def test_old_vs_new_comparison():
    """Direct comparison: old established token vs new fresh token"""
    print("\n\n🥊 OLD vs NEW TOKEN COMPARISON")
    print("=" * 50)

    analyzer = LiquidityAnalyzer()

    # Old established token (like the Fartcoin we saw before)
    old_token = create_test_token_data(
        age_hours=5763,  # Same as the Fartcoin result
        liquidity=8740097,
        volume=16175523,
        txns=1000,
    )
    old_token["base_symbol"] = "FARTCOIN"

    # New fresh token with much smaller numbers
    new_token = create_test_token_data(
        age_hours=2,  # 2 hours old
        liquidity=15000,  # Much smaller
        volume=8000,  # Much smaller
        txns=50,
    )
    new_token["base_symbol"] = "NEWFRESH"

    print("🏛️  OLD TOKEN (Established):")
    print(f"   Age: {old_token['age_hours']:.1f} hours")
    print(f"   Liquidity: ${old_token['total_liquidity_usd']:,.0f}")
    print(f"   Volume: ${old_token['volume_24h_usd']:,.0f}")

    print("\n🌱 NEW TOKEN (Fresh):")
    print(f"   Age: {new_token['age_hours']:.1f} hours")
    print(f"   Liquidity: ${new_token['total_liquidity_usd']:,.0f}")
    print(f"   Volume: ${new_token['volume_24h_usd']:,.0f}")

    # Analyze both
    old_result = await analyzer.analyze_pair(old_token)
    new_result = await analyzer.analyze_pair(new_token)

    print(f"\n📊 RESULTS:")
    print(f"   Old Token: {'✅ ACCEPTED' if old_result else '❌ REJECTED'}")
    if old_result:
        print(f"      Combined Score: {old_result.get('combined_score', 0):.3f}")
        print(f"      Freshness Score: {old_result.get('freshness_score', 0):.3f}")

    print(f"   New Token: {'✅ ACCEPTED' if new_result else '❌ REJECTED'}")
    if new_result:
        print(f"      Combined Score: {new_result.get('combined_score', 0):.3f}")
        print(f"      Freshness Score: {new_result.get('freshness_score', 0):.3f}")

    print(f"\n🎯 SNIFFER SUCCESS:")
    old_rejected = old_result is None
    new_accepted = new_result is not None

    if old_rejected and new_accepted:
        print("   ✅ PERFECT! Old token rejected, fresh token accepted")
    elif old_rejected and not new_accepted:
        print("   ⚠️  Old rejected (good) but fresh also rejected (check thresholds)")
    elif not old_rejected and new_accepted:
        print("   ⚠️  Both accepted (fresh priority may need tuning)")
    else:
        print("   ❌ Both rejected (system too restrictive)")


async def main():
    """Run all tests"""
    print("🎯 TOKEN SNIFFER REFACTOR TEST SUITE")
    print("=" * 60)
    print("Testing if our changes successfully prioritize fresh tokens...")

    try:
        # Test 1: General analyzer behavior
        results = await test_analyzer_behavior()
        analyze_test_results(results)

        # Test 2: Direct old vs new comparison
        await test_old_vs_new_comparison()

        print("\n\n🏁 TEST COMPLETE")
        print("=" * 60)
        print("If you see ✅ symbols above, the refactor is working!")
        print("The system should now prioritize fresh tokens over established ones.")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
