import time
import requests
from typing import Any
from statbotics_cache import StatboticsCache


class StatboticsClient:
    """
    Statbotics API client with SQLite caching and pagination.

    All API calls are cached in SQLite database. Subsequent calls
    return cached data without hitting the API.
    """

    BASE_URL = "https://api.statbotics.io/v3"

    def __init__(self, cache_db: str = "statbotics_cache.db"):
        self.cache = StatboticsCache(cache_db)
        self.headers = {"User-Agent": "FRC-EPA-Analysis/1.0"}

    def _make_request(self, url: str) -> Any:
        """
        Make an API request with caching. Takes a full URL (not just endpoint)
        since paginated URLs include query parameters.
        """
        cached_data = self.cache.get(url)
        if cached_data is not None:
            return cached_data

        time.sleep(0.5)  # Be polite to the server
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        self.cache.set(url, data, response.status_code)

        return data

    def get_team_years(self, year: int, min_count: int = 1) -> list[dict]:
        """
        Fetch ALL team-year records for a given year, handling pagination.

        Args:
            year: Competition year
            min_count: Minimum record.count to include (default 1)

        Returns:
            List of team-year dicts, filtered to teams with record.count >= min_count
        """
        all_results = []
        offset = 0
        limit = 1000

        while True:
            url = f"{self.BASE_URL}/team_years?year={year}&limit={limit}&offset={offset}"
            page = self._make_request(url)
            all_results.extend(page)
            if len(page) < limit:
                break
            offset += limit

        return [
            t for t in all_results
            if t.get("record", {}).get("count", 0) >= min_count
        ]

    def get_epa_values(self, year: int, min_count: int = 1) -> list[float]:
        """
        Convenience method: returns sorted EPA mean values for a year.

        Extracts epa.total_points.mean from each team-year record.
        Filters out teams with record.count < min_count.

        Returns:
            Sorted list of EPA values
        """
        team_years = self.get_team_years(year, min_count)
        values = []
        for t in team_years:
            epa = t.get("epa", {}).get("total_points", {}).get("mean")
            if epa is not None:
                values.append(epa)
        return sorted(values)

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_stats()
