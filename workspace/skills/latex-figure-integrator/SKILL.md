---
name: latex-figure-integrator
description: Integrate generated figures into LaTeX documents with smart features. Generate figure environments, automatic captions with data source attribution, multi-figure layouts, and consistent styling. Enhanced with cleveref support, automatic table label generation, and figure placement optimization. Export high-resolution PNG (300 DPI) and vector PDF. Use when: (1) inserting figures into LaTeX papers, (2) generating figure captions with data provenance, (3) creating multi-panel figure layouts, (4) ensuring figure consistency with paper style, (5) managing figure numbering and references.

**当以下情况时使用此 Skill**：
(1) 需要将图表集成到 LaTeX 文档
(2) 需要自动生成带数据来源的图注
(3) 需要生成多面板图表 (subfigure)
(4) 需要使用 cleveref 进行智能引用
(5) 需要优化图表在文档中的位置
---

# LaTeX Figure Integrator (Enhanced)

Integrate generated experiment figures into LaTeX documents with smart features and automatic optimization.

## What's New in v2.0

### 🧠 Smart Caption Generation
- Automatic source attribution ("Based on Table 3")
- Cleveref support for smart references (`\Cref{fig:results}`)
- Auto-detection of table/figure references

### 📋 Automatic Table Label Generation
```latex
% Auto-generated labels for source tables
\label{tab:1}  % Table I
\label{tab:2}  % Table II
```

### 📄 Enhanced Preamble
- All required packages included
- Color definitions
- Graphics path configuration
- Hyperref setup

### 🎯 Figure Placement Optimization
- Preferred page assignment
- Ordering constraints
- Automatic layout suggestions

## Quick Start

### Basic Usage

```python
from scripts.enhanced_latex_generator import EnhancedLatexGenerator
from scripts.figure_manager import FigureManager

manager = FigureManager()
manager.add_figure(
    image_path="figures/result.pdf",
    caption="Model performance comparison.",
    label="fig:performance",
    source_table="Table 2"  # Auto-attributed in caption
)

generator = EnhancedLatexGenerator(document_class='ieee')
latex_code = generator.generate_smart_figures(manager)
```

### Standalone Document

```python
standalone = generator.generate_standalone_document(
    manager,
    title="Experimental Results",
    author="Your Name"
)
```

## Smart Features

### Automatic Source Attribution

```python
manager.add_figure(
    image_path="fig1.pdf",
    caption="Inference time comparison.",
    source_table="Table I",        # Generates: Based on Table~\ref{tab:1}.
    source_section="Section IV"    # Or: Based on Section IV.
)
```

Generates:
```latex
\caption{Inference time comparison. Based on Table~\ref{tab:1}.}
```

### Cleveref Support

```python
generator = EnhancedLatexGenerator(
    document_class='ieee',
    use_cleveref=True  # Enable smart references
)
```

Enables:
```latex
% Single reference
See \Cref{fig:performance} for results.
% Output: See Figure 1 for results.

% Multiple references
See \Cref{fig:performance,fig:memory}.
% Output: See Figures 1 and 2.
```

### Multi-Panel Figures

```python
manager.add_subfigure_group(
    subfigures=[
        {"path": "acc.pdf", "subcaption": "(a) Accuracy"},
        {"path": "loss.pdf", "subcaption": "(b) Loss"}
    ],
    layout="2x1",
    caption="Training metrics.",
    label="fig:training"
)
```

Generates:
```latex
\begin{figure}[t]
\centering
\begin{subfigure}[t]{0.45\textwidth}
  \centering
  \includegraphics[width=\linewidth]{acc.pdf}
  \caption*{(a) Accuracy}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.45\textwidth}
  \centering
  \includegraphics[width=\linewidth]{loss.pdf}
  \caption*{(b) Loss}
\end{subfigure}
\caption{Training metrics.}
\label{fig:training}
\end{figure}
```

## Document Class Presets

