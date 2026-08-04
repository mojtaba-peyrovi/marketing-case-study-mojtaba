"""
Shared chart styling — applies the Company's brand palette to all matplotlib/seaborn figures.

Brand palette (anonymized for this case study):
  primary:  #9D4EDD  (purple)
  accent:   #FF0066  (pink-red)
  soft:     #C77DFF  (light purple)
  dark:     #1A1A2E  (near-black)
  muted:    #6C757D  (grey)
  bg:       #FAFAFA  (off-white)

Typography: uses DejaVu Sans (matplotlib default, close to DM Sans)
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

PRIMARY   = "#9D4EDD"
ACCENT    = "#FF0066"
SOFT      = "#C77DFF"
DARK      = "#1A1A2E"
MUTED     = "#6C757D"
BG        = "#FAFAFA"
LIGHT_BG  = "#F3E8FF"

PALETTE = [PRIMARY, ACCENT, SOFT, "#7B2FBE", "#FF4D8D", "#E0AAFF", MUTED, "#3D0066"]
MARKET_COLORS = {
    "German":  PRIMARY,
    "French":  ACCENT,
    "English": SOFT,
    "UNKNOWN": MUTED,
}


def apply_brand_style():
    """Apply global matplotlib style matching the Company's branding."""
    mpl.rcParams.update({
        "figure.facecolor":   BG,
        "axes.facecolor":     BG,
        "axes.edgecolor":     "#DDDDDD",
        "axes.labelcolor":    DARK,
        "axes.titlesize":     14,
        "axes.titleweight":   "bold",
        "axes.labelsize":     11,
        "axes.grid":          True,
        "grid.color":         "#E8E8E8",
        "grid.linewidth":     0.8,
        "xtick.color":        DARK,
        "ytick.color":        DARK,
        "text.color":         DARK,
        "font.family":        "DejaVu Sans",
        "font.size":          10,
        "legend.frameon":     False,
        "legend.fontsize":    9,
        "figure.titlesize":   15,
        "figure.titleweight": "bold",
        "savefig.facecolor":  BG,
        "savefig.bbox":       "tight",
        "savefig.dpi":        150,
    })
    sns.set_palette(PALETTE)


def save_chart(fig, path):
    """Save figure with consistent settings and close it."""
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"    Chart saved -> {path}")
