import logging
import asyncio
from app.config.config import settings
from app.data.providers.synthetic import SyntheticRailwayProvider
from app.data.cache import railway_cache_manager

logger = logging.getLogger("ai-service.data.syncer")


class BackgroundRailwaySyncer:
    """
    Asynchronous background sync worker that polls external providers (or synthetic adapter)
    at configurable intervals and updates the local Redis cache.
    """

    def __init__(self):
        self.provider = SyntheticRailwayProvider()
        self.running = False

    async def start(self) -> None:
        """Launches the background syncer loop task."""
        if self.running:
            return
        self.running = True
        logger.info(
            f"Starting Background Railway Syncer loop (Interval: {settings.SYNC_INTERVAL_SECS} seconds)..."
        )
        asyncio.create_task(self._sync_loop())

    async def _sync_loop(self) -> None:
        while self.running:
            try:
                logger.info("Executing background railway data synchronization...")

                # In development, we refresh cache entries for popular trains
                target_trains = ["12002", "12626", "12434", "22692", "12860"]
                for t_num in target_trains:
                    # Sync delay history
                    delay_info = await self.provider.get_delay_history(t_num)
                    if delay_info:
                        # Convert model to dict for serialization
                        railway_cache_manager.set(
                            "delay", t_num, delay_info.model_dump()
                        )

                    # Sync schedules / details
                    trains = await self.provider.search_trains(
                        "NDLS", "BPL"
                    )  # Ndls-Bpl sector schedules
                    for t in trains:
                        railway_cache_manager.set(
                            "schedule", t.train_number, t.model_dump()
                        )

                logger.info("Background railway data sync completed successfully.")
            except Exception as e:
                logger.error(f"Error in background sync worker loop: {e}")

            # Sleep for the configured interval duration
            await asyncio.sleep(settings.SYNC_INTERVAL_SECS)

    def stop(self) -> None:
        self.running = False
        logger.info("Background Railway Syncer loop stopped.")


railway_background_syncer = BackgroundRailwaySyncer()
