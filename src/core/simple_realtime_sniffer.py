"""
Simplified Real-time Token Discovery
Uses periodic blockchain scanning instead of WebSocket monitoring
More reliable and easier to implement
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

logger = logging.getLogger(__name__)


class SimpleRealtimeSniffer:
    """
    Simplified real-time token discovery using periodic blockchain scanning
    More reliable than WebSocket monitoring, still much faster than DexScreener
    """

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url)
        self.http_client = httpx.AsyncClient()

        # Track discovered pairs
        self.fresh_pairs = {}  # pair_address -> discovery_data
        self.callbacks = []

        # Monitoring state
        self.is_monitoring = False
        self.scan_interval = 60  # Scan every 60 seconds

        # Known DEX program IDs for transaction filtering
        self.dex_programs = {
            "raydium_amm": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "raydium_clmm": "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
            "orca_whirlpool": "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
            "meteora": "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
        }

    async def start_monitoring(self, callback: Callable = None):
        """Start periodic blockchain scanning for fresh pairs"""
        logger.info("🚀 Starting simplified real-time monitoring...")

        if callback:
            self.callbacks.append(callback)

        self.is_monitoring = True

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._periodic_blockchain_scan()),
            asyncio.create_task(self._cleanup_old_pairs()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.is_monitoring = False
            await self._cleanup()

    async def _periodic_blockchain_scan(self):
        """Periodically scan for new transactions and pairs"""
        logger.info("📡 Starting periodic blockchain scanning...")

        last_scan_signature = None

        while self.is_monitoring:
            try:
                # Get recent signatures from known DEX programs
                new_pairs = await self._scan_recent_transactions(last_scan_signature)

                for pair_data in new_pairs:
                    await self._handle_new_pair_detected(pair_data)

                if new_pairs:
                    logger.info(f"🆕 Found {len(new_pairs)} new pairs in this scan")

                await asyncio.sleep(self.scan_interval)

            except Exception as e:
                logger.error(f"Scan error: {e}")
                await asyncio.sleep(self.scan_interval)

    async def _scan_recent_transactions(
        self, last_signature: Optional[str]
    ) -> List[Dict]:
        """Scan recent transactions for new pair creation"""
        discovered_pairs = []

        try:
            # Check DexScreener for very recent pairs (last 2 hours)
            # This is more reliable than parsing blockchain transactions directly
            recent_pairs = await self._get_recent_dexscreener_pairs()

            for pair in recent_pairs:
                age_hours = pair.get("age_hours", 999)
                pair_address = pair.get("pair_address", "")

                # Only include very fresh pairs (< 2 hours) that we haven't seen
                if age_hours <= 2 and pair_address not in self.fresh_pairs:
                    discovery_time = datetime.now()

                    pair_data = {
                        **pair,
                        "discovery_method": "realtime_dexscreener",
                        "discovery_time": discovery_time.isoformat(),
                        "age_at_discovery": age_hours,
                    }

                    self.fresh_pairs[pair_address] = pair_data
                    discovered_pairs.append(pair_data)

        except Exception as e:
            logger.error(f"Error scanning recent transactions: {e}")

        return discovered_pairs

    async def _get_recent_dexscreener_pairs(self) -> List[Dict]:
        """Get very recent pairs from DexScreener and parse them"""
        from ..core.dexscreener_massive import MassiveDexScreenerClient

        try:
            scanner = MassiveDexScreenerClient()

            # Get pairs but focus on very recent ones
            raw_pairs = await scanner.get_latest_pairs()
            recent_pairs = []

            for raw_pair in raw_pairs[:200]:  # Check first 200 pairs
                parsed = scanner.parse_pair_data(raw_pair)
                if not parsed:
                    continue

                age_hours = parsed.get("age_hours")
                if age_hours is not None and age_hours <= 3:  # Only very fresh pairs
                    recent_pairs.append(parsed)

            await scanner.close()

            # Sort by age (newest first)
            recent_pairs.sort(key=lambda x: x.get("age_hours", 999))

            return recent_pairs[:50]  # Return top 50 freshest

        except Exception as e:
            logger.error(f"Error getting recent DexScreener pairs: {e}")
            return []

    async def _handle_new_pair_detected(self, pair_data: Dict):
        """Handle a newly discovered pair"""
        try:
            pair_address = pair_data.get("pair_address", "")
            base_symbol = pair_data.get("base_symbol", "UNKNOWN")
            age_hours = pair_data.get("age_hours", 0)

            logger.info(
                f"🆕 NEW FRESH PAIR: {base_symbol} ({age_hours:.1f}h old) - {pair_address}"
            )

            # Notify callbacks
            for callback in self.callbacks:
                try:
                    await callback(pair_data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        except Exception as e:
            logger.error(f"Error handling new pair: {e}")

    async def get_fresh_pairs_last_24h(self) -> List[Dict]:
        """Get all pairs discovered in the last 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        fresh_pairs = []
        for pair_address, pair_data in self.fresh_pairs.items():
            discovery_time_str = pair_data.get("discovery_time", "")
            try:
                discovery_time = datetime.fromisoformat(
                    discovery_time_str.replace("Z", "+00:00")
                )
                discovery_time = discovery_time.replace(
                    tzinfo=None
                )  # Remove timezone for comparison

                if discovery_time >= cutoff_time:
                    fresh_pairs.append(pair_data)
            except Exception:
                # If we can't parse the time, include it anyway if it's recent
                age_hours = pair_data.get("age_hours", 999)
                if age_hours <= 24:
                    fresh_pairs.append(pair_data)

        # Sort by discovery time (newest first)
        fresh_pairs.sort(key=lambda x: x.get("age_hours", 999))
        return fresh_pairs[:20]  # Top 20 freshest

    async def get_ultra_fresh_pairs(self) -> List[Dict]:
        """Get pairs discovered in the last 2 hours (ultra fresh)"""
        cutoff_time = datetime.now() - timedelta(hours=2)

        ultra_fresh = []
        for pair_address, pair_data in self.fresh_pairs.items():
            age_hours = pair_data.get("age_hours", 999)
            if age_hours <= 2:  # Ultra fresh (< 2 hours)
                ultra_fresh.append(pair_data)

        # Sort by age (newest first)
        ultra_fresh.sort(key=lambda x: x.get("age_hours", 999))
        return ultra_fresh[:10]  # Top 10 ultra fresh

    async def _cleanup_old_pairs(self):
        """Periodically clean up old pair records"""
        while self.is_monitoring:
            try:
                cutoff_time = datetime.now() - timedelta(hours=48)

                pairs_to_remove = []
                for pair_address, pair_data in self.fresh_pairs.items():
                    age_hours = pair_data.get("age_hours", 0)
                    if age_hours > 48:  # Remove pairs older than 48 hours
                        pairs_to_remove.append(pair_address)

                for pair_addr in pairs_to_remove:
                    del self.fresh_pairs[pair_addr]

                if pairs_to_remove:
                    logger.info(f"🧹 Cleaned up {len(pairs_to_remove)} old pair records")

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _cleanup(self):
        """Clean up resources"""
        try:
            await self.http_client.aclose()
            await self.client.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def stop_monitoring(self):
        """Stop monitoring"""
        logger.info("🛑 Stopping simplified real-time monitoring...")
        self.is_monitoring = False


