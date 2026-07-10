import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger("ai-service.memory.long_term")

class LongTermMemory:
    """
    Retrieves user profile context, preferences, and historical statistics.
    Communicates with the NestJS backend endpoints. Falls back to mock profiles
    if the backend is unreachable.
    """
    def __init__(self, backend_url: str = "http://localhost:5000"):
        self.backend_url = backend_url

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Fetches the theme, language, and custom travel preferences of a user."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.backend_url}/api/users/{user_id}/preferences")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch real preferences from NestJS: {e}. Using fallback.")
        
        # Safe mock fallback
        return {
            "theme": "dark",
            "language": "en",
            "travelPrefs": {
                "preferred_class": "3A",
                "seat_preference": "lower",
                "food_preference": "veg",
                "favorite_stations": ["NDLS", "BPL", "R"]
            }
        }

    async def get_travel_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves past completed and scheduled trips for the user."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.backend_url}/api/users/{user_id}/trips")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch trips from NestJS: {e}. Using fallback.")
            
        return [
            {
                "id": "mock-trip-1",
                "source": "NDLS",
                "destination": "BPL",
                "journeyDate": "2026-06-15T06:00:00Z",
                "status": "completed"
            },
            {
                "id": "mock-trip-2",
                "source": "BPL",
                "destination": "R",
                "journeyDate": "2026-07-02T11:25:00Z",
                "status": "completed"
            }
        ]

    async def get_pnr_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves list of PNR tracks associated with the user."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.backend_url}/api/users/{user_id}/pnrs")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch PNR history: {e}. Using fallback.")
            
        return [
            {
                "pnr": "4210987654",
                "journeyDate": "2026-07-20T00:00:00Z",
                "prediction": "CNF",
                "actualStatus": "unknown"
            }
        ]

long_term_memory = LongTermMemory()
