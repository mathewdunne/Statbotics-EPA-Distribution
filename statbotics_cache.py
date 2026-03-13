"""SQLite-based cache for Statbotics API responses.
Reuses the TBACache implementation with a Statbotics-specific database file."""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional

from tba_cache import TBACache

TTL = timedelta(hours=12)


class StatboticsCache(TBACache):
    """Cache for Statbotics API responses, using a separate database."""

    def __init__(self, db_path: str = "statbotics_cache.db"):
        super().__init__(db_path)

    def get(self, url: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT response_data, status_code, cached_at FROM api_cache WHERE url = ?",
            (url,)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            response_data, status_code, cached_at = result
            cached_time = datetime.fromisoformat(cached_at)
            if status_code == 200 and datetime.now() - cached_time < TTL:
                return json.loads(response_data)

        return None
