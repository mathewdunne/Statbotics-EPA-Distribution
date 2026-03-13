# FRC EPA Inequality Analysis

Analyzes the distribution of EPA (Expected Points Added) across FRC teams over time using data from the [Statbotics API](https://api.statbotics.io). Generates inequality metrics (Gini coefficient, percentile ratios, top/bottom shares, etc.) and visualizations saved to `results/`.

## Setup

```bash
pip install -r requirements.txt
python epa_inequality.py
```

Plots are saved to the `results/` directory. A summary table of metrics is printed to the console.

## Caching

API responses are cached in a local SQLite database (`statbotics_cache.db`) so repeated runs don't re-fetch data. The Statbotics cache has a **12-hour TTL** — after that, entries are treated as stale and re-fetched on the next run. To force a full refresh, delete `statbotics_cache.db`.

## Custom Analysis

### Changing the year range

Edit the `years` list in the `__main__` block of `epa_inequality.py`:

```python
years = list(range(2002, 2026))  # all available years
```

### Filtering teams

`get_epa_values` and `get_team_years` accept a `min_count` parameter that filters out teams with fewer than N matches played. Increase this to focus on teams with more data:

```python
client.get_epa_values(2024, min_count=6)  # only teams with 6+ matches
```

### Using metrics independently

Every metric function in `epa_inequality.py` takes a plain numpy array and returns a scalar, so you can use them on any dataset:

| Function | Returns |
| --- | --- |
| `gini_coefficient(values)` | Gini coefficient (0 = equal, 1 = maximally unequal) |
| `top_share(values, pct)` | Fraction of total EPA held by the top X% |
| `middle_tier_share(values)` | Fraction of total EPA held by P25–P75 |
| `percentile_ratios(values)` | `(P90/P50, P50/P10)` tuple |
| `coefficient_of_variation(values)` | Standard deviation / mean |
| `skewness(values)` | Fisher's skewness |
| `kurtosis(values)` | Fisher's excess kurtosis |

Example:

```python
from statbotics_client import StatboticsClient
from epa_inequality import gini_coefficient, top_share, percentile_ratios
import numpy as np

client = StatboticsClient()
epa = np.array(client.get_epa_values(2024, min_count=1))

print(f"Gini: {gini_coefficient(epa):.3f}")
print(f"Top 10% share: {top_share(epa, 0.10):.1%}")
print(f"P90/P50 ratio: {percentile_ratios(epa)[0]:.2f}")
```

### Accessing raw team data

Use `get_team_years` for the full team-year records (EPA breakdowns, win/loss record, etc.):

```python
teams = client.get_team_years(2024, min_count=1)
for t in teams[:3]:
    print(t["team"], t["epa"]["total_points"]["mean"])
```
