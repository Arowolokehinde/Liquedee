"""
Gem Hunter Scanner
Specialized scanner for finding true crypto gems with strict criteria
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GemHunterScanner:
    """
    Advanced gem hunting scanner with strict criteria:
    - Age: < 72 hours
    - Liquidity: ≥ $2,000
    - Volume Spike: ≥ 200% increase
    - Market Cap: $5k - $500k range
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=20.0)
        self.gem_criteria = {
            "max_age_hours": 72,
            "min_liquidity_usd": 2000,
            "min_volume_spike_percent": 200,
            "min_market_cap": 5000,
            "max_market_cap": 500000,
        }

    async def hunt_gems(self, max_gems: int = 15) -> List[Dict]:
        """
        Hunt for crypto gems across multiple sources
        Returns only tokens meeting strict gem criteria
        """
        logger.info(f"💎 Starting gem hunt (target: {max_gems} gems)...")

        all_gems = []

        try:
            # Strategy 1: DexScreener trending fresh tokens
            dexscreener_gems = await self._hunt_dexscreener_gems(max_gems)
            all_gems.extend(dexscreener_gems)
            logger.info(f"📊 DexScreener: Found {len(dexscreener_gems)} potential gems")

            # Strategy 2: DEX factory new launches
            if len(all_gems) < max_gems:
                factory_gems = await self._hunt_dex_factory_gems(
                    max_gems - len(all_gems)
                )
                all_gems.extend(factory_gems)
                logger.info(f"🏭 DEX Factory: Found {len(factory_gems)} potential gems")

            # Strategy 3: Pump.fun recent launches
            if len(all_gems) < max_gems:
                pumpfun_gems = await self._hunt_pumpfun_gems(max_gems - len(all_gems))
                all_gems.extend(pumpfun_gems)
                logger.info(f"🚀 Pump.fun: Found {len(pumpfun_gems)} potential gems")

            # Remove duplicates and sort by gem score
            unique_gems = self._deduplicate_gems(all_gems)
            verified_gems = [
                gem for gem in unique_gems if self._verify_gem_criteria(gem)
            ]

            # Sort by gem score (combination of freshness, spike, and potential)
            verified_gems.sort(key=lambda x: x.get("gem_score", 0), reverse=True)

            final_gems = verified_gems[:max_gems]

            logger.info(f"💎 Gem hunt complete: {len(final_gems)} verified gems found")
            return final_gems

        except Exception as e:
            logger.error(f"Gem hunt error: {e}")
            return []

    async def _hunt_dexscreener_gems(self, max_gems: int) -> List[Dict]:
        """Hunt for gems on DexScreener trending endpoints"""
        gems = []

        try:
            # Try multiple Solana-focused DexScreener endpoints for fresh tokens
            endpoints = [
                "https://api.dexscreener.com/latest/dex/pairs/solana",
                "https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112",
                "https://api.dexscreener.com/latest/dex/search/?q=solana&orderBy=pairCreatedAt",
                "https://api.dexscreener.com/latest/dex/search/?q=raydium",
                "https://api.dexscreener.com/latest/dex/search/?q=orca",
            ]

            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        for pair in pairs[:50]:  # Check first 50 from each endpoint
                            gem = self._parse_potential_gem(pair, "dexscreener")
                            if (
                                gem
                                and self._is_solana_token(pair)
                                and self._is_potential_gem(gem)
                            ):
                                gems.append(gem)

                                if len(gems) >= max_gems:
                                    return gems
                except Exception as e:
                    logger.warning(f"DexScreener endpoint error: {e}")
                    continue

        except Exception as e:
            logger.error(f"DexScreener gem hunt error: {e}")

        return gems

    async def _hunt_dex_factory_gems(self, max_gems: int) -> List[Dict]:
        """Hunt for gems from DEX factory new launches"""
        gems = []

        try:
            # This would connect to DEX factory monitoring
            # For now, we'll use DexScreener with fresh filtering

            response = await self.http_client.get(
                "https://api.dexscreener.com/latest/dex/search/?q=created"
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])

                for pair in pairs[:30]:
                    gem = self._parse_potential_gem(pair, "dex_factory")
                    if (
                        gem
                        and self._is_solana_token(pair)
                        and self._is_ultra_fresh_gem(gem)
                    ):  # Extra fresh criteria
                        gems.append(gem)

                        if len(gems) >= max_gems:
                            break

        except Exception as e:
            logger.error(f"DEX factory gem hunt error: {e}")

        return gems

    async def _hunt_pumpfun_gems(self, max_gems: int) -> List[Dict]:
        """Hunt for gems on Pump.fun (when API is available)"""
        gems = []

        try:
            # Pump.fun API integration would go here
            # For now, we'll simulate or use alternative endpoint

            # Try pump.fun style tokens via DexScreener
            response = await self.http_client.get(
                "https://api.dexscreener.com/latest/dex/search/?q=pump"
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])

                for pair in pairs[:20]:
                    gem = self._parse_potential_gem(pair, "pumpfun")
                    if (
                        gem
                        and self._is_solana_token(pair)
                        and self._is_potential_gem(gem)
                    ):
                        gems.append(gem)

                        if len(gems) >= max_gems:
                            break

        except Exception as e:
            logger.error(f"Pump.fun gem hunt error: {e}")

        return gems

    def _parse_potential_gem(self, pair: Dict, source: str) -> Optional[Dict]:
        """Parse pair data into potential gem format"""
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

            # Calculate volume spike
            volume_spike = self._calculate_volume_spike(
                volume_1h, volume_24h, age_hours
            )

            gem = {
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

            # Calculate gem score
            gem["gem_score"] = self._calculate_gem_score(gem)

            return gem

        except Exception as e:
            logger.error(f"Error parsing potential gem: {e}")
            return None

    def _calculate_volume_spike(
        self, volume_1h: float, volume_24h: float, age_hours: float
    ) -> float:
        """Calculate volume spike percentage"""
        try:
            if volume_24h <= 0 or age_hours <= 0:
                return 0

            # Expected hourly volume based on 24h average
            expected_hourly = volume_24h / 24

            if expected_hourly <= 0:
                return 0

            # Actual vs expected spike
            spike_percent = (volume_1h / expected_hourly - 1) * 100

            return max(0, spike_percent)  # Return 0 if negative

        except Exception:
            return 0

    def _calculate_gem_score(self, gem: Dict) -> float:
        """Calculate overall gem score (0-10)"""
        try:
            score = 0

            # Freshness score (0-3 points)
            age_hours = gem.get("age_hours", 999)
            if age_hours <= 1:
                score += 3.0
            elif age_hours <= 6:
                score += 2.5
            elif age_hours <= 24:
                score += 2.0
            elif age_hours <= 72:
                score += 1.0

            # Volume spike score (0-3 points)
            spike = gem.get("volume_spike_percent", 0)
            if spike >= 500:
                score += 3.0
            elif spike >= 300:
                score += 2.5
            elif spike >= 200:
                score += 2.0
            elif spike >= 100:
                score += 1.0

            # Market cap score (0-2 points) - sweet spot range
            mcap = gem.get("market_cap_usd", 0)
            if 10000 <= mcap <= 100000:  # $10k-$100k sweet spot
                score += 2.0
            elif 5000 <= mcap <= 500000:  # Within our range
                score += 1.5
            elif mcap > 0:  # Has market cap data
                score += 0.5

            # Liquidity score (0-2 points)
            liquidity = gem.get("liquidity_usd", 0)
            if liquidity >= 10000:
                score += 2.0
            elif liquidity >= 5000:
                score += 1.5
            elif liquidity >= 2000:
                score += 1.0

            return round(score, 2)

        except Exception:
            return 0

    def _is_solana_token(self, pair: Dict) -> bool:
        """Verify this is actually a Solana token pair"""
        try:
            dex_id = pair.get("dexId", "").lower()
            chain_id = pair.get("chainId", "").lower()

            # Check for known Solana DEXs
            solana_dexs = [
                "raydium",
                "orca",
                "jupiter",
                "meteora",
                "openbook",
                "lifinity",
            ]

            # Check if it's explicitly marked as Solana chain or uses Solana DEXs
            if chain_id == "solana" or any(dex in dex_id for dex in solana_dexs):
                return True

            # Additional validation: Check if base or quote token is SOL
            base_token = pair.get("baseToken", {})
            quote_token = pair.get("quoteToken", {})

            sol_address = "So11111111111111111111111111111111111111112"
            if (
                base_token.get("address") == sol_address
                or quote_token.get("address") == sol_address
            ):
                return True

            return False

        except Exception:
            return False

    def _is_potential_gem(self, gem: Dict) -> bool:
        """Quick filter for potential gems"""
        try:
            age_hours = gem.get("age_hours", 999)
            liquidity = gem.get("liquidity_usd", 0)

            # Basic criteria
            if age_hours > 72:  # Not fresh enough
                return False

            if liquidity < 1000:  # Minimum liquidity (relaxed for initial filtering)
                return False

            return True

        except Exception:
            return False

    def _is_ultra_fresh_gem(self, gem: Dict) -> bool:
        """Extra strict criteria for DEX factory gems"""
        try:
            age_hours = gem.get("age_hours", 999)
            return age_hours <= 6  # Ultra fresh only

        except Exception:
            return False

    def _verify_gem_criteria(self, gem: Dict) -> bool:
        """Verify gem meets all strict criteria"""
        try:
            criteria = self.gem_criteria

            # Age check
            if gem.get("age_hours", 999) > criteria["max_age_hours"]:
                return False

            # Liquidity check
            if gem.get("liquidity_usd", 0) < criteria["min_liquidity_usd"]:
                return False

            # Volume spike check
            if (
                gem.get("volume_spike_percent", 0)
                < criteria["min_volume_spike_percent"]
            ):
                return False

            # Market cap range check
            mcap = gem.get("market_cap_usd", 0)
            if mcap > 0:  # Only check if we have market cap data
                if (
                    mcap < criteria["min_market_cap"]
                    or mcap > criteria["max_market_cap"]
                ):
                    return False

            # Add alert type based on gem quality
            gem_score = gem.get("gem_score", 0)
            if gem_score >= 8:
                gem["alert_type"] = "ULTRA_GEM"
            elif gem_score >= 6:
                gem["alert_type"] = "POTENTIAL_GEM"
            else:
                gem["alert_type"] = "EMERGING_TOKEN"

            return True

        except Exception:
            return False

    def _deduplicate_gems(self, gems: List[Dict]) -> List[Dict]:
        """Remove duplicate gems by pair address"""
        seen_addresses = set()
        unique_gems = []

        for gem in gems:
            address = gem.get("pair_address", "")
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                unique_gems.append(gem)

        return unique_gems

    async def get_newest_tokens_fallback(self, max_tokens: int = 3) -> List[Dict]:
        """Fallback: Get newest available Solana tokens under 72h when no gems found"""
        try:
            # Try multiple Solana-specific endpoints
            solana_endpoints = [
                "https://api.dexscreener.com/latest/dex/search/?q=solana",
                "https://api.dexscreener.com/latest/dex/pairs/solana",
                "https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112",
            ]

            fresh_tokens = []
            max_age_hours = self.gem_criteria["max_age_hours"]  # Respect 72h limit

            for endpoint in solana_endpoints:
                try:
                    response = await self.http_client.get(endpoint)

                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        # Parse and filter for Solana tokens under age limit
                        for pair in pairs[:30]:
                            token = self._parse_potential_gem(pair, "fallback")
                            if token:
                                age_hours = token.get("age_hours", 999)
                                dex_id = pair.get("dexId", "").lower()

                                # Only include Solana tokens under 72h with decent liquidity
                                if (
                                    age_hours <= max_age_hours
                                    and token.get("liquidity_usd", 0) >= 1000
                                    and (
                                        "raydium" in dex_id
                                        or "orca" in dex_id
                                        or "jupiter" in dex_id
                                        or "chainId" in pair
                                        and pair.get("chainId") == "solana"
                                    )
                                ):
                                    fresh_tokens.append(token)

                                if (
                                    len(fresh_tokens) >= max_tokens * 2
                                ):  # Get more than needed
                                    break

                        if len(fresh_tokens) >= max_tokens:
                            break

                except Exception as e:
                    logger.warning(f"Solana endpoint error: {e}")
                    continue

            if fresh_tokens:
                # Sort by age (newest first) and gem score
                fresh_tokens.sort(
                    key=lambda x: (x.get("age_hours", 999), -x.get("gem_score", 0))
                )
                result = fresh_tokens[:max_tokens]

                logger.info(
                    f"Fallback found {len(result)} fresh Solana tokens under {max_age_hours}h"
                )
                return result
            else:
                logger.info(
                    f"No fresh Solana tokens found under {max_age_hours}h for fallback"
                )
                return []

        except Exception as e:
            logger.error(f"Fallback tokens error: {e}")

        return []

    async def close(self):
        """Close HTTP client"""
        try:
            await self.http_client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")
