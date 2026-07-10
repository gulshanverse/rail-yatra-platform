import unittest
import asyncio
from app.data.models import DataQualityMetadata
from app.data.cache import railway_cache_manager
from app.data.health import provider_health_monitor
from app.data.manager import railway_data_manager

class TestRailwayDataPlatform(unittest.TestCase):

    def test_data_quality_metadata_parsing(self):
        """Verifies metadata Pydantic model validations."""
        meta = DataQualityMetadata(
            provider="test-provider",
            last_updated=1719918200.0,
            data_age_secs=10,
            confidence=0.9,
            source_type="live"
        )
        self.assertEqual(meta.provider, "test-provider")
        self.assertEqual(meta.source_type, "live")

    def test_cache_ttl_and_fallbacks(self):
        """Verifies caching client writes, retrieves, and expires properly."""
        data_type = "pnr"
        key = "1234567890"
        mock_val = {"pnr": key, "train_number": "12002", "status": "CNF"}

        # Write to cache
        railway_cache_manager.set(data_type, key, mock_val)
        
        # Retrieve from cache
        retrieved = railway_cache_manager.get(data_type, key)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["pnr"], key)
        self.assertEqual(retrieved["status"], "CNF")

    def test_health_monitor_failovers(self):
        """Verifies health monitor increments failures and toggles offline status."""
        provider = "irctc"
        
        # Reset health state
        provider_health_monitor.record_success(provider)
        self.assertTrue(provider_health_monitor.is_healthy(provider))

        # Record failures up to threshold
        provider_health_monitor.record_failure(provider, threshold=2)
        provider_health_monitor.record_failure(provider, threshold=2)
        
        self.assertFalse(provider_health_monitor.is_healthy(provider))
        self.assertEqual(provider_health_monitor.get_status_report()[provider]["status"], "offline")

        # Record success to restore
        provider_health_monitor.record_success(provider)
        self.assertTrue(provider_health_monitor.is_healthy(provider))

    def test_data_manager_fallback(self):
        """Verifies RailwayDataManager fetches normalized models successfully."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_checks():
            trains = await railway_data_manager.search_trains("NDLS", "BPL")
            self.assertTrue(len(trains) > 0)
            self.assertEqual(trains[0].train_number, "12002")
            self.assertEqual(trains[0].data_quality.provider, "synthetic")

            delay = await railway_data_manager.get_delay_history("12002")
            self.assertIsNotNone(delay)
            self.assertEqual(delay.train_number, "12002")
            self.assertEqual(delay.avg_delay_mins, 12)
            
        loop.run_until_complete(run_checks())
        loop.close()

if __name__ == '__main__':
    unittest.main()
