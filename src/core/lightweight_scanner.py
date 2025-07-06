"""
Lightweight Token Scanner
Fast, focused scanning that completes in 10-15 seconds
Designed to replace the blocking MassiveDexScreenerClient
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LightweightTokenScanner:
    """
    Lightweight scanner that prioritizes speed and reliability
    Focuses on essential endpoints and limits results for fast completion
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=15.0)
        self.base_url = "https://api.dexscreener.com/latest/dex"

    async def get_fresh_opportunities(self, max_pairs: int = 25) -> List[Dict]:
        """
        Get fresh token opportunities with fast, focused scanning
        Limited to 25 pairs maximum for speed
        """
        logger.info(f"🔍 Starting lightweight scan (max {max_pairs} pairs)...")

        try:
            # Strategy: Focus only on SOL pairs (most active and reliable)
            fresh_pairs = await self._scan_sol_pairs_only(max_pairs)

            logger.info(
                f"✅ Lightweight scan complete: {len(fresh_pairs)} fresh opportunities found"
            )
            return fresh_pairs

        except Exception as e:
            logger.error(f"Lightweight scan error: {e}")
            return []

    async def _scan_sol_pairs_only(self, max_pairs: int) -> List[Dict]:
        """
        Scan multiple endpoints for fresh pairs - prioritize speed over comprehensiveness
        """
        try:
            fresh_opportunities = []

            # Strategy 1: Check latest pairs across all Solana DEXs (most likely to have fresh tokens)
            latest_pairs = await self._get_latest_solana_pairs(max_pairs)
            fresh_opportunities.extend(latest_pairs)

            # If we don't have enough, try SOL token pairs as backup
            if len(fresh_opportunities) < max_pairs:
                sol_pairs = await self._get_sol_token_pairs(
                    max_pairs - len(fresh_opportunities)
                )
                fresh_opportunities.extend(sol_pairs)

            # Sort by freshness score (newest first)
            fresh_opportunities.sort(
                key=lambda x: x.get("freshness_score", 0), reverse=True
            )

            return fresh_opportunities[:max_pairs]

        except Exception as e:
            logger.error(f"Error in lightweight scan: {e}")
            return []

    async def _get_latest_solana_pairs(self, max_pairs: int) -> List[Dict]:
        """Get latest pairs from Solana DEXs - more likely to be fresh"""
        try:
            # This endpoint often has newer pairs
            url = f"{self.base_url}/search/?q=SOL"

            response = await self.http_client.get(url)
            response.raise_for_status()

            data = response.json()
            pairs = data.get("pairs", [])

            logger.info(f"📊 Found {len(pairs)} pairs from search endpoint")

            fresh_opportunities = []
            for pair in pairs[: max_pairs * 2]:
                parsed = self._parse_pair_data(pair)
                if parsed and self._is_fresh_opportunity(parsed):
                    fresh_opportunities.append(parsed)

                    if len(fresh_opportunities) >= max_pairs:
                        break

            return fresh_opportunities

        except Exception as e:
            logger.error(f"Error getting latest pairs: {e}")
            return []

    async def _get_sol_token_pairs(self, max_pairs: int) -> List[Dict]:
        """Fallback: Get SOL token pairs"""
        try:
            # Get SOL pairs from DexScreener
            url = f"{self.base_url}/tokens/So11111111111111111111111111111111111111112"  # SOL token address

            response = await self.http_client.get(url)
            response.raise_for_status()

            data = response.json()
            pairs = data.get("pairs", [])

            logger.info(f"📊 Processing {len(pairs)} SOL pairs...")

            # For SOL pairs, be more permissive on age since they tend to be older
            fresh_opportunities = []
            for pair in pairs[: max_pairs * 2]:
                parsed = self._parse_pair_data(pair)
                if parsed and self._is_quality_pair(
                    parsed
                ):  # Use quality filter instead of freshness
                    fresh_opportunities.append(parsed)

                    if len(fresh_opportunities) >= max_pairs:
                        break

            return fresh_opportunities

        except Exception as e:
            logger.error(f"Error scanning SOL pairs: {e}")
            return []

    def _is_quality_pair(self, pair: Dict) -> bool:
        """
        Alternative filter for quality pairs when fresh pairs aren't available
        """
        try:
            liquidity_usd = pair.get("total_liquidity_usd", 0)
            volume_24h = pair.get("volume_24h_usd", 0)

            # Quality criteria (not age-dependent)
            if liquidity_usd < 1000:  # At least $1k liquidity
                return False

            if volume_24h < 100:  # At least $100 volume
                return False

            # Calculate a quality score based on activity
            volume_to_liq = volume_24h / liquidity_usd if liquidity_usd > 0 else 0

            # Give it a reasonable score based on activity
            if volume_to_liq > 0.5:
                quality_score = 0.8
            elif volume_to_liq > 0.1:
                quality_score = 0.6
            else:
                quality_score = 0.4

            pair["freshness_score"] = quality_score
            pair["combined_score"] = quality_score * (1 + min(volume_to_liq, 1))

            return quality_score > 0.3

        except Exception:
            return False

    def _parse_pair_data(self, pair: Dict) -> Optional[Dict]:
        """
        Parse pair data from DexScreener API response
        Simplified parsing for speed
        """
        try:
            # Basic validation
            if not pair.get("baseToken") or not pair.get("quoteToken"):
                return None

            base_token = pair["baseToken"]
            quote_token = pair["quoteToken"]

            # Calculate age
            age_hours = 999
            if pair.get("pairCreatedAt"):
                created_time = datetime.fromtimestamp(pair["pairCreatedAt"] / 1000)
                age_hours = (datetime.now() - created_time).total_seconds() / 3600

            # Get liquidity and volume
            liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0) or 0)
            volume_24h = float(pair.get("volume", {}).get("h24", 0) or 0)

            # Skip if no meaningful data
            if liquidity_usd < 100 and volume_24h < 50:
                return None

            return {
                "pair_address": pair.get("pairAddress", ""),
                "base_token": base_token.get("address", ""),
                "quote_token": quote_token.get("address", ""),
                "base_symbol": base_token.get("symbol", "UNKNOWN"),
                "quote_symbol": quote_token.get("symbol", "SOL"),
                "dex_name": pair.get("dexId", "unknown"),
                "total_liquidity_usd": liquidity_usd,
                "liquidity_usd": liquidity_usd,
                "volume_24h_usd": volume_24h,
                "price_usd": float(pair.get("priceUsd", 0) or 0),
                "price_change_24h": float(
                    pair.get("priceChange", {}).get("h24", 0) or 0
                ),
                "txns_24h": (pair.get("txns", {}).get("h24", {}).get("buys", 0) or 0)
                + (pair.get("txns", {}).get("h24", {}).get("sells", 0) or 0),
                "market_cap_usd": float(pair.get("marketCap", 0) or 0),
                "age_hours": age_hours,
                "volume_to_liquidity_ratio": volume_24h / liquidity_usd
                if liquidity_usd > 0
                else 0,
                "url": f"https://dexscreener.com/solana/{pair.get('pairAddress', '')}",
                "source": "lightweight_scanner",
            }

        except Exception as e:
            logger.error(f"Error parsing pair data: {e}")
            return None

    def _is_fresh_opportunity(self, pair: Dict) -> bool:
        """
        Quick filter for fresh opportunities
        More permissive than the full analyzer for speed
        """
        try:
            age_hours = pair.get("age_hours", 999)
            liquidity_usd = pair.get("total_liquidity_usd", 0)
            volume_24h = pair.get("volume_24h_usd", 0)

            # Fresh token criteria (focused on truly fresh)
            if age_hours > 72:  # Must be less than 72 hours old
                return False

            if liquidity_usd < 500:  # Minimum liquidity
                return False

            if volume_24h < 50:  # Minimum volume
                return False

            # Calculate freshness score quickly
            freshness_score = self._calculate_quick_freshness_score(pair)
            pair["freshness_score"] = freshness_score

            # Basic momentum check
            volume_to_liq = pair.get("volume_to_liquidity_ratio", 0)
            if volume_to_liq > 0.1:  # Some momentum
                pair["combined_score"] = freshness_score * (1 + min(volume_to_liq, 2))
            else:
                pair["combined_score"] = freshness_score

            return freshness_score > 0.3  # Standard freshness threshold

        except Exception:
            return False

    def _calculate_quick_freshness_score(self, pair: Dict) -> float:
        """
        Quick freshness score calculation
        Simplified version of the full analyzer
        """
        try:
            age_hours = pair.get("age_hours", 999)

            if age_hours <= 1:
                return 1.0  # Brand new
            elif age_hours <= 6:
                return 0.9  # Very fresh
            elif age_hours <= 24:
                return 0.7  # Fresh
            elif age_hours <= 48:
                return 0.5  # Moderately fresh
            else:
                return 0.3  # Still within 72h window

        except Exception:
            return 0.1

    async def close(self):
        """Close HTTP client"""
        try:
            await self.http_client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")


