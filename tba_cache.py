import sqlite3
import json
from datetime import datetime
from typing import Optional, Any
import os


class TBACache:
    """SQLite-based cache for Blue Alliance API responses."""

    def __init__(self, db_path: str = "tba_cache.db"):
        """Initialize the cache with the specified database path."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                url TEXT PRIMARY KEY,
                response_data TEXT NOT NULL,
                cached_at TIMESTAMP NOT NULL,
                status_code INTEGER NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def get(self, url: str) -> Optional[dict]:
        """
        Retrieve cached response for a URL.

        Args:
            url: The API endpoint URL

        Returns:
            Cached JSON response as dict, or None if not cached
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT response_data, status_code FROM api_cache WHERE url = ?",
            (url,)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            response_data, status_code = result
            if status_code == 200:
                return json.loads(response_data)

        return None

    def set(self, url: str, response_data: Any, status_code: int = 200):
        """
        Cache an API response.

        Args:
            url: The API endpoint URL
            response_data: The JSON response data (dict or list)
            status_code: HTTP status code
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO api_cache (url, response_data, cached_at, status_code)
            VALUES (?, ?, ?, ?)
            """,
            (url, json.dumps(response_data), datetime.now(), status_code)
        )

        conn.commit()
        conn.close()

    def clear(self):
        """Clear all cached data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_cache")
        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM api_cache")
        total_entries = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(cached_at), MAX(cached_at) FROM api_cache")
        result = cursor.fetchone()
        oldest, newest = result

        conn.close()

        return {
            "total_entries": total_entries,
            "oldest_entry": oldest,
            "newest_entry": newest
        }
