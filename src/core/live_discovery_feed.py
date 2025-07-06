"""
Live Discovery Feed Scanner
Focused on finding MORE fresh opportunities with moderate criteria
Less strict than gem hunter - quantity of fresh discoveries
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LiveDiscoveryScanner:
    """
    Live discovery feed scanner with moderate criteria:
    - Age: < 24 hours (vs 72h for gems)
    - Liquidity: ≥ $1,000 (vs $2k for gems)
    - Volume Spike: ≥ 100% (vs 200% for gems)
    - Market Cap: $1k - $1M range (vs $5k-500k for gems)
    - Focus: MORE opportunities, recent discoveries
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=20.0)
        self.discovery_criteria = {
            "max_age_hours": 24,  # 24h vs 72h for gems
            "min_liquidity_usd": 1000,  # $1k vs $2k for gems
            "min_volume_spike_percent": 100,  # 100% vs 200% for gems
            "min_market_cap": 1000,  # $1k vs $5k for gems
            "max_market_cap": 1000000,  # $1M vs $500k for gems
        }

    async def scan_live_discoveries(self, max_discoveries: int = 15) -> List[Dict]:
        """
        Scan for live fresh discoveries with moderate criteria
        Returns more opportunities than strict gem hunting
        """
        logger.info(
            f"🚀 Starting live discovery scan (target: {max_discoveries} discoveries)..."
        )

        all_discoveries = []

        try:
            # Strategy 1: Recent Solana tokens (most active)
            recent_tokens = await self._scan_recent_solana_tokens(max_discoveries)
            all_discoveries.extend(recent_tokens)
            logger.info(f"📊 Recent Solana: Found {len(recent_tokens)} discoveries")

            # Strategy 2: Fresh pump.fun style tokens
            if len(all_discoveries) < max_discoveries:
                pump_tokens = await self._scan_fresh_pump_tokens(
                    max_discoveries - len(all_discoveries)
                )
                all_discoveries.extend(pump_tokens)
                logger.info(f"🚀 Pump Style: Found {len(pump_tokens)} discoveries")

            # Strategy 3: New DEX listings
            if len(all_discoveries) < max_discoveries:
                dex_tokens = await self._scan_new_dex_listings(
                    max_discoveries - len(all_discoveries)
                )
                all_discoveries.extend(dex_tokens)
                logger.info(f"🏭 DEX Listings: Found {len(dex_tokens)} discoveries")

            # Strategy 4: Trending searches
            if len(all_discoveries) < max_discoveries:
                trending_tokens = await self._scan_trending_tokens(
                    max_discoveries - len(all_discoveries)
                )
                all_discoveries.extend(trending_tokens)
                logger.info(f"📈 Trending: Found {len(trending_tokens)} discoveries")

            # Remove duplicates and filter
            unique_discoveries = self._deduplicate_discoveries(all_discoveries)
            filtered_discoveries = [
                d for d in unique_discoveries if self._meets_discovery_criteria(d)
            ]

            # Sort by discovery score (freshness + activity)
            filtered_discoveries.sort(
                key=lambda x: x.get("discovery_score", 0), reverse=True
            )

            final_discoveries = filtered_discoveries[:max_discoveries]

            logger.info(
                f"🚀 Live discovery scan complete: {len(final_discoveries)} fresh discoveries found"
            )
            return final_discoveries

        except Exception as e:
            logger.error(f"Live discovery scan error: {e}")
            return []

    async def _scan_recent_solana_tokens(self, max_tokens: int) -> List[Dict]:
        """Scan for recently created Solana tokens"""
        discoveries = []

        try:
            # Multiple endpoints for fresh token discovery
            endpoints = [
                "https://api.dexscreener.com/latest/dex/search/?q=SOL&orderBy=h24Volume",
                "https://api.dexscreener.com/latest/dex/search/?q=new",
                "https://api.dexscreener.com/latest/dex/search/?q=launched",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:30]:  # Check first 30 from each
                            discovery = self._parse_discovery(pair, "recent_solana")
                            if discovery and self._is_recent_discovery(discovery):
                                discoveries.append(discovery)

                                if len(discoveries) >= max_tokens:
                                    return discoveries
                except Exception as e:
                    logger.warning(f"Recent Solana endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Recent Solana scan error: {e}")

        return discoveries

    async def _scan_fresh_pump_tokens(self, max_tokens: int) -> List[Dict]:
        """Scan for fresh pump.fun style tokens"""
        discoveries = []

        try:
            # Pump.fun and similar platforms
            endpoints = [
                "https://api.dexscreener.com/latest/dex/search/?q=pump",
                "https://api.dexscreener.com/latest/dex/search/?q=meme",
                "https://api.dexscreener.com/latest/dex/search/?q=fair",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:20]:
                            discovery = self._parse_discovery(pair, "pump_style")
                            if discovery and self._is_fresh_discovery(discovery):
                                discoveries.append(discovery)

                                if len(discoveries) >= max_tokens:
                                    return discoveries
                except Exception as e:
                    logger.warning(f"Pump style endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Pump style scan error: {e}")

        return discoveries

    async def _scan_new_dex_listings(self, max_tokens: int) -> List[Dict]:
        """Scan for new DEX listings"""
        discoveries = []

        try:
            # Focus on different DEXs for variety
            endpoints = [
                "https://api.dexscreener.com/latest/dex/search/?q=raydium",
                "https://api.dexscreener.com/latest/dex/search/?q=orca",
                "https://api.dexscreener.com/latest/dex/search/?q=meteora",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:15]:
                            discovery = self._parse_discovery(pair, "dex_listing")
                            if discovery and self._is_viable_discovery(discovery):
                                discoveries.append(discovery)

                                if len(discoveries) >= max_tokens:
                                    return discoveries
                except Exception as e:
                    logger.warning(f"DEX listing endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"DEX listing scan error: {e}")

        return discoveries

    async def _scan_trending_tokens(self, max_tokens: int) -> List[Dict]:
        """Scan for trending tokens with recent activity"""
        discoveries = []

        try:
            # Focus on trending/active tokens
            endpoints = [
                "https://api.dexscreener.com/latest/dex/search/?q=trending",
                "https://api.dexscreener.com/latest/dex/search/?q=volume",
                "https://api.dexscreener.com/latest/dex/search/?q=active",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:10]:
                            discovery = self._parse_discovery(pair, "trending")
                            if discovery and self._has_recent_activity(discovery):
                                discoveries.append(discovery)

                                if len(discoveries) >= max_tokens:
                                    return discoveries
                except Exception as e:
                    logger.warning(f"Trending endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Trending scan error: {e}")

        return discoveries

    def _parse_discovery(self, pair: Dict, source: str) -> Optional[Dict]:
        """Parse pair data into discovery format"""
        try:
            if not pair.get("baseToken") or not pair.get("quoteToken"):
                return None

            base_token = pair["baseToken"]
            quote_token = pair["quoteToken"]

            # Calculate age
            age_hours = 999
            if pair.get("pairCreatedAt"):
                created_time = datetime.fromtimestamp(pair["pairCreatedAt"] / 1000)
                age_hours = (datetime.now() - created_time).total_seconds() / 3600

            # Get financial metrics
            liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0) or 0)
            volume_24h = float(pair.get("volume", {}).get("h24", 0) or 0)
            volume_1h = float(pair.get("volume", {}).get("h1", 0) or 0)
            market_cap = float(pair.get("marketCap", 0) or 0)
            price_change_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0)

            # Calculate volume spike (less strict than gems)
            volume_spike = self._calculate_volume_activity(
                volume_1h, volume_24h, age_hours
            )

            discovery = {
                "pair_address": pair.get("pairAddress", ""),
                "base_token": base_token.get("address", ""),
                "quote_token": quote_token.get("address", ""),
                "base_symbol": base_token.get("symbol", "UNKNOWN"),
                "quote_symbol": quote_token.get("symbol", "SOL"),
                "dex_name": pair.get("dexId", "unknown"),
                "total_liquidity_usd": liquidity_usd,
                "liquidity_usd": liquidity_usd,
                "volume_24h_usd": volume_24h,
                "volume_1h_usd": volume_1h,
                "market_cap_usd": market_cap,
                "price_usd": float(pair.get("priceUsd", 0) or 0),
                "price_change_24h": price_change_24h,
                "age_hours": age_hours,
                "volume_spike_percent": volume_spike,
                "source": source,
                "url": f"https://dexscreener.com/solana/{pair.get('pairAddress', '')}",
                "discovered_at": datetime.now().isoformat(),
            }

            # Calculate discovery score (freshness + activity focus)
            discovery["discovery_score"] = self._calculate_discovery_score(discovery)

            return discovery

        except Exception as e:
            logger.error(f"Error parsing discovery: {e}")
            return None

    def _calculate_volume_activity(
        self, volume_1h: float, volume_24h: float, age_hours: float
    ) -> float:
        """Calculate volume activity (less strict than gem spike detection)"""
        try:
            if volume_24h <= 0 or age_hours <= 0:
                return 0

            # More lenient activity calculation
            expected_hourly = volume_24h / 24

            if expected_hourly <= 0:
                return 0

            # Activity vs expected
            activity_percent = (volume_1h / expected_hourly - 1) * 100

            return max(0, activity_percent)

        except Exception:
            return 0

    def _calculate_discovery_score(self, discovery: Dict) -> float:
        """Calculate discovery score focusing on freshness and activity"""
        try:
            score = 0

            # Freshness score (0-4 points) - higher weight for recency
            age_hours = discovery.get("age_hours", 999)
            if age_hours <= 0.5:  # 30 minutes
                score += 4.0
            elif age_hours <= 2:  # 2 hours
                score += 3.5
            elif age_hours <= 6:  # 6 hours
                score += 3.0
            elif age_hours <= 12:  # 12 hours
                score += 2.5
            elif age_hours <= 24:  # 24 hours
                score += 2.0

            # Activity score (0-3 points)
            volume_activity = discovery.get("volume_spike_percent", 0)
            if volume_activity >= 300:
                score += 3.0
            elif volume_activity >= 150:
                score += 2.5
            elif volume_activity >= 100:
                score += 2.0
            elif volume_activity >= 50:
                score += 1.5
            elif volume_activity > 0:
                score += 1.0

            # Liquidity score (0-2 points)
            liquidity = discovery.get("liquidity_usd", 0)
            if liquidity >= 10000:
                score += 2.0
            elif liquidity >= 5000:
                score += 1.5
            elif liquidity >= 1000:
                score += 1.0

            # Price momentum (0-1 point)
            price_change = discovery.get("price_change_24h", 0)
            if price_change > 20:
                score += 1.0
            elif price_change > 0:
                score += 0.5

            return round(score, 2)

        except Exception:
            return 0

    def _is_recent_discovery(self, discovery: Dict) -> bool:
        """Check if discovery is recent (< 12 hours)"""
        age_hours = discovery.get("age_hours", 999)
        return age_hours <= 12

    def _is_fresh_discovery(self, discovery: Dict) -> bool:
        """Check if discovery is fresh (< 6 hours)"""
        age_hours = discovery.get("age_hours", 999)
        return age_hours <= 6

    def _is_viable_discovery(self, discovery: Dict) -> bool:
        """Check if discovery is viable (< 24 hours + basic criteria)"""
        age_hours = discovery.get("age_hours", 999)
        liquidity = discovery.get("liquidity_usd", 0)
        return age_hours <= 24 and liquidity >= 500

    def _has_recent_activity(self, discovery: Dict) -> bool:
        """Check if discovery has recent activity"""
        volume_activity = discovery.get("volume_spike_percent", 0)
        return volume_activity >= 50  # Any positive activity

    def _meets_discovery_criteria(self, discovery: Dict) -> bool:
        """Check if discovery meets moderate criteria"""
        try:
            criteria = self.discovery_criteria

            # Age check (more lenient)
            if discovery.get("age_hours", 999) > criteria["max_age_hours"]:
                return False

            # Liquidity check (lower threshold)
            if discovery.get("liquidity_usd", 0) < criteria["min_liquidity_usd"]:
                return False

            # Activity check (lower threshold)
            if (
                discovery.get("volume_spike_percent", 0)
                < criteria["min_volume_spike_percent"]
            ):
                return False

            # Market cap check (wider range)
            mcap = discovery.get("market_cap_usd", 0)
            if mcap > 0:
                if (
                    mcap < criteria["min_market_cap"]
                    or mcap > criteria["max_market_cap"]
                ):
                    return False

            # Add discovery type based on score
            discovery_score = discovery.get("discovery_score", 0)
            if discovery_score >= 8:
                discovery["discovery_type"] = "HOT_DISCOVERY"
            elif discovery_score >= 6:
                discovery["discovery_type"] = "FRESH_FIND"
            elif discovery_score >= 4:
                discovery["discovery_type"] = "NEW_OPPORTUNITY"
            else:
                discovery["discovery_type"] = "RECENT_LAUNCH"

            return True

        except Exception:
            return False

    def _deduplicate_discoveries(self, discoveries: List[Dict]) -> List[Dict]:
        """Remove duplicate discoveries"""
        seen_addresses = set()
        unique_discoveries = []

        for discovery in discoveries:
            address = discovery.get("pair_address", "")
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                unique_discoveries.append(discovery)

        return unique_discoveries

    async def close(self):
        """Close HTTP client"""
        try:
            await self.http_client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")
