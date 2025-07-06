"""
Alpha Scanner
Multi-chain trending token scanner for curated daily alpha gems
Tracks volume leaders, social mentions, and price spikes across chains
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


class AlphaScanner:
    """
    Multi-chain alpha scanner for trending tokens:
    - Volume leaders across chains
    - Social mention spikes
    - Price momentum leaders
    - Cross-chain trending analysis
    - Daily curated alpha gems
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Alpha criteria for trending tokens
        self.alpha_criteria = {
            "min_volume_24h": 50000,  # $50k minimum volume
            "min_market_cap": 100000,  # $100k minimum market cap
            "min_price_spike_percent": 15,  # 15% minimum price spike
            "min_social_mentions": 10,  # Minimum social activity
            "max_age_days": 30,  # Maximum 30 days old
            "min_liquidity": 25000,  # $25k minimum liquidity
        }

        # Supported chains for alpha scanning
        self.supported_chains = [
            "solana",
            "ethereum",
            "bsc",
            "polygon",
            "arbitrum",
            "avalanche",
            "base",
        ]

    async def scan_alpha_gems(self, max_gems: int = 20) -> List[Dict]:
        """
        Scan for top alpha gems across all chains
        Returns curated list of trending tokens by multiple criteria
        """
        logger.info(
            f"🔥 Starting alpha gem scan across chains (target: {max_gems} gems)..."
        )

        all_alpha_gems = []

        try:
            # Strategy 1: Volume leaders (most important)
            volume_leaders = await self._scan_volume_leaders(max_gems // 2)
            all_alpha_gems.extend(volume_leaders)
            logger.info(f"📊 Volume Leaders: Found {len(volume_leaders)} alpha gems")

            # Strategy 2: Price spike leaders
            if len(all_alpha_gems) < max_gems:
                spike_leaders = await self._scan_price_spike_leaders(
                    max_gems - len(all_alpha_gems)
                )
                all_alpha_gems.extend(spike_leaders)
                logger.info(f"🚀 Spike Leaders: Found {len(spike_leaders)} alpha gems")

            # Strategy 3: Social trending tokens
            if len(all_alpha_gems) < max_gems:
                social_trending = await self._scan_social_trending(
                    max_gems - len(all_alpha_gems)
                )
                all_alpha_gems.extend(social_trending)
                logger.info(
                    f"🐦 Social Trending: Found {len(social_trending)} alpha gems"
                )

            # Strategy 4: New listings with momentum
            if len(all_alpha_gems) < max_gems:
                momentum_gems = await self._scan_momentum_gems(
                    max_gems - len(all_alpha_gems)
                )
                all_alpha_gems.extend(momentum_gems)
                logger.info(f"⚡ Momentum Gems: Found {len(momentum_gems)} alpha gems")

            # Remove duplicates and filter
            unique_gems = self._deduplicate_alpha_gems(all_alpha_gems)
            filtered_gems = [g for g in unique_gems if self._meets_alpha_criteria(g)]

            # Sort by alpha score (trending strength)
            filtered_gems.sort(key=lambda x: x.get("alpha_score", 0), reverse=True)

            final_gems = filtered_gems[:max_gems]

            logger.info(
                f"🔥 Alpha gem scan complete: {len(final_gems)} trending gems found"
            )
            return final_gems

        except Exception as e:
            logger.error(f"Alpha gem scan error: {e}")
            return []

    async def _scan_volume_leaders(self, max_tokens: int) -> List[Dict]:
        """Scan for highest volume tokens across chains"""
        alpha_gems = []

        try:
            # Multi-chain volume leaders
            endpoints = [
                "https://api.dexscreener.com/latest/dex/search/?q=solana&orderBy=h24Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=ethereum&orderBy=h24Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=bsc&orderBy=h24Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=polygon&orderBy=h24Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=arbitrum&orderBy=h24Volume",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:10]:  # Top 10 from each chain
                            alpha_gem = self._parse_alpha_gem(pair, "volume_leader")
                            if alpha_gem and self._is_volume_leader(alpha_gem):
                                alpha_gems.append(alpha_gem)

                                if len(alpha_gems) >= max_tokens:
                                    return alpha_gems
                except Exception as e:
                    logger.warning(f"Volume leader endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Volume leaders scan error: {e}")

        return alpha_gems

    async def _scan_price_spike_leaders(self, max_tokens: int) -> List[Dict]:
        """Scan for tokens with biggest price spikes"""
        alpha_gems = []

        try:
            # Price spike queries across chains
            spike_queries = [
                "https://api.dexscreener.com/latest/dex/search/?q=gainers",
                "https://api.dexscreener.com/latest/dex/search/?q=trending",
                "https://api.dexscreener.com/latest/dex/search/?q=movers",
            ]

            for query in spike_queries:
                try:
                    response = await self.http_client.get(query)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:15]:
                            alpha_gem = self._parse_alpha_gem(pair, "price_spike")
                            if alpha_gem and self._is_price_spike_leader(alpha_gem):
                                alpha_gems.append(alpha_gem)

                                if len(alpha_gems) >= max_tokens:
                                    return alpha_gems
                except Exception as e:
                    logger.warning(f"Price spike endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Price spike scan error: {e}")

        return alpha_gems

    async def _scan_social_trending(self, max_tokens: int) -> List[Dict]:
        """Scan for socially trending tokens"""
        alpha_gems = []

        try:
            # Social trending indicators
            social_queries = [
                "https://api.dexscreener.com/latest/dex/search/?q=viral",
                "https://api.dexscreener.com/latest/dex/search/?q=community",
                "https://api.dexscreener.com/latest/dex/search/?q=meme",
            ]

            for query in social_queries:
                try:
                    response = await self.http_client.get(query)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:10]:
                            alpha_gem = self._parse_alpha_gem(pair, "social_trending")
                            if alpha_gem and self._has_social_momentum(alpha_gem):
                                alpha_gems.append(alpha_gem)

                                if len(alpha_gems) >= max_tokens:
                                    return alpha_gems
                except Exception as e:
                    logger.warning(f"Social trending endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Social trending scan error: {e}")

        return alpha_gems

    async def _scan_momentum_gems(self, max_tokens: int) -> List[Dict]:
        """Scan for new tokens with strong momentum"""
        alpha_gems = []

        try:
            # Momentum-focused queries
            momentum_queries = [
                "https://api.dexscreener.com/latest/dex/search/?q=new&orderBy=h24Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=fresh&orderBy=h1Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=launch",
            ]

            for query in momentum_queries:
                try:
                    response = await self.http_client.get(query)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:8]:
                            alpha_gem = self._parse_alpha_gem(pair, "momentum_gem")
                            if alpha_gem and self._has_strong_momentum(alpha_gem):
                                alpha_gems.append(alpha_gem)

                                if len(alpha_gems) >= max_tokens:
                                    return alpha_gems
                except Exception as e:
                    logger.warning(f"Momentum gem endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Momentum gems scan error: {e}")

        return alpha_gems

    def _parse_alpha_gem(self, pair: Dict, source: str) -> Optional[Dict]:
        """Parse pair data into alpha gem format"""
        try:
            if not pair.get("baseToken") or not pair.get("quoteToken"):
                return None

            base_token = pair["baseToken"]
            quote_token = pair["quoteToken"]

            # Calculate age
            age_hours = 999
            age_days = 999
            if pair.get("pairCreatedAt"):
                created_time = datetime.fromtimestamp(pair["pairCreatedAt"] / 1000)
                age_hours = (datetime.now() - created_time).total_seconds() / 3600
                age_days = age_hours / 24

            # Get financial metrics
            liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0) or 0)
            volume_24h = float(pair.get("volume", {}).get("h24", 0) or 0)
            volume_1h = float(pair.get("volume", {}).get("h1", 0) or 0)
            market_cap = float(pair.get("marketCap", 0) or 0)
            price_change_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0)
            price_change_1h = float(pair.get("priceChange", {}).get("h1", 0) or 0)

            # Determine chain
            chain = self._determine_chain(pair)

            # Get transaction data
            txns_24h = pair.get("txns", {}).get("h24", {})
            buys = txns_24h.get("buys", 0) or 0
            sells = txns_24h.get("sells", 0) or 0

            alpha_gem = {
                "pair_address": pair.get("pairAddress", ""),
                "base_token": base_token.get("address", ""),
                "quote_token": quote_token.get("address", ""),
                "base_symbol": base_token.get("symbol", "UNKNOWN"),
                "quote_symbol": quote_token.get("symbol", "UNKNOWN"),
                "chain": chain,
                "dex_name": pair.get("dexId", "unknown"),
                "total_liquidity_usd": liquidity_usd,
                "liquidity_usd": liquidity_usd,
                "volume_24h_usd": volume_24h,
                "volume_1h_usd": volume_1h,
                "market_cap_usd": market_cap,
                "price_usd": float(pair.get("priceUsd", 0) or 0),
                "price_change_24h": price_change_24h,
                "price_change_1h": price_change_1h,
                "age_hours": age_hours,
                "age_days": age_days,
                "buys_24h": buys,
                "sells_24h": sells,
                "social_mentions": self._estimate_social_mentions(pair, volume_24h),
                "source": source,
                "url": f"https://dexscreener.com/{chain}/{pair.get('pairAddress', '')}",
                "discovered_at": datetime.now().isoformat(),
            }

            # Calculate alpha score (trending strength)
            alpha_gem["alpha_score"] = self._calculate_alpha_score(alpha_gem)

            return alpha_gem

        except Exception as e:
            logger.error(f"Error parsing alpha gem: {e}")
            return None

    def _determine_chain(self, pair: Dict) -> str:
        """Determine blockchain from pair data"""
        chain_id = pair.get("chainId", "")
        dex_id = pair.get("dexId", "").lower()

        # Chain detection logic
        if "solana" in dex_id or chain_id == "solana":
            return "solana"
        elif "ethereum" in dex_id or chain_id == "1":
            return "ethereum"
        elif "bsc" in dex_id or "pancake" in dex_id or chain_id == "56":
            return "bsc"
        elif "polygon" in dex_id or chain_id == "137":
            return "polygon"
        elif "arbitrum" in dex_id or chain_id == "42161":
            return "arbitrum"
        elif "avalanche" in dex_id or chain_id == "43114":
            return "avalanche"
        elif "base" in dex_id or chain_id == "8453":
            return "base"
        else:
            return "unknown"

    def _estimate_social_mentions(self, pair: Dict, volume_24h: float) -> int:
        """Estimate social mentions based on volume and activity"""
        # Simple heuristic: higher volume = more social activity
        if volume_24h > 1000000:  # $1M+ volume
            return 50 + int(volume_24h / 100000)
        elif volume_24h > 500000:  # $500k+ volume
            return 25 + int(volume_24h / 50000)
        elif volume_24h > 100000:  # $100k+ volume
            return 10 + int(volume_24h / 25000)
        else:
            return max(1, int(volume_24h / 10000))

    def _calculate_alpha_score(self, gem: Dict) -> float:
        """Calculate alpha score based on trending strength"""
        try:
            score = 0

            # Volume score (0-4 points) - most important for alpha
            volume_24h = gem.get("volume_24h_usd", 0)
            if volume_24h >= 5000000:  # $5M+
                score += 4.0
            elif volume_24h >= 2000000:  # $2M+
                score += 3.5
            elif volume_24h >= 1000000:  # $1M+
                score += 3.0
            elif volume_24h >= 500000:  # $500k+
                score += 2.5
            elif volume_24h >= 100000:  # $100k+
                score += 2.0
            elif volume_24h >= 50000:  # $50k+
                score += 1.0

            # Price momentum score (0-3 points)
            price_change_24h = gem.get("price_change_24h", 0)
            if price_change_24h >= 100:  # 100%+
                score += 3.0
            elif price_change_24h >= 50:  # 50%+
                score += 2.5
            elif price_change_24h >= 25:  # 25%+
                score += 2.0
            elif price_change_24h >= 15:  # 15%+
                score += 1.5
            elif price_change_24h > 0:  # Any gain
                score += 0.5

            # Market cap scoring (0-2 points) - sweet spot
            market_cap = gem.get("market_cap_usd", 0)
            if 1000000 <= market_cap <= 50000000:  # $1M-$50M sweet spot
                score += 2.0
            elif 500000 <= market_cap <= 100000000:  # $500k-$100M
                score += 1.5
            elif 100000 <= market_cap <= 500000:  # $100k-$500k
                score += 1.0

            # Liquidity score (0-1 point)
            liquidity = gem.get("liquidity_usd", 0)
            if liquidity >= 100000:  # $100k+
                score += 1.0
            elif liquidity >= 25000:  # $25k+
                score += 0.5

            # Social activity bonus (0-1 point)
            social_mentions = gem.get("social_mentions", 0)
            if social_mentions >= 100:
                score += 1.0
            elif social_mentions >= 50:
                score += 0.75
            elif social_mentions >= 25:
                score += 0.5
            elif social_mentions >= 10:
                score += 0.25

            # Chain diversity bonus
            chain = gem.get("chain", "")
            if chain in ["ethereum", "solana"]:  # Major chains
                score += 0.5
            elif chain in ["arbitrum", "polygon", "bsc"]:  # L2/Alt chains
                score += 0.3

            return round(score, 2)

        except Exception:
            return 0

    def _is_volume_leader(self, gem: Dict) -> bool:
        """Check if gem qualifies as volume leader"""
        volume = gem.get("volume_24h_usd", 0)
        return volume >= 500000  # $500k+ volume

    def _is_price_spike_leader(self, gem: Dict) -> bool:
        """Check if gem has significant price spike"""
        price_change = gem.get("price_change_24h", 0)
        return price_change >= 25  # 25%+ gain

    def _has_social_momentum(self, gem: Dict) -> bool:
        """Check if gem has social momentum"""
        mentions = gem.get("social_mentions", 0)
        volume = gem.get("volume_24h_usd", 0)
        return mentions >= 15 and volume >= 100000

    def _has_strong_momentum(self, gem: Dict) -> bool:
        """Check if gem has strong overall momentum"""
        volume = gem.get("volume_24h_usd", 0)
        price_change = gem.get("price_change_24h", 0)
        age_days = gem.get("age_days", 999)

        return volume >= 100000 and price_change >= 10 and age_days <= 30

    def _meets_alpha_criteria(self, gem: Dict) -> bool:
        """Check if gem meets alpha criteria"""
        try:
            criteria = self.alpha_criteria

            # Volume check
            if gem.get("volume_24h_usd", 0) < criteria["min_volume_24h"]:
                return False

            # Market cap check
            mcap = gem.get("market_cap_usd", 0)
            if mcap > 0 and mcap < criteria["min_market_cap"]:
                return False

            # Age check (not too old)
            if gem.get("age_days", 999) > criteria["max_age_days"]:
                return False

            # Liquidity check
            if gem.get("liquidity_usd", 0) < criteria["min_liquidity"]:
                return False

            # Add alpha type based on score
            alpha_score = gem.get("alpha_score", 0)
            if alpha_score >= 9:
                gem["alpha_type"] = "MEGA_ALPHA"
            elif alpha_score >= 7:
                gem["alpha_type"] = "STRONG_ALPHA"
            elif alpha_score >= 5:
                gem["alpha_type"] = "SOLID_ALPHA"
            else:
                gem["alpha_type"] = "EMERGING_ALPHA"

            return True

        except Exception:
            return False

    def _deduplicate_alpha_gems(self, gems: List[Dict]) -> List[Dict]:
        """Remove duplicate alpha gems"""
        seen_addresses = set()
        unique_gems = []

        for gem in gems:
            address = gem.get("pair_address", "")
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                unique_gems.append(gem)

        return unique_gems

    async def close(self):
        """Close HTTP client"""
        try:
            await self.http_client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")
