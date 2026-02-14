import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Style ──────────────────────────────────────────────

BG = "#1e1e2e"
FG = "#cdd6f4"
GRID = "#45475a"
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


def chart_score_histogram(distribution: list[dict]) -> bytes:
    """Histogram of per-user average bands."""
    if not distribution:
        return _empty_chart("No data")

    bins = [float(r["band_bucket"]) for r in distribution]
    counts = [r["cnt"] for r in distribution]
    colors = [_band_color(b) for b in bins]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(bins, counts, color=colors, width=0.4, alpha=BAR_ALPHA)
    ax.set_xlabel("Average Band")
    ax.set_ylabel("Users")
    ax.set_xlim(0, 9.5)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(True, axis="y")
    ax.set_title("User Score Distribution", fontsize=13, fontweight="bold", pad=12)

    return _to_png(fig)