### IEEEtran
```python
generator = EnhancedLatexGenerator(document_class='ieee')
# - \columnwidth for single column
# - \textwidth for figure* (wide)
# - subcaption package
```

### ACM
```python
generator = EnhancedLatexGenerator(document_class='acm')
# - \linewidth
# - ACM-specific formatting
```

### NeurIPS
```python
generator = EnhancedLatexGenerator(document_class='neurips')
# - \textwidth
# - Minimal margins
```

## Generated Preamble

```latex
% Enhanced LaTeX Preamble
\usepackage{graphicx}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage{subcaption}
\usepackage{cleveref}  % Smart references
\crefname{table}{Table}{Tables}
\crefname{figure}{Figure}{Figures}

% Math
\usepackage{amsmath}
\usepackage{amssymb}

% Tables
\usepackage{booktabs}
\usepackage{array}
\usepackage{multirow}

% Colors
\usepackage{xcolor}

% Links
\usepackage{hyperref}

% Graphics path
\graphicspath{{figures/}}
```

## Figure Placement Optimization

### Add Placement Preferences

```python
from enhanced_latex_generator import FigurePlacementOptimizer

optimizer = FigurePlacementOptimizer()

# Add figures with preferred pages
optimizer.add_figure(fig1, preferred_page=3)
optimizer.add_figure(fig2, preferred_page=4)

# Add ordering constraints
optimizer.add_constraint("fig:method", "fig:results", relation="before")
optimizer.add_constraint("fig:results", "fig:ablation", relation="after")

# Optimize
optimized = optimizer.optimize()
suggestions = optimizer.suggest_placements()
```

## Output Files

### preamble.tex
Required packages and configuration.

### figures.tex
Figure environments for `\input` into main document.

### figures_standalone.tex
Complete standalone document for preview.

## Advanced Usage

### Custom Table Labels

```python
data_manager = {
    "tables": [
        {"id": "inference", "caption": "Inference Time"},
        {"id": "memory", "caption": "Memory Consumption"}
    ]
}

latex = generator.generate_smart_figures(manager, data_manager)
```

Generates:
```latex
% Auto-generated table labels
% Inference Time
% \label{tab:inference}
% Memory Consumption
% \label{tab:memory}
```

### Wide Figures (Two-Column)

```python
manager.add_figure(
    image_path="large_result.pdf",
    caption="Comprehensive comparison.",
    label="fig:large",
    wide=True  # Uses figure* environment
)
```

### Custom Widths

```python
manager.add_figure(
    image_path="result.pdf",
    caption="Results.",
    width=r"0.8\textwidth"  # Custom width
)
```

## Integration Workflow

### 1. Generate Figures
```python
# From experiment-visualizer
viz.save(fig, "figures/result")
# Creates: result.pdf, result.png
```

### 2. Add to Manager
```python
manager.add_figure(
    image_path="figures/result.pdf",
    caption="...",
    source_table="Table 1"
)
```

### 3. Generate LaTeX
```python
preamble = generator.generate_enhanced_preamble()
figures = generator.generate_smart_figures(manager)
standalone = generator.generate_standalone_document(manager)
```

### 4. Include in Document
```latex
% In preamble
\input{preamble}

% In document
\input{figures}

% Or standalone
% pdflatex figures_standalone.tex
```

## Dependencies

None - pure Python with standard library.

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `enhanced_latex_generator.py` | Smart LaTeX generation |
| `latex_generator.py` | Basic LaTeX generation |
| `figure_manager.py` | Figure organization |

## Migration from v1.0

Old code:
```python
from scripts.latex_generator import LatexFigureGenerator

generator = LatexFigureGenerator(document_class='ieee')
latex = generator.generate(manager)
```

New code:
```python
from scripts.enhanced_latex_generator import EnhancedLatexGenerator

generator = EnhancedLatexGenerator(
    document_class='ieee',
    use_cleveref=True,  # New!
    use_subcaption=True
)
latex = generator.generate_smart_figures(manager, data_manager)
```