class EnhancedRealtimeSniffer:
    """
    Enhanced version that combines multiple detection methods
    """

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.simple_sniffer = SimpleRealtimeSniffer(rpc_url)
        self.is_monitoring = False

    async def start_comprehensive_monitoring(self, callback: Callable = None):
        """Start comprehensive monitoring using multiple methods"""
        logger.info("🚀 Starting comprehensive real-time monitoring...")

        self.is_monitoring = True

        # Start simple periodic scanning
        simple_task = asyncio.create_task(
            self.simple_sniffer.start_monitoring(callback)
        )

        # Could add more monitoring methods here in the future
        # e.g., mempool monitoring, webhook listeners, etc.

        try:
            await simple_task
        except Exception as e:
            logger.error(f"Comprehensive monitoring error: {e}")
        finally:
            self.is_monitoring = False

    async def get_all_fresh_pairs(self) -> List[Dict]:
        """Get all fresh pairs from all monitoring methods"""
        return await self.simple_sniffer.get_fresh_pairs_last_24h()

    async def get_ultra_fresh_pairs(self) -> List[Dict]:
        """Get ultra fresh pairs (< 2 hours)"""
        return await self.simple_sniffer.get_ultra_fresh_pairs()

    def stop_monitoring(self):
        """Stop all monitoring"""
        self.simple_sniffer.stop_monitoring()
        self.is_monitoring = False


# Factory for creating sniffers
class SimpleSnifferFactory:
    """Factory for creating simplified real-time sniffers"""

    @staticmethod
    def create_simple_sniffer(rpc_url: str = None) -> SimpleRealtimeSniffer:
        """Create a simple real-time sniffer"""
        return SimpleRealtimeSniffer(
            rpc_url=rpc_url or "https://api.mainnet-beta.solana.com"
        )

    @staticmethod
    def create_enhanced_sniffer(rpc_url: str = None) -> EnhancedRealtimeSniffer:
        """Create an enhanced real-time sniffer"""
        return EnhancedRealtimeSniffer(
            rpc_url=rpc_url or "https://api.mainnet-beta.solana.com"
        )
