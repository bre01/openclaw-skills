---
name: experiment-visualizer
description: Generate deterministic, publication-quality visualizations from experimental data. Enhanced with automatic visualization type routing, advanced chart types (radar, grouped comparison), and smart layout optimization. Support confusion matrices (heatmaps), model comparisons (bar/radar charts), training curves (line plots), ablation studies (grouped bars). Match academic paper styling (IEEE/ACM/NeurIPS). Use when: (1) creating paper figures from experiment data, (2) generating confusion matrix heatmaps, (3) plotting model performance comparisons, (4) visualizing training curves, (5) styling plots for publication.

**当以下情况时使用此 Skill**：
(1) 需要从实验数据生成图表
(2) 需要根据数据类型自动选择最佳可视化方案
(3) 需要生成混淆矩阵、对比图、消融图、训练曲线
(4) 需要雷达图、分组对比图等高级图表
(5) 需要符合 IEEE/ACM/NeurIPS 学术风格的图表
---

# Experiment Visualizer (Enhanced)

Generate publication-quality visualizations with automatic type detection and advanced chart types.

## What's New in v2.0

### 🤖 Auto-Viz Router
Automatically selects the best visualization type based on data characteristics:

```python
from scripts.enhanced_visualizer import EnhancedVisualizer

viz = EnhancedVisualizer(auto_route=True)

# Automatically selects best chart type
fig = viz.plot(data)  # Could be heatmap, radar, bar chart, etc.
```

### 📊 New Chart Types
- **Radar Chart** - Multi-metric model comparison
- **Grouped Comparison** - Hardware/platform comparisons
- **Dual-Axis Training Curves** - Loss + accuracy on same plot
- **Smart Ablation** - Delta annotations, impact sorting

### 🎨 Enhanced Styling
- Automatic figure size optimization
- Colorblind-friendly palettes
- Smart label rotation for readability
- Grid and annotation customization

## Quick Start

### Automatic Visualization

```python
from scripts.enhanced_visualizer import EnhancedVisualizer

viz = EnhancedVisualizer(style='ieee', auto_route=True)

# Data with any structure
fig = viz.plot(experiment_data)

# Save in multiple formats
viz.save(fig, "figure", formats=['png', 'pdf'])
```

### Manual Control

```python
# Force specific chart type
fig = viz.plot(data, viz_type='model_comparison_radar')

# Or use specific plot functions
fig = viz.plot_confusion_matrix(data)
fig = viz.plot_comparison_radar(data)
fig = viz.plot_grouped_comparison(data)
```

## Visualization Types

### Confusion Matrix Heatmap
```python
fig = viz.plot_confusion_matrix(
    data,
    normalize=True,           # Show percentages
    show_precision_recall=True,
    annotate=True,            # Cell values
    cmap='Blues'
)
```

### Model Comparison Bar Chart
```python
fig = viz.plot_comparison_bar(
    data,
    horizontal=False,         # Vertical bars
    sort_by='accuracy',       # Sort models
    show_values=True,         # Value labels
    value_format='{:.2f}'
)
```

### Radar Chart
```python
fig = viz.plot_comparison_radar(
    data,
    metrics=['accuracy', 'f1', 'precision', 'recall', 'speed'],
    normalize=True,           # Normalize to 0-1
    fill_area=True
)
```

### Ablation Study
```python
fig = viz.plot_ablation(
    data,
    metric='accuracy',
    show_deltas=True,         # Show performance drop
    sort_by_impact=True,      # Sort by magnitude of change
    baseline_color='#1f77b4',
    variant_color='#ff7f0e'
)
```

### Training Curves
```python
fig = viz.plot_training_curves(
    data,
    smooth=True,              # Moving average
    smooth_window=5,
    highlight_best=True,      # Mark best validation
    dual_axis=True            # Loss + accuracy
)
```

### Grouped Comparison
```python
fig = viz.plot_grouped_comparison(
    data,
    platforms=['Linux', 'Zephyr'],
    conditions=['408 MHz', '600 MHz', '816 MHz'],
    show_speedup=True
)
```

## Auto-Viz Routing

### How It Works

