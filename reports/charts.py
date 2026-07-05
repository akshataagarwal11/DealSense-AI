"""Matplotlib chart generation for the DealSense PDF report."""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle

SCORE_COLORS_HEX = {
    "High": "#C0392B",
    "Medium": "#D68910",
    "Low": "#1E7B34",
}
NAVY = "#1F3864"

# Gauge zones read left-to-right as Low -> Medium -> High, matching the
# spec's "Low=left, Medium=center, High=right" layout.
_ZONE_ANGLES = {
    "Low": (120, 180),
    "Medium": (60, 120),
    "High": (0, 60),
}
_NEEDLE_ANGLE_DEG = {
    "Low": 150,
    "Medium": 90,
    "High": 30,
}


def generate_gauge_chart(score: str, confidence: int, output_path: str) -> str:
    """Semicircle gauge with a needle pointing at the risk zone. Saves PNG, returns path."""
    fig, ax = plt.subplots(figsize=(4, 2.6))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.55, 1.15)
    ax.set_aspect("equal")
    ax.axis("off")

    for zone, (start, end) in _ZONE_ANGLES.items():
        ax.add_patch(Wedge((0, 0), 1.0, start, end,
                            facecolor=SCORE_COLORS_HEX[zone],
                            edgecolor="white", linewidth=2))

    angle = math.radians(_NEEDLE_ANGLE_DEG.get(score, 90))
    needle_x, needle_y = 0.82 * math.cos(angle), 0.82 * math.sin(angle)
    ax.plot([0, needle_x], [0, needle_y], color=NAVY, linewidth=3,
            solid_capstyle="round", zorder=5)
    ax.add_patch(Circle((0, 0), 0.06, color=NAVY, zorder=6))

    color = SCORE_COLORS_HEX.get(score, NAVY)
    ax.text(0, -0.28, f"{score} Risk", ha="center", va="center",
            fontsize=16, fontweight="bold", color=color)
    ax.text(0, -0.45, f"Confidence: {confidence}%", ha="center", va="center",
            fontsize=10, color="#555555")

    fig.savefig(output_path, dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return output_path


def generate_risk_factor_chart(risk_factors: list, output_path: str) -> str:
    """Horizontal bar chart of risk factors, colored and sized by severity."""
    severity_weight = {"High": 3, "Medium": 2, "Low": 1}

    factors = [rf["factor"] for rf in risk_factors][::-1]
    severities = [rf["severity"] for rf in risk_factors][::-1]
    widths = [severity_weight.get(s, 1) for s in severities]
    colors = [SCORE_COLORS_HEX.get(s, "#888888") for s in severities]

    fig, ax = plt.subplots(figsize=(6.6, 0.5 * max(len(factors), 3) + 1))
    y_pos = range(len(factors))
    ax.barh(y_pos, widths, color=colors, height=0.6)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(factors, fontsize=9)
    ax.set_xlim(0, 3.6)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["Low", "Medium", "High"])
    ax.set_xlabel("Severity")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
