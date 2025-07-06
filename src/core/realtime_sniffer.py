"""
Real-time blockchain monitoring for TRULY fresh token launches
Monitors DEX factory contracts directly for new pair creation events
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import httpx
import websockets
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts
from solana.rpc.websocket_api import connect
from solders.pubkey import Pubkey
from solders.signature import Signature

logger = logging.getLogger(__name__)


class RealtimeTokenSniffer:
    """
    Real-time blockchain monitoring for fresh token launches
    Monitors DEX factory contracts and detects new pairs within minutes
    """

    def __init__(
        self,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        wss_url: str = "wss://api.mainnet-beta.solana.com",
    ):
        self.rpc_url = rpc_url
        self.wss_url = wss_url
        self.client = AsyncClient(rpc_url)
        self.http_client = httpx.AsyncClient()

        # DEX factory program IDs we'll monitor
        self.dex_factories = {
            "raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium AMM
            "orca": "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca Whirlpool
            "meteora": "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",  # Meteora DLMM
        }

        # Track recently discovered pairs
        self.fresh_pairs = {}  # pair_address -> discovery_time
        self.callbacks = []  # List of callback functions for new discoveries

        # Monitoring state
        self.is_monitoring = False
        self.websocket_connections = {}

    async def start_realtime_monitoring(self, callback: Callable = None):
        """Start real-time monitoring of DEX factories"""
        logger.info("🚀 Starting real-time blockchain monitoring...")

        if callback:
            self.callbacks.append(callback)

        self.is_monitoring = True

        # Start monitoring tasks for each DEX
        tasks = []
        for dex_name, factory_address in self.dex_factories.items():
            task = asyncio.create_task(
                self._monitor_dex_factory(dex_name, factory_address)
            )
            tasks.append(task)

        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_old_pairs())
        tasks.append(cleanup_task)

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.is_monitoring = False
            await self._cleanup()

    async def _monitor_dex_factory(self, dex_name: str, factory_address: str):
        """Monitor a specific DEX factory for new pair creation"""
        logger.info(f"📡 Monitoring {dex_name} factory: {factory_address}")

        try:
            async with connect(self.wss_url) as websocket:
                self.websocket_connections[dex_name] = websocket

                # Subscribe to account changes for the factory
                await websocket.account_subscribe(
                    Pubkey.from_string(factory_address), commitment="confirmed"
                )

                # Also subscribe to logs mentioning the factory
                # Note: Using a simpler approach due to API compatibility
                try:
                    await websocket.logs_subscribe(
                        filter_="all",  # Listen to all logs for now
                        commitment="confirmed",
                    )
                except Exception as log_error:
                    logger.warning(
                        f"Could not subscribe to logs for {dex_name}: {log_error}"
                    )
                    # Continue with just account monitoring

                logger.info(f"✅ Subscribed to {dex_name} factory events")

                async for message in websocket:
                    if not self.is_monitoring:
                        break

                    await self._process_factory_event(dex_name, message)

        except Exception as e:
            logger.error(f"Error monitoring {dex_name}: {e}")
            # Attempt to reconnect after a delay
            if self.is_monitoring:
                await asyncio.sleep(5)
                await self._monitor_dex_factory(dex_name, factory_address)

    async def _process_factory_event(self, dex_name: str, message):
        """Process incoming factory events to detect new pairs"""
        try:
            if hasattr(message, "result") and message.result:
                result = message.result

                # Check if this looks like a pair creation event
                if self._is_pair_creation_event(result):
                    await self._handle_new_pair_detected(dex_name, result)

        except Exception as e:
            logger.error(f"Error processing {dex_name} event: {e}")

    def _is_pair_creation_event(self, event_data) -> bool:
        """Heuristic to detect if this event represents a new pair creation"""
        # This is a simplified heuristic - in practice, you'd need to:
        # 1. Parse transaction logs more carefully
        # 2. Look for specific instruction signatures
        # 3. Check for token mint creation patterns

        # For now, we'll use simple heuristics
        event_str = str(event_data).lower()

        pair_indicators = ["initialize", "create_pool", "new_pair", "liquidity", "mint"]

        return any(indicator in event_str for indicator in pair_indicators)

    async def _handle_new_pair_detected(self, dex_name: str, event_data):
        """Handle detection of a new pair"""
        try:
            # Extract pair address from event (simplified)
            pair_address = self._extract_pair_address(event_data)

            if pair_address and pair_address not in self.fresh_pairs:
                discovery_time = datetime.utcnow()
                self.fresh_pairs[pair_address] = discovery_time

                logger.info(f"🆕 NEW PAIR DETECTED on {dex_name}: {pair_address}")

                # Get detailed pair information
                pair_info = await self._get_pair_details(pair_address, dex_name)

                if pair_info:
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            await callback(pair_info)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

        except Exception as e:
            logger.error(f"Error handling new pair: {e}")

    def _extract_pair_address(self, event_data) -> Optional[str]:
        """Extract pair address from event data (simplified implementation)"""
        # This is a placeholder - real implementation would need to:
        # 1. Parse Solana transaction logs properly
        # 2. Understand each DEX's specific event structure
        # 3. Extract the actual pair/pool address

        # For now, return None to avoid false positives
        return None

    async def _get_pair_details(
        self, pair_address: str, dex_name: str
    ) -> Optional[Dict]:
        """Get detailed information about a newly discovered pair"""
        try:
            # First, try to get info from DexScreener (might not be indexed yet)
            dexscreener_url = (
                f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}"
            )

            try:
                response = await self.http_client.get(dexscreener_url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("pair"):
                        logger.info(f"✅ Found pair on DexScreener: {pair_address}")
                        return self._format_pair_info(
                            data["pair"], dex_name, from_blockchain=True
                        )
            except Exception:
                pass  # DexScreener might not have indexed it yet

            # If not on DexScreener yet, get basic info from blockchain
            pair_info = await self._get_pair_info_from_blockchain(
                pair_address, dex_name
            )
            return pair_info

        except Exception as e:
            logger.error(f"Error getting pair details for {pair_address}: {e}")
            return None

    async def _get_pair_info_from_blockchain(
        self, pair_address: str, dex_name: str
    ) -> Optional[Dict]:
        """Get pair information directly from blockchain"""
        try:
            # Get account info for the pair
            account_info = await self.client.get_account_info(
                Pubkey.from_string(pair_address)
            )

            if not account_info.value:
                return None

            # This is a simplified implementation
            # Real implementation would need to parse the account data
            # based on each DEX's specific data structures

            discovery_time = self.fresh_pairs.get(pair_address, datetime.utcnow())
            age_minutes = (datetime.utcnow() - discovery_time).total_seconds() / 60

            return {
                "pair_address": pair_address,
                "dex_name": dex_name,
                "base_symbol": "UNKNOWN",
                "quote_symbol": "SOL",  # Most new pairs are against SOL
                "total_liquidity_usd": 0,  # Would need to calculate
                "volume_24h_usd": 0,
                "age_hours": age_minutes / 60,
                "discovery_method": "blockchain_realtime",
                "discovery_time": discovery_time.isoformat(),
                "raw_blockchain_data": True,
            }

        except Exception as e:
            logger.error(f"Error getting blockchain info for {pair_address}: {e}")
            return None

    def _format_pair_info(
        self, pair_data: Dict, dex_name: str, from_blockchain: bool = False
    ) -> Dict:
        """Format pair information for consistency"""
        discovery_time = datetime.utcnow()

        # Calculate age from creation time if available
        age_hours = 0
        if pair_data.get("pairCreatedAt"):
            created_time = datetime.fromtimestamp(pair_data["pairCreatedAt"] / 1000)
            age_hours = (discovery_time - created_time).total_seconds() / 3600

        return {
            "pair_address": pair_data.get("pairAddress", ""),
            "base_token": pair_data.get("baseToken", {}).get("address", ""),
            "quote_token": pair_data.get("quoteToken", {}).get("address", ""),
            "base_symbol": pair_data.get("baseToken", {}).get("symbol", "UNKNOWN"),
            "quote_symbol": pair_data.get("quoteToken", {}).get("symbol", "SOL"),
            "dex_name": dex_name,
            "total_liquidity_usd": float(
                pair_data.get("liquidity", {}).get("usd", 0) or 0
            ),
            "volume_24h_usd": float(pair_data.get("volume", {}).get("h24", 0) or 0),
            "price_usd": float(pair_data.get("priceUsd", 0) or 0),
            "price_change_24h": float(
                pair_data.get("priceChange", {}).get("h24", 0) or 0
            ),
            "txns_24h": (pair_data.get("txns", {}).get("h24", {}).get("buys", 0) or 0)
            + (pair_data.get("txns", {}).get("h24", {}).get("sells", 0) or 0),
            "market_cap_usd": float(pair_data.get("marketCap", 0) or 0),
            "age_hours": age_hours,
            "discovery_method": "blockchain_realtime"
            if from_blockchain
            else "dexscreener_realtime",
            "discovery_time": discovery_time.isoformat(),
            "volume_to_liquidity_ratio": 0,  # Calculate if needed
            "raw_data": pair_data,
        }

    async def get_fresh_pairs_last_24h(self) -> List[Dict]:
        """Get all pairs discovered in the last 24 hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        fresh_pairs = []
        for pair_address, discovery_time in self.fresh_pairs.items():
            if discovery_time >= cutoff_time:
                pair_info = await self._get_pair_details(pair_address, "unknown")
                if pair_info:
                    fresh_pairs.append(pair_info)

        # Sort by discovery time (newest first)
        fresh_pairs.sort(key=lambda x: x.get("discovery_time", ""), reverse=True)
        return fresh_pairs

    async def _cleanup_old_pairs(self):
        """Periodically clean up old pair records"""
        while self.is_monitoring:
            try:
                cutoff_time = datetime.utcnow() - timedelta(
                    hours=48
                )  # Keep 48h history

                pairs_to_remove = [
                    pair_addr
                    for pair_addr, discovery_time in self.fresh_pairs.items()
                    if discovery_time < cutoff_time
                ]

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
            # Close websocket connections
            for dex_name, ws in self.websocket_connections.items():
                try:
                    await ws.close()
                except Exception as e:
                    logger.error(f"Error closing {dex_name} websocket: {e}")

            # Close HTTP client
            await self.http_client.aclose()

            # Close Solana client
            await self.client.close()

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        logger.info("🛑 Stopping real-time monitoring...")
        self.is_monitoring = False