```python
from scripts.auto_viz_router import AutoVizRouter

router = AutoVizRouter()
recommendation = router.route(data)

print(recommendation['primary']['type'])
# Output: 'model_comparison_radar'

print(recommendation['primary']['reasons'])
# Output: ['5 metrics (good for radar)', '3 models (readable on radar)']

print(recommendation['alternatives'])
# Output: [{'chart_type': 'model_comparison_bar', 'reason': '...'}]
```

### Scoring Criteria

| Data Characteristic | Radar Score | Bar Score |
|--------------------|-------------|-----------|
| 3-4 metrics | +0.3 | +0.4 |
| 5+ metrics | +0.5 | +0.2 |
| 2-5 models | +0.3 | +0.3 |
| 6+ models | -0.1 | +0.2 |

## Styling Configuration

### Built-in Styles

```python
# IEEE Transactions (default for papers)
viz = EnhancedVisualizer(style='ieee')
# - Font: Serif, 8pt
# - Figure: 3.5" x 2.5"
# - DPI: 300

# ACM Style
viz = EnhancedVisualizer(style='acm')

# NeurIPS Style
viz = EnhancedVisualizer(style='neurips')
```

### Custom Style

```python
from scripts.style_config import StyleConfig

style = StyleConfig(
    font_family='Arial',
    font_size=10,
    figure_size=(6, 4),
    dpi=300,
    color_palette='viridis'
)

viz = EnhancedVisualizer(style=style)
```

## Data Format

### Confusion Matrix
```json
{
  "experiment_type": "confusion_matrix",
  "labels": ["Cat", "Dog", "Bird"],
  "matrix": [[95, 3, 2], [4, 91, 5], [1, 2, 97]],
  "per_class_precision": [0.95, 0.95, 0.93],
  "per_class_recall": [0.95, 0.91, 0.97]
}
```

### Model Comparison
```json
{
  "experiment_type": "model_comparison",
  "models": [
    {"name": "ResNet50", "accuracy": 0.92, "params_M": 25.6},
    {"name": "ViT-B", "accuracy": 0.94, "params_M": 86.6}
  ]
}
```

### Hardware Comparison
```json
{
  "experiment_type": "hardware_comparison",
  "models": [
    {
      "name": "MNIST",
      "linux_408mhz": 3.0,
      "zephyr_408mhz": 2.8,
      "linux_600mhz": 2.1,
      "zephyr_600mhz": 1.9
    }
  ],
  "frequencies": ["408 MHz", "600 MHz"],
  "platforms": ["Linux", "Zephyr"]
}
```

## Output Formats

### High Resolution PNG
- 300 DPI
- Transparent background option
- Optimized for web viewing

### Vector PDF
- Embedded fonts
- Scalable without quality loss
- Suitable for print

### SVG (optional)
- Web-friendly
- Editable in vector software

## Advanced Features

### Smart Layout Detection
```python
# Automatically detects and warns about:
# - Too many models for radar chart
# - Need for horizontal bars
# - Subplot requirements for multiple metrics
```

### Data Smoothing
```python
fig = viz.plot_training_curves(
    data,
    smooth=True,
    smooth_window=5  # Moving average window
)
```

### Multi-Panel Figures
```python
# Multiple metrics automatically get subplots
fig = viz.plot_comparison_bar(
    data,
    # Creates 2x2 grid for 4 metrics
)
```

## Dependencies

```bash
pip install matplotlib seaborn numpy pandas
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `enhanced_visualizer.py` | Main visualizer with auto-routing |
| `auto_viz_router.py` | Intelligent chart type selection |
| `style_config.py` | Academic styling configurations |

## Migration from v1.0

Old code:
```python
from scripts.visualizer import ExperimentVisualizer

viz = ExperimentVisualizer(style='ieee')
fig = viz.plot(data)  # Limited auto-detection
```

New code:
```python
from scripts.enhanced_visualizer import EnhancedVisualizer

viz = EnhancedVisualizer(style='ieee', auto_route=True)
fig = viz.plot(data)  # Full auto-routing with recommendations

# Access routing details
print(viz.router.recommendation)
```
