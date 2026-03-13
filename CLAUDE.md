# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FRC EPA inequality analysis — fetches EPA (Expected Points Added) data from the Statbotics API, computes distribution/inequality metrics, and generates visualizations.

## Commands

```bash
pip install -r requirements.txt   # install dependencies
python epa_inequality.py          # run full analysis (outputs to results/)
```

No test suite or linter is configured.

## Architecture

```
epa_inequality.py          # entry point: metrics, plots, summary table
  └─ StatboticsClient      # API client with pagination + caching
       └─ StatboticsCache  # extends TBACache with 12-hour TTL
            └─ TBACache    # base SQLite cache (indefinite retention)
```

- **tba_client.py / tba_cache.py** — Blue Alliance API client and base cache class. TBACache is the parent class for StatboticsCache.
- **statbotics_cache.py** — Overrides `get()` to enforce a 12-hour TTL. Stale entries cause a cache miss and re-fetch.
- **statbotics_client.py** — Handles pagination (`limit`/`offset`) and 0.5s rate limiting. Caches full URLs (including query params) as keys.
- **epa_inequality.py** — All metric functions are pure NumPy (no SciPy dependency) and accept a plain `np.ndarray`. Plots use matplotlib and save to `results/`.

## Key Design Decisions

- Cache DBs (`statbotics_cache.db`, `tba_cache.db`) are gitignored and can be deleted to force a full refresh.
- The `.env` file holds `TBA_API_KEY` for Blue Alliance (not needed for Statbotics analysis).
- `requirements.txt` is UTF-16 encoded.