class FastSnifferBot:
    """
    Drop-in replacement for the blocking scan functionality
    Focuses on speed and reliability over comprehensive coverage
    """

    def __init__(self):
        self.scanner = LightweightTokenScanner()

    async def quick_scan(self, max_results: int = 15) -> List[Dict]:
        """
        Fast scan that completes in 10-15 seconds
        Returns top fresh opportunities
        """
        logger.info(f"⚡ Starting fast scan (target: {max_results} results)...")
        start_time = datetime.now()

        try:
            # Get fresh opportunities
            opportunities = await self.scanner.get_fresh_opportunities(max_pairs=25)

            # Apply additional scoring if needed
            scored_opportunities = []
            for opp in opportunities:
                # Add alert type based on freshness
                age_hours = opp.get("age_hours", 999)
                if age_hours <= 1:
                    opp["alert_type"] = "BRAND_NEW_LAUNCH"
                elif age_hours <= 6:
                    opp["alert_type"] = "VIRAL_FRESH_TOKEN"
                else:
                    opp["alert_type"] = "TRENDING_NEW_TOKEN"

                scored_opportunities.append(opp)

            # Sort by combined score and limit results
            scored_opportunities.sort(
                key=lambda x: x.get("combined_score", 0), reverse=True
            )
            final_results = scored_opportunities[:max_results]

            scan_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"✅ Fast scan complete in {scan_time:.1f}s: {len(final_results)} opportunities"
            )

            return final_results

        except Exception as e:
            logger.error(f"Fast scan error: {e}")
            return []

    async def close(self):
        """Clean up resources"""
        await self.scanner.close()