# Enhanced mempool monitoring (advanced feature)
class MempoolSniffer:
    """
    Monitor Solana mempool for pending pair creation transactions
    This gives the earliest possible detection of new pairs
    """

    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url)
        self.is_monitoring = False

    async def start_mempool_monitoring(self, callback: Callable = None):
        """Monitor mempool for pending pair creation transactions"""
        logger.info("🔍 Starting mempool monitoring (experimental)...")

        # Note: Solana doesn't have a traditional mempool like Ethereum
        # Instead, we can monitor recent transactions and catch them very quickly

        self.is_monitoring = True

        try:
            while self.is_monitoring:
                await self._scan_recent_transactions()
                await asyncio.sleep(2)  # Check every 2 seconds

        except Exception as e:
            logger.error(f"Mempool monitoring error: {e}")
        finally:
            await self.client.close()

    async def _scan_recent_transactions(self):
        """Scan recent transactions for pair creation patterns"""
        try:
            # Get recent signatures
            signatures = await self.client.get_signatures_for_address(
                Pubkey.from_string(
                    "11111111111111111111111111111111"
                ),  # System program
                limit=20,
            )

            for sig_info in signatures.value:
                if sig_info.err is None:  # Only successful transactions
                    # This is a simplified check - real implementation would
                    # need to parse transaction instructions properly
                    pass

        except Exception as e:
            logger.error(f"Error scanning recent transactions: {e}")

    def stop_monitoring(self):
        """Stop mempool monitoring"""
        self.is_monitoring = False


# Factory for creating different types of sniffers
class RealtimeSnifferFactory:
    """Factory for creating different types of real-time sniffers"""

    @staticmethod
    def create_blockchain_sniffer(
        rpc_url: str = None, wss_url: str = None
    ) -> RealtimeTokenSniffer:
        """Create a blockchain monitoring sniffer"""
        return RealtimeTokenSniffer(
            rpc_url=rpc_url or "https://api.mainnet-beta.solana.com",
            wss_url=wss_url or "wss://api.mainnet-beta.solana.com",
        )

    @staticmethod
    def create_mempool_sniffer(rpc_url: str = None) -> MempoolSniffer:
        """Create a mempool monitoring sniffer"""
        return MempoolSniffer(rpc_url=rpc_url or "https://api.mainnet-beta.solana.com")
