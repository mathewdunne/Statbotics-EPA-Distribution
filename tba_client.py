import os
import requests
from typing import Optional, Any
from tba_cache import TBACache


class TBAClient:
    """
    Blue Alliance API client with SQLite caching.

    All API calls are cached in SQLite database. Subsequent calls
    return cached data without hitting the API.
    """

    BASE_URL = "https://www.thebluealliance.com/api/v3"

    def __init__(self, api_key: Optional[str] = None, cache_db: str = "tba_cache.db"):
        """
        Initialize the TBA API client.

        Args:
            api_key: The Blue Alliance API key (defaults to TBA_API_KEY env var)
            cache_db: Path to the SQLite cache database
        """
        self.api_key = api_key or os.getenv("TBA_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in TBA_API_KEY environment variable")

        self.cache = TBACache(cache_db)
        self.headers = {"X-TBA-Auth-Key": self.api_key}

    def _make_request(self, endpoint: str) -> Any:
        """
        Make an API request with caching.

        Args:
            endpoint: API endpoint (without base URL)

        Returns:
            JSON response as dict or list
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Check cache first
        cached_data = self.cache.get(url)
        if cached_data is not None:
            return cached_data

        # Cache miss - fetch from API
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()

        # Store in cache
        self.cache.set(url, data, response.status_code)

        return data

    def get_status(self) -> dict:
        """Get API status."""
        return self._make_request("status")

    def get_events(self, year: int) -> list:
        """
        Get all events for a given year.

        Args:
            year: Competition year

        Returns:
            List of event dictionaries
        """
        return self._make_request(f"events/{year}")

    def get_event_matches(self, event_key: str) -> list:
        """
        Get all matches for a given event.

        Args:
            event_key: Event key (e.g., '2026week1')

        Returns:
            List of match dictionaries
        """
        return self._make_request(f"event/{event_key}/matches")

    def get_team(self, team_key: str) -> dict:
        """
        Get team information.

        Args:
            team_key: Team key (e.g., 'frc254')

        Returns:
            Team dictionary
        """
        return self._make_request(f"team/{team_key}")

    def get_team_events(self, team_key: str, year: int) -> list:
        """
        Get all events a team participated in for a given year.

        Args:
            team_key: Team key (e.g., 'frc254')
            year: Competition year

        Returns:
            List of event dictionaries
        """
        return self._make_request(f"team/{team_key}/events/{year}")

    def get_event(self, event_key: str) -> dict:
        """
        Get event details.

        Args:
            event_key: Event key

        Returns:
            Event dictionary
        """
        return self._make_request(f"event/{event_key}")

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_stats()
