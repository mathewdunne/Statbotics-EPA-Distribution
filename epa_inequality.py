import matplotlib.pyplot as plt
import numpy as np
from statbotics_client import StatboticsClient

client = StatboticsClient()


# ---------------------------------------------------------------------------
# Metric functions (pure numpy, no scipy)
# ---------------------------------------------------------------------------

def gini_coefficient(values: np.ndarray) -> float:
    """Compute the Gini coefficient. Shifts values so min=0 if negatives exist."""
    shifted = values - values.min() if values.min() < 0 else values.copy()
    if shifted.sum() == 0:
        return 0.0
    sorted_vals = np.sort(shifted)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * sorted_vals) - (n + 1) * np.sum(sorted_vals)) / (n * np.sum(sorted_vals))


def top_share(values: np.ndarray, top_pct: float) -> float:
    """Fraction of total EPA held by the top X% of teams."""
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    cutoff_idx = int(n * (1 - top_pct))
    top_sum = sorted_vals[cutoff_idx:].sum()
    total_sum = sorted_vals.sum()
    return top_sum / total_sum if total_sum != 0 else 0.0


def percentile_ratios(values: np.ndarray) -> tuple[float, float]:
    """Returns (P90/P50, P50/P10) ratios."""
    p10 = np.percentile(values, 10)
    p50 = np.percentile(values, 50)
    p90 = np.percentile(values, 90)
    ratio_90_50 = p90 / p50 if p50 != 0 else float('inf')
    ratio_50_10 = p50 / p10 if p10 != 0 else float('inf')
    return ratio_90_50, ratio_50_10


def coefficient_of_variation(values: np.ndarray) -> float:
    """Standard deviation / mean."""
    mean = np.mean(values)
    std = np.std(values, ddof=1)
    return std / mean if mean != 0 else float('inf')


def middle_tier_share(values: np.ndarray) -> float:
    """Fraction of total EPA held by teams in the P25-P75 range."""
    p25 = np.percentile(values, 25)
    p75 = np.percentile(values, 75)
    middle_sum = values[(values >= p25) & (values <= p75)].sum()
    total_sum = values.sum()
    return middle_sum / total_sum if total_sum != 0 else 0.0


def skewness(values: np.ndarray) -> float:
    """Fisher's skewness."""
    n = len(values)
    if n < 3:
        return 0.0
    mean = np.mean(values)
    std = np.std(values, ddof=1)
    if std == 0:
        return 0.0
    return (n / ((n - 1) * (n - 2))) * np.sum(((values - mean) / std) ** 3)


def kurtosis(values: np.ndarray) -> float:
    """Fisher's excess kurtosis."""
    n = len(values)
    if n < 4:
        return 0.0
    mean = np.mean(values)
    std = np.std(values, ddof=1)
    if std == 0:
        return 0.0
    m4 = np.mean((values - mean) ** 4)
    return (m4 / (std ** 4)) - 3


def gaussian_kde(data: np.ndarray, x_grid: np.ndarray, bandwidth: float = None) -> np.ndarray:
    """Simple Gaussian KDE without scipy (Silverman's rule for bandwidth)."""
    if bandwidth is None:
        bandwidth = 1.06 * np.std(data) * len(data) ** (-1 / 5)
    kernels = np.exp(-0.5 * ((x_grid[:, None] - data[None, :]) / bandwidth) ** 2)
    density = kernels.sum(axis=1) / (len(data) * bandwidth * np.sqrt(2 * np.pi))
    return density


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect_all_years(years: list[int], min_count: int = 1) -> dict[int, np.ndarray]:
    """Fetch EPA arrays for all specified years. Returns {year: np.ndarray}."""
    yearly_data = {}
    for year in years:
        print(f"  Fetching {year}...", end=" ", flush=True)
        values = client.get_epa_values(year, min_count)
        if len(values) == 0:
            print("no qualifying teams, skipping")
            continue
        yearly_data[year] = np.array(values)
        print(f"{len(values)} teams")
    return yearly_data


# ---------------------------------------------------------------------------
# Plotting functions
# ---------------------------------------------------------------------------

