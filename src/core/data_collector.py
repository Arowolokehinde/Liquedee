import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings

from ..database.models import LiquiditySnapshot, PairAlert, TokenPair
from .dexscreener import DexScreenerClient
from .liquidity_analyzer import LiquidityAnalyzer
from .solana_client import SolanaClient

logger = logging.getLogger(__name__)


class DataCollector:
    """Main data collection orchestrator"""

    def __init__(self):
        self.dexscreener = DexScreenerClient()
        self.solana = SolanaClient()
        self.analyzer = LiquidityAnalyzer()

        # Database setup
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Collection settings
        self.collection_interval = 30  # seconds
        self.min_liquidity_threshold = 10000  # $10k minimum
        self.running = False

    async def start_collection(self):
        """Start the data collection process"""
        logger.info("🚀 Starting data collection...")
        self.running = True

        while self.running:
            try:
                await self._collect_cycle()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Collection cycle error: {e}")
                await asyncio.sleep(5)  # Short delay on error

    async def _collect_cycle(self):
        """Single data collection cycle"""
        cycle_start = datetime.utcnow()
        logger.info(f"📊 Starting collection cycle at {cycle_start}")

        # Get latest pairs from DexScreener
        raw_pairs = await self.dexscreener.get_latest_pairs()
        logger.info(f"📥 Retrieved {len(raw_pairs)} pairs from DexScreener")

        processed_pairs = 0
        new_pairs = 0
        alerts_generated = 0

        for raw_pair in raw_pairs:
            try:
                # Parse pair data
                pair_data = self.dexscreener.parse_pair_data(raw_pair)
                if not pair_data:
                    continue

                # Skip low liquidity pairs
                if pair_data["total_liquidity_usd"] < self.min_liquidity_threshold:
                    continue

                # Store/update pair in database
                pair_stored = await self._store_pair_data(pair_data)
                if pair_stored:
                    new_pairs += 1

                # Store liquidity snapshot
                await self._store_liquidity_snapshot(pair_data)

                # Analyze for alerts
                alert = await self.analyzer.analyze_pair(pair_data)
                if alert:
                    await self._store_alert(alert)
                    alerts_generated += 1

                processed_pairs += 1

            except Exception as e:
                logger.error(
                    f"Error processing pair {pair_data.get('pair_address', 'unknown')}: {e}"
                )

        cycle_end = datetime.utcnow()
        duration = (cycle_end - cycle_start).total_seconds()

        logger.info(f"✅ Collection cycle complete:")
        logger.info(f"   📊 Processed: {processed_pairs} pairs")
        logger.info(f"   🆕 New pairs: {new_pairs}")
        logger.info(f"   🚨 Alerts: {alerts_generated}")
        logger.info(f"   ⏱️  Duration: {duration:.2f}s")

    async def _store_pair_data(self, pair_data: Dict) -> bool:
        """Store pair data in database"""
        try:
            session = self.SessionLocal()

            # Check if pair already exists
            existing_pair = (
                session.query(TokenPair)
                .filter_by(pair_address=pair_data["pair_address"])
                .first()
            )

            if not existing_pair:
                # Create new pair
                new_pair = TokenPair(
                    pair_address=pair_data["pair_address"],
                    base_token=pair_data["base_token"],
                    quote_token=pair_data["quote_token"],
                    base_symbol=pair_data["base_symbol"],
                    quote_symbol=pair_data["quote_symbol"],
                    dex_name=pair_data["dex_name"],
                    pool_address=pair_data["pool_address"],
                )
                session.add(new_pair)
                session.commit()
                session.close()
                return True
            else:
                # Update existing pair
                existing_pair.updated_at = datetime.utcnow()
                session.commit()
                session.close()
                return False

        except Exception as e:
            logger.error(f"Error storing pair data: {e}")
            return False

    async def _store_liquidity_snapshot(self, pair_data: Dict):
        """Store liquidity snapshot"""
        try:
            session = self.SessionLocal()

            snapshot = LiquiditySnapshot(
                pair_address=pair_data["pair_address"],
                total_liquidity_usd=pair_data["total_liquidity_usd"],
                base_liquidity=pair_data["base_liquidity"],
                quote_liquidity=pair_data["quote_liquidity"],
                volume_24h_usd=pair_data["volume_24h_usd"],
                price_usd=pair_data["price_usd"],
                price_change_24h=pair_data["price_change_24h"],
                txns_24h=pair_data["txns_24h"],
                buyers_24h=pair_data["buyers_24h"],
                sellers_24h=pair_data["sellers_24h"],
                fdv_usd=pair_data["fdv_usd"],
                market_cap_usd=pair_data["market_cap_usd"],
                raw_data=pair_data["raw_data"],
            )

            session.add(snapshot)
            session.commit()
            session.close()

        except Exception as e:
            logger.error(f"Error storing liquidity snapshot: {e}")

    async def _store_alert(self, alert_data: Dict):
        """Store generated alert"""
        try:
            session = self.SessionLocal()

            alert = PairAlert(
                pair_address=alert_data["pair_address"],
                alert_type=alert_data["alert_type"],
                confidence_score=alert_data["confidence_score"],
                liquidity_usd=alert_data["liquidity_usd"],
                volume_24h_usd=alert_data.get("volume_24h_usd"),
                alert_data=alert_data,
            )

            session.add(alert)
            session.commit()
            session.close()

            logger.info(
                f"🚨 Alert generated: {alert_data['alert_type']} for {alert_data['pair_address']}"
            )

        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    async def stop_collection(self):
        """Stop data collection"""
        logger.info("🛑 Stopping data collection...")
        self.running = False
        await self.dexscreener.close()
        await self.solana.close()
