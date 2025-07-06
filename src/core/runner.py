import asyncio
import logging
import signal

from ..database.setup import setup_database
from .data_collector import DataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CollectionRunner:
    """Main runner for data collection"""

    def __init__(self):
        self.collector = DataCollector()
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Start the collection system"""
        logger.info("🚀 Starting Liquidity Sniffer Agent...")

        # Setup database
        await setup_database()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start collection
        try:
            collection_task = asyncio.create_task(self.collector.start_collection())
            await asyncio.wait(
                [collection_task, self.shutdown_event.wait()],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except KeyboardInterrupt:
            logger.info("📡 Received interrupt signal")
        finally:
            await self.collector.stop_collection()
            logger.info("🛑 Collection stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}")
        asyncio.create_task(self._shutdown())

    async def _shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Initiating graceful shutdown...")
        self.shutdown_event.set()


async def main():
    """Main entry point"""
    runner = CollectionRunner()
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