def plot_gini_over_time(yearly_data: dict[int, np.ndarray], save_path: str):
    years = sorted(yearly_data.keys())
    ginis = [gini_coefficient(yearly_data[y]) for y in years]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, ginis, marker='o', color='steelblue', linewidth=2, markersize=5)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Gini Coefficient", fontsize=12)
    ax.set_title("FRC EPA Inequality: Gini Coefficient Over Time", fontsize=13)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_top_shares_over_time(yearly_data: dict[int, np.ndarray], save_path: str):
    years = sorted(yearly_data.keys())
    shares_top10 = [top_share(yearly_data[y], 0.10) * 100 for y in years]
    shares_bot50 = [(1 - top_share(yearly_data[y], 0.50)) * 100 for y in years]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, shares_top10, marker='^', color='#1f77b4', linewidth=2.5, markersize=8,
            label="Top 10% of teams")
    ax.plot(years, shares_bot50, marker='v', color='#d62728', linewidth=2.5, markersize=8,
            label="Bottom 50% of teams")

    # Annotate start and end values
    ax.annotate(f'{shares_top10[0]:.1f}%', (years[0], shares_top10[0]),
                textcoords="offset points", xytext=(-35, -15), fontsize=11, color='#1f77b4', fontweight='bold')
    ax.annotate(f'{shares_top10[-1]:.1f}%', (years[-1], shares_top10[-1]),
                textcoords="offset points", xytext=(8, -5), fontsize=11, color='#1f77b4', fontweight='bold')
    ax.annotate(f'{shares_bot50[0]:.1f}%', (years[0], shares_bot50[0]),
                textcoords="offset points", xytext=(-35, 8), fontsize=11, color='#d62728', fontweight='bold')
    ax.annotate(f'{shares_bot50[-1]:.1f}%', (years[-1], shares_bot50[-1]),
                textcoords="offset points", xytext=(8, -5), fontsize=11, color='#d62728', fontweight='bold')

    ax.fill_between(years, shares_top10, shares_bot50, alpha=0.08, color='gray')
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Share of Total EPA (%)", fontsize=12)
    ax.set_title("Top 10% vs Bottom 50% Share of Total EPA", fontsize=13)
    ax.legend(fontsize=12, loc='upper right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_percentile_ratios_over_time(yearly_data: dict[int, np.ndarray], save_path: str):
    years = sorted(yearly_data.keys())
    r90_50 = []
    r50_10 = []
    for y in years:
        r1, r2 = percentile_ratios(yearly_data[y])
        r90_50.append(r1)
        r50_10.append(r2)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, r90_50, marker='o', label="P90/P50 (elite vs median)", linewidth=2, markersize=5)
    ax.plot(years, r50_10, marker='s', label="P50/P10 (median vs bottom)", linewidth=2, markersize=5)
    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Ratio", fontsize=12)
    ax.set_title("FRC EPA Percentile Ratios Over Time", fontsize=13)
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_distribution_shape(yearly_data: dict[int, np.ndarray], save_path: str):
    # Pick representative years that exist in the data
    candidates = [2005, 2010, 2015, 2019, 2025]
    plot_years = [y for y in candidates if y in yearly_data]
    if not plot_years:
        plot_years = sorted(yearly_data.keys())[::max(1, len(yearly_data) // 5)]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(plot_years)))

    for year, color in zip(plot_years, colors):
        data = yearly_data[year]
        x_min, x_max = data.min() - 5, data.max() + 5
        x_grid = np.linspace(x_min, x_max, 300)
        density = gaussian_kde(data, x_grid)
        ax.plot(x_grid, density, label=str(year), color=color, linewidth=2)

    ax.set_xlabel("EPA (total_points.mean)", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title("FRC EPA Distribution Shape Across Eras", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_skewness_kurtosis_over_time(yearly_data: dict[int, np.ndarray], save_path: str):
    years = sorted(yearly_data.keys())
    skews = [skewness(yearly_data[y]) for y in years]
    kurts = [kurtosis(yearly_data[y]) for y in years]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    l1 = ax1.plot(years, skews, marker='o', color='steelblue', linewidth=2, markersize=5, label="Skewness")
    l2 = ax2.plot(years, kurts, marker='s', color='coral', linewidth=2, markersize=5, label="Excess Kurtosis")

    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Skewness", fontsize=12, color='steelblue')
    ax2.set_ylabel("Excess Kurtosis", fontsize=12, color='coral')
    ax1.set_title("FRC EPA Distribution Shape Metrics Over Time", fontsize=13)

    lines = l1 + l2
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, fontsize=11)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_cv_over_time(yearly_data: dict[int, np.ndarray], save_path: str):
    years = sorted(yearly_data.keys())
    cvs = [coefficient_of_variation(yearly_data[y]) for y in years]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, cvs, marker='o', color='steelblue', linewidth=2, markersize=5)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Coefficient of Variation (SD / Mean)", fontsize=12)
    ax.set_title("FRC EPA Coefficient of Variation Over Time", fontsize=13)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_middle_tier_over_time(yearly_data: dict[int, np.ndarray], save_path: str):
    years = sorted(yearly_data.keys())
    shares = [middle_tier_share(yearly_data[y]) * 100 for y in years]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, shares, marker='o', color='steelblue', linewidth=2, markersize=5)
    ax.axhline(50, color='gray', linestyle='--', linewidth=1, alpha=0.5, label="50% reference")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Middle Tier Share of Total EPA (%)", fontsize=12)
    ax.set_title("FRC 'Middle Class' (P25-P75) Share of Total EPA Over Time", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_percentile_fan(yearly_data: dict[int, np.ndarray], save_path: str):
    """Normalized percentile fan chart — all values relative to that year's median."""
    years = sorted(yearly_data.keys())
    percentiles = [10, 25, 75, 90]
    labels = ["P10", "P25", "P75", "P90"]
    markers = ['v', 's', 's', '^']
    colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']

    trajectories = {p: [] for p in percentiles}
    for y in years:
        median = np.median(yearly_data[y])
        for p in percentiles:
            trajectories[p].append(np.percentile(yearly_data[y], p) / median)

    fig, ax = plt.subplots(figsize=(10, 6))
    for p, label, marker, color in zip(percentiles, labels, markers, colors):
        ax.plot(years, trajectories[p], marker=marker, label=label,
                linewidth=2, markersize=6, color=color)

    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label="Median (1.0)")
    ax.fill_between(years, trajectories[25], trajectories[75],
                     alpha=0.1, color='green', label="IQR (P25-P75)")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("EPA / Median EPA", fontsize=12)
    ax.set_title("FRC EPA Percentile Trajectories (Normalized to Median)", fontsize=13)
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


def plot_lorenz_curve(yearly_data: dict[int, np.ndarray], save_path: str):
    """Lorenz curves for selected years showing cumulative EPA share vs cumulative team share."""
    years = sorted(yearly_data.keys())
    # Pick a spread of years to avoid clutter
    selected = [years[0], years[2], years[len(years) // 2], years[-1]]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect('equal')
    ax.plot([0, 100], [0, 100], color='black', linestyle='--', linewidth=1.5, label="Perfect equality")

    colors = ['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728']
    for year, color in zip(selected, colors):
        sorted_v = np.sort(yearly_data[year])
        n = len(sorted_v)
        cum_share = np.cumsum(sorted_v) / sorted_v.sum() * 100
        team_pct = np.arange(1, n + 1) / n * 100
        g = gini_coefficient(yearly_data[year])
        ax.plot(team_pct, cum_share, linewidth=2.5, color=color,
                label=f"{year} (Gini = {g:.3f})")

    ax.set_xlabel("% of Teams (ranked by EPA)", fontsize=12)
    ax.set_ylabel("Cumulative Share of EPA (%)", fontsize=12)
    ax.set_title("Lorenz Curve — FRC EPA Distribution", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"Saved {save_path}")
    plt.close()


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary(yearly_data: dict[int, np.ndarray]):
    """Print a formatted table of all metrics for each year."""
    years = sorted(yearly_data.keys())
    print("\n" + "=" * 120)
    print(f"{'Year':>6} {'Teams':>6} {'Mean':>8} {'Median':>8} {'Gini':>6} "
          f"{'Top10%':>7} {'Top25%':>7} {'Top50%':>7} "
          f"{'P90/50':>7} {'P50/10':>7} {'CV':>6} {'Mid%':>6} {'Skew':>6} {'Kurt':>6}")
    print("-" * 120)
    for y in years:
        v = yearly_data[y]
        r1, r2 = percentile_ratios(v)
        print(f"{y:>6} {len(v):>6} {np.mean(v):>8.1f} {np.median(v):>8.1f} "
              f"{gini_coefficient(v):>6.3f} "
              f"{top_share(v, 0.10):>7.3f} {top_share(v, 0.25):>7.3f} {top_share(v, 0.50):>7.3f} "
              f"{r1:>7.2f} {r2:>7.2f} "
              f"{coefficient_of_variation(v):>6.3f} "
              f"{middle_tier_share(v) * 100:>6.1f} "
              f"{skewness(v):>6.2f} {kurtosis(v):>6.2f}")
    print("=" * 120)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.makedirs("results", exist_ok=True)

    years = list(range(2016, 2026))

    print("Fetching EPA data from Statbotics...")
    yearly_data = collect_all_years(years, min_count=1)

    print(f"\nData collected for {len(yearly_data)} years")

    # Generate all plots
    plot_gini_over_time(yearly_data, "results/epa_gini_over_time.png")
    plot_top_shares_over_time(yearly_data, "results/epa_top_shares.png")
    plot_percentile_ratios_over_time(yearly_data, "results/epa_percentile_ratios.png")
    plot_distribution_shape(yearly_data, "results/epa_distributions.png")
    plot_skewness_kurtosis_over_time(yearly_data, "results/epa_skewness_kurtosis.png")
    plot_cv_over_time(yearly_data, "results/epa_cv_over_time.png")
    plot_middle_tier_over_time(yearly_data, "results/epa_middle_tier_share.png")
    plot_percentile_fan(yearly_data, "results/epa_percentile_fan.png")
    plot_lorenz_curve(yearly_data, "results/epa_lorenz_curve.png")

    # Print summary table
    print_summary(yearly_data)

    # Cache stats
    stats = client.get_cache_stats()
    print(f"\nStatbotics cache: {stats['total_entries']} entries")
