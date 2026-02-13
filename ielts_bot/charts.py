import io
from datetime import date, datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

# ── Style ──────────────────────────────────────────────

BG = "#1e1e2e"
FG = "#cdd6f4"
GRID = "#45475a"
ACCENT1 = "#89b4fa"  # blue
ACCENT2 = "#a6e3a1"  # green
ACCENT3 = "#f9e2af"  # yellow
ACCENT4 = "#f38ba8"  # red
BAR_ALPHA = 0.85

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "axes.edgecolor": GRID,
    "axes.labelcolor": FG,
    "text.color": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "grid.color": GRID,
    "grid.alpha": 0.4,
    "font.size": 11,
    "font.family": "DejaVu Sans",
})


def _to_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── Growth chart ───────────────────────────────────────

def chart_growth(daily_rows: list[dict]) -> bytes:
    """Dual-axis chart: new users (bars) + sessions (line)."""
    if not daily_rows:
        return _empty_chart("No data")

    days = [r["day"] for r in daily_rows]
    new_users = [r.get("new_users", 0) for r in daily_rows]
    sessions = [r.get("sessions", 0) for r in daily_rows]

    fig, ax1 = plt.subplots(figsize=(8, 4))

    ax1.bar(days, new_users, color=ACCENT1, alpha=BAR_ALPHA, label="New users", width=0.6)
    ax1.set_ylabel("New users")
    ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    ax2 = ax1.twinx()
    ax2.plot(days, sessions, color=ACCENT2, marker="o", linewidth=2, markersize=5, label="Sessions")
    ax2.set_ylabel("Sessions")
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(days) // 10)))
    fig.autofmt_xdate(rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.6)

    ax1.grid(True, axis="y")
    ax1.set_title("Growth: users & sessions (14 days)", fontsize=13, fontweight="bold", pad=12)
    return _to_png(fig)


# ── Scores chart ───────────────────────────────────────

def chart_scores(
    daily_avg: list[dict],
    distribution: list[dict],
) -> bytes:
    """Two subplots: score trend (line) + score distribution (histogram)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [3, 2]})

    # Left: trend
    if daily_avg:
        days = [r["day"] for r in daily_avg if r.get("avg_band") is not None]
        bands = [float(r["avg_band"]) for r in daily_avg if r.get("avg_band") is not None]
        if days:
            ax1.plot(days, bands, color=ACCENT3, marker="o", linewidth=2, markersize=5)
            ax1.fill_between(days, bands, alpha=0.15, color=ACCENT3)
            ax1.set_ylim(0, 9)
            ax1.set_ylabel("Avg band")
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
            fig.autofmt_xdate(rotation=45)
            for b in [5.0, 6.0, 7.0]:
                ax1.axhline(y=b, color=GRID, linestyle="--", alpha=0.5)
                ax1.text(days[-1], b + 0.1, f"B{b:.0f}", fontsize=8, color=GRID)
        else:
            ax1.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax1.transAxes)
    else:
        ax1.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax1.transAxes)

    ax1.set_title("Score trend", fontsize=11, fontweight="bold")
    ax1.grid(True, axis="y")

    # Right: distribution
    if distribution:
        bins = [float(r["band_bucket"]) for r in distribution]
        counts = [r["cnt"] for r in distribution]
        colors = [_band_color(b) for b in bins]
        ax2.bar(bins, counts, color=colors, width=0.4, alpha=BAR_ALPHA)
        ax2.set_xlabel("Band")
        ax2.set_ylabel("Count")
        ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)

    ax2.set_title("Distribution", fontsize=11, fontweight="bold")
    ax2.grid(True, axis="y")

    fig.suptitle("Score Analytics", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    return _to_png(fig)


# ── Usage chart ────────────────────────────────────────

def chart_usage(daily_rows: list[dict]) -> bytes:
    """Bar chart: audio minutes per day + completion rate line."""
    if not daily_rows:
        return _empty_chart("No data")

    days = [r["day"] for r in daily_rows]
    audio_mins = [round(r.get("audio_minutes", 0), 1) for r in daily_rows]
    completion = [round(r.get("completion_pct", 0), 1) for r in daily_rows]

    fig, ax1 = plt.subplots(figsize=(8, 4))

    ax1.bar(days, audio_mins, color=ACCENT4, alpha=BAR_ALPHA, label="Audio (min)", width=0.6)
    ax1.set_ylabel("Audio minutes")

    ax2 = ax1.twinx()
    ax2.plot(days, completion, color=ACCENT2, marker="s", linewidth=2, markersize=5, label="Completion %")
    ax2.set_ylabel("Completion %")
    ax2.set_ylim(0, 105)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    fig.autofmt_xdate(rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.6)

    ax1.grid(True, axis="y")
    ax1.set_title("Usage: audio & completion rate (14 days)", fontsize=13, fontweight="bold", pad=12)
    return _to_png(fig)


# ── Helpers ────────────────────────────────────────────

def _band_color(band: float) -> str:
    if band >= 7.0:
        return ACCENT2
    if band >= 5.5:
        return ACCENT3
    return ACCENT4


def _empty_chart(text: str) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=14, transform=ax.transAxes)
    ax.set_axis_off()
    return _to_png(fig)
