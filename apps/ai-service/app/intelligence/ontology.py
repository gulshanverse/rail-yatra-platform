# app/intelligence/ontology.py
from typing import Dict, Any
from app.intelligence.interfaces import IOntologyManager


class OntologyManager(IOntologyManager):
    def __init__(self):
        # Maps division codes to Zones
        self.division_to_zone: Dict[str, str] = {
            "DLI": "NR",  # Delhi -> Northern Railway
            "BPL": "WCR",  # Bhopal -> West Central Railway
            "AGC": "NCR",  # Agra -> North Central Railway
            "BB": "CR",  # Mumbai CSMT -> Central Railway
            "HWH": "ER",  # Howrah -> Eastern Railway
            "SBC": "SWR",  # Bangalore -> South Western Railway
        }

        # Maps station codes to Divisions
        self.station_to_division: Dict[str, str] = {
            "NDLS": "DLI",
            "DLI": "DLI",
            "NZM": "DLI",
            "BPL": "BPL",
            "AGC": "AGC",
            "CSTM": "BB",
            "HWH": "HWH",
            "SBC": "SBC",
        }

    def get_zone_for_division(self, division_code: str) -> str:
        return self.division_to_zone.get(division_code.upper().strip(), "NR")

    def get_division_for_station(self, station_code: str) -> str:
        return self.station_to_division.get(station_code.upper().strip(), "DLI")

    def get_spatial_hierarchy(self, station_code: str) -> Dict[str, Any]:
        station = station_code.upper().strip()
        division = self.get_division_for_station(station)
        zone = self.get_zone_for_division(division)

        return {
            "network": "Indian Railways Grid",
            "zone": zone,
            "division": division,
            "station": station,
        }
