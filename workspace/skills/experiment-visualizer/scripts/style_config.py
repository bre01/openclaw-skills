"""
Style Configuration Module
Academic paper styling configurations.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


@dataclass
class StyleConfig:
    """Configuration for academic figure styling."""
    
    # Font settings
    font_family: str = 'serif'
    font_size: int = 10
    title_size: int = 11
    label_size: int = 10
    tick_size: int = 9
    legend_size: int = 9
    
    # Figure settings
    figure_size: Tuple[float, float] = (6, 4)
    dpi: int = 300
    
    # Color settings
    color_palette: str = 'viridis'
    primary_color: str = '#1f77b4'
    secondary_color: str = '#ff7f0e'
    accent_color: str = '#2ca02c'
    
    # Grid settings
    grid: bool = True
    grid_alpha: float = 0.3
    grid_style: str = '--'
    
    # Line/Bar settings
    line_width: float = 1.5
    bar_width: float = 0.6
    marker_size: float = 6
    
    # Spacing
    tight_layout: bool = True
    pad_inches: float = 0.1
    
    # LaTeX
    use_latex: bool = False
    latex_preamble: List[str] = field(default_factory=list)


# Predefined academic styles
IEEE_STYLE = StyleConfig(
    font_family='serif',
    font_size=8,
    title_size=9,
    label_size=8,
    tick_size=7,
    legend_size=7,
    figure_size=(3.5, 2.5),  # Single column width
    dpi=300,
    color_palette='tab10',
    grid=True,
    grid_alpha=0.3,
    line_width=1.0,
    bar_width=0.5,
    marker_size=4,
    use_latex=False
)

ACM_STYLE = StyleConfig(
    font_family='Linux Libertine',
    font_size=9,
    title_size=10,
    label_size=9,
    tick_size=8,
    legend_size=8,
    figure_size=(3.33, 2.5),
    dpi=300,
    color_palette='tab10',
    grid=False,
    line_width=1.2,
    bar_width=0.6,
    marker_size=5,
    use_latex=False
)

NEURIPS_STYLE = StyleConfig(
    font_family='sans-serif',
    font_size=10,
    title_size=11,
    label_size=10,
    tick_size=9,
    legend_size=9,
    figure_size=(5, 3.5),
    dpi=300,
    color_palette='colorblind',
    grid=True,
    grid_alpha=0.2,
    line_width=1.5,
    bar_width=0.7,
    marker_size=6,
    use_latex=False
)

# Colorblind-friendly palettes
COLORBLIND_PALETTE = [
    '#0173B2', '#DE8F05', '#029E73', '#D55E00',
    '#CC78BC', '#CA9161', '#FBAFE4', '#949494',
    '#56B4E9', '#E69F00'
]

# Significance markers
SIGNIFICANCE_MARKERS = {
    'ns': '',           # Not significant
    '*': '*',           # p < 0.05
    '**': '**',         # p < 0.01
    '***': '***',       # p < 0.001
}


class StyleManager:
    """Manage and apply figure styles."""
    
    STYLES = {
        'ieee': IEEE_STYLE,
        'acm': ACM_STYLE,
        'neurips': NEURIPS_STYLE,
        'default': StyleConfig()
    }
    
    @classmethod
    def get_style(cls, name: str) -> StyleConfig:
        """Get a predefined style by name."""
        if name.lower() in cls.STYLES:
            return cls.STYLES[name.lower()]
        raise ValueError(f"Unknown style: {name}. Available: {list(cls.STYLES.keys())}")
    
    @classmethod
    def apply_style(cls, config: StyleConfig):
        """Apply style configuration to matplotlib."""
        plt.rcParams.update({
            'font.family': config.font_family,
            'font.size': config.font_size,
            'axes.titlesize': config.title_size,
            'axes.labelsize': config.label_size,
            'xtick.labelsize': config.tick_size,
            'ytick.labelsize': config.tick_size,
            'legend.fontsize': config.legend_size,
            'figure.dpi': config.dpi,
            'lines.linewidth': config.line_width,
            'lines.markersize': config.marker_size,
            'axes.grid': config.grid,
            'grid.alpha': config.grid_alpha,
            'grid.linestyle': config.grid_style,
            'axes.prop_cycle': plt.cycler(color=COLORBLIND_PALETTE),
        })
        
        if config.use_latex:
            plt.rcParams['text.usetex'] = True
            if config.latex_preamble:
                plt.rcParams['text.latex.preamble'] = '\n'.join(config.latex_preamble)
    
    @classmethod
    def reset_style(cls):
        """Reset matplotlib to default style."""
        plt.rcParams.update(plt.rcParamsDefault)