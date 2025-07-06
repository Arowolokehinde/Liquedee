#!/usr/bin/env python3
"""
MASSIVE COMPREHENSIVE SCAN - Find hundreds of opportunities
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from datetime import datetime

from src.core.dexscreener import DexScreenerClient
from src.core.liquidity_analyzer import LiquidityAnalyzer


async def massive_scan():
    print("🚀 MASSIVE COMPREHENSIVE SCAN - MAXIMUM OPPORTUNITIES")
    print("=" * 80)

    client = DexScreenerClient()
    analyzer = LiquidityAnalyzer()

    start_time = datetime.now()

    try:
        # Get all opportunities
        pairs = await client.get_latest_pairs()

        print(f"📊 MASSIVE SCAN COMPLETE: {len(pairs)} total pairs found!")
        print(
            f"⏱️  Scan time: {(datetime.now() - start_time).total_seconds():.1f} seconds"
        )

        if not pairs:
            print("❌ No opportunities found")
            return

        # Analyze all pairs
        all_alerts = []
        categories = {}

        print(f"\n🔍 Analyzing all {len(pairs)} opportunities...")

        for i, raw_pair in enumerate(pairs):
            if i % 100 == 0:
                print(f"   Analyzed {i}/{len(pairs)} pairs...")

            parsed = client.parse_pair_data(raw_pair)
            if not parsed:
                continue

            alert = await analyzer.analyze_pair(parsed)
            if alert:
                all_alerts.append(alert)
                alert_type = alert["alert_type"]

                if alert_type not in categories:
                    categories[alert_type] = 0
                categories[alert_type] += 1

        # Sort by opportunity score
        all_alerts.sort(key=lambda x: x["opportunity_score"], reverse=True)

        print(f"\n🎉 MASSIVE SCAN RESULTS:")
        print(f"📊 Total pairs scanned: {len(pairs)}")
        print(f"🎯 Total opportunities found: {len(all_alerts)}")
        print(
            f"⏱️  Total time: {(datetime.now() - start_time).total_seconds():.1f} seconds"
        )

        print(f"\n📋 Categories breakdown:")
        for category, count in sorted(
            categories.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"   • {category}: {count}")

        # Show top opportunities
        print(f"\n🔥 TOP 25 OPPORTUNITIES:")
        for i, alert in enumerate(all_alerts[:25]):
            age_str = f"{alert['age_hours']:.1f}h" if alert["age_hours"] else "unknown"
            print(
                f'{i+1:2d}. {alert["base_symbol"]}/{alert["quote_symbol"]} | {alert["dex_name"]}'
            )
            print(
                f'     💰 ${alert["liquidity_usd"]:,.0f} liq | 📈 ${alert["volume_24h_usd"]:,.0f} vol | ⏰ {age_str}'
            )
            print(
                f'     🎯 {alert["opportunity_score"]:.2f} opp | 🛡️  {alert["safety_score"]:.2f} safe | 🚀 {alert["momentum_score"]:.2f} mom'
            )
            print(
                f'     📊 {alert["price_change_24h"]:+.1f}% 24h | 🔄 {alert["txns_24h"]} txns'
            )
            print()

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/scan_results_{timestamp}.json"

        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        with open(filename, "w") as f:
            json.dump(
                {
                    "scan_time": start_time.isoformat(),
                    "total_pairs": len(pairs),
                    "total_opportunities": len(all_alerts),
                    "categories": categories,
                    "top_opportunities": all_alerts[:50],  # Save top 50
                },
                f,
                indent=2,
            )

        print(f"💾 Results saved to: {filename}")

        if len(all_alerts) > 200:
            print(f"\n🚀 INCREDIBLE SUCCESS: Found {len(all_alerts)} opportunities!")
            print(
                f"This scanner is finding more opportunities than DexScreener itself!"
            )

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(massive_scan())
