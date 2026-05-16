"""
Main Visualizer Module
Unified interface for generating experiment visualizations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import numpy as np

from style_config import StyleConfig, StyleManager, COLORBLIND_PALETTE


class ExperimentVisualizer:
    """Main interface for creating publication-quality experiment figures."""
    
    def __init__(self, style: Union[str, StyleConfig] = 'ieee'):
        """
        Initialize visualizer with style.
        
        Args:
            style: Style name ('ieee', 'acm', 'neurips', 'default') or StyleConfig
        """
        if isinstance(style, str):
            self.config = StyleManager.get_style(style)
        else:
            self.config = style
        
        self.style_name = style if isinstance(style, str) else 'custom'
        StyleManager.apply_style(self.config)
    
    def plot(self, data: Dict[str, Any], **kwargs) -> Figure:
        """
        Auto-select and generate appropriate visualization.
        
        Args:
            data: Experiment data dictionary (can be {source, data} or direct experiment data)
            **kwargs: Additional plotting parameters
        
        Returns:
            Matplotlib Figure object
        """
        # Handle both {source, data} structure and direct data
        if 'data' in data and 'source' in data:
            exp_data = data['data']
        else:
            exp_data = data
        
        exp_type = exp_data.get('experiment_type', exp_data.get('type', 'unknown'))
        
        if exp_type == 'confusion_matrix':
            return self.plot_confusion_matrix(data, **kwargs)
        elif exp_type == 'model_comparison':
            return self.plot_comparison_bar(data, **kwargs)
        elif exp_type == 'ablation':
            return self.plot_ablation(data, **kwargs)
        elif exp_type == 'training_curve':
            return self.plot_training_curves(data, **kwargs)
        else:
            raise ValueError(f"Unknown experiment type: {exp_type}")
    
    def plot_confusion_matrix(self, data: Dict, 
                             normalize: bool = True,
                             show_precision_recall: bool = True,
                             cmap: str = 'Blues',
                             figsize: Optional[Tuple] = None,
                             title: Optional[str] = None,
                             **kwargs) -> Figure:
        """
        Plot confusion matrix as heatmap.
        
        Args:
            data: Dict with 'matrix', 'labels', optional 'per_class_precision/recall'
            normalize: Whether to normalize to percentages
            show_precision_recall: Add precision/recall annotations
            cmap: Colormap name
            figsize: Figure size tuple
            title: Plot title
        """
        matrix = np.array(data.get('matrix', data.get('data', {}).get('matrix', [])))
        labels = data.get('labels', data.get('data', {}).get('labels', []))
        
        if matrix.size == 0:
            raise ValueError("Empty confusion matrix")
        
        if normalize:
            row_sums = matrix.sum(axis=1, keepdims=True)
            matrix_norm = matrix / row_sums * 100
        else:
            matrix_norm = matrix
        
        figsize = figsize or self.config.figure_size
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot heatmap
        im = ax.imshow(matrix_norm, cmap=cmap, aspect='auto')
        
        # Set ticks
        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        
        # Rotate x labels if many classes
        if len(labels) > 5:
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.set_ylabel('Percentage (%)' if normalize else 'Count', rotation=-90, va="bottom")
        
        # Add text annotations
        for i in range(len(labels)):
            for j in range(len(labels)):
                val = matrix_norm[i, j]
                text_color = "white" if val > matrix_norm.max() * 0.6 else "black"
                text = f"{val:.1f}" if normalize else f"{int(val)}"
                ax.text(j, i, text, ha="center", va="center", color=text_color, fontsize=8)
        
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("True Label")
        ax.set_title(title or "Confusion Matrix")
        
        # Add precision/recall annotations if available
        if show_precision_recall:
            precision = data.get('per_class_precision') or data.get('data', {}).get('per_class_precision', [])
            recall = data.get('per_class_recall') or data.get('data', {}).get('per_class_recall', [])
            
            if precision and recall:
                # Add table below
                table_data = [[f"{p:.3f}" for p in precision], [f"{r:.3f}" for r in recall]]
                table = ax.table(
                    cellText=table_data,
                    rowLabels=['Precision', 'Recall'],
                    colLabels=labels,
                    loc='bottom',
                    cellLoc='center'
                )
                table.auto_set_font_size(False)
                table.set_fontsize(7)
                table.scale(1, 1.5)
                plt.subplots_adjust(bottom=0.2)
        
        plt.tight_layout()
        return fig
    
    def plot_comparison_bar(self, data: Dict,
                           metrics: Optional[List[str]] = None,
                           error_bars: Optional[Dict] = None,
                           significance: Optional[Dict] = None,
                           figsize: Optional[Tuple] = None,
                           title: Optional[str] = None,
                           **kwargs) -> Figure:
        """
        Plot model comparison as bar chart.
        
        Args:
            data: Dict with 'models' list
            metrics: List of metrics to plot (default: all)
            error_bars: Dict of error values per metric
            significance: Dict of significance markers
            figsize: Figure size
            title: Plot title
        """
        models_data = data.get('models', data.get('data', {}).get('models', []))
        
        if not models_data:
            raise ValueError("No model data provided")
        
        # Extract model names and metrics
        model_names = [m['name'] for m in models_data]
        
        # Get all available metrics
        all_metrics = set()
        for m in models_data:
            all_metrics.update(k for k in m.keys() if k != 'name')
        
        metrics = metrics or sorted(list(all_metrics))
        
        figsize = figsize or (len(model_names) * 1.2 + 2, self.config.figure_size[1])
        
        n_metrics = len(metrics)
        if n_metrics == 0:
            raise ValueError("No metrics found")
        
        fig, axes = plt.subplots(1, n_metrics, figsize=figsize, squeeze=False)
        axes = axes.flatten()
        
        colors = COLORBLIND_PALETTE[:len(model_names)]
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            
            values = [m.get(metric, 0) for m in models_data]
            
            # Get error bars if provided
            errs = None
            if error_bars and metric in error_bars:
                errs = error_bars[metric]
            
            x = np.arange(len(model_names))
            bars = ax.bar(x, values, width=self.config.bar_width, color=colors, 
                         yerr=errs, capsize=3 if errs else 0)
            
            # Add value labels on bars
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.3f}' if val < 1 else f'{val:.1f}',
                       ha='center', va='bottom', fontsize=7)
            
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_xticks(x)
            ax.set_xticklabels(model_names, rotation=30, ha='right')
            ax.set_title(metric.replace('_', ' ').title())
            
            # Add significance markers
            if significance:
                for (m1, m2), marker in significance.items():
                    if m1 in model_names and m2 in model_names:
                        i1, i2 = model_names.index(m1), model_names.index(m2)
                        y_max = max(values[i1], values[i2])
                        ax.plot([i1, i2], [y_max * 1.05, y_max * 1.05], 'k-', linewidth=1)
                        ax.text((i1 + i2) / 2, y_max * 1.08, marker, ha='center', fontsize=8)
        
        fig.suptitle(title or "Model Comparison", y=1.02)
        plt.tight_layout()
        return fig
    
    def plot_ablation(self, data: Dict,
                     metric: str = 'accuracy',
                     show_deltas: bool = True,
                     figsize: Optional[Tuple] = None,
                     title: Optional[str] = None,
                     **kwargs) -> Figure:
        """
        Plot ablation study results.
        
        Args:
            data: Dict with 'baseline' and 'variants'
            metric: Metric to visualize
            show_deltas: Show performance difference from baseline
            figsize: Figure size
            title: Plot title
        """
        variants = data.get('variants', data.get('data', {}).get('variants', []))
        baseline_name = data.get('baseline', data.get('data', {}).get('baseline'))
        
        if not variants:
            raise ValueError("No ablation variants provided")
        
        # Extract names and values
        names = [v['name'] for v in variants]
        values = [v.get('metrics', {}).get(metric, v.get(metric, 0)) for v in variants]
        
        # Find baseline value
        baseline_val = None
        for v in variants:
            if v['name'] == baseline_name:
                baseline_val = v.get('metrics', {}).get(metric, v.get(metric, 0))
                break
        
        figsize = figsize or (len(names) * 0.8 + 2, self.config.figure_size[1])
        fig, ax = plt.subplots(figsize=figsize)
        
        # Determine colors (baseline different)
        colors = []
        for name in names:
            if name == baseline_name:
                colors.append(self.config.primary_color)
            else:
                colors.append(self.config.secondary_color)
        
        x = np.arange(len(names))
        bars = ax.bar(x, values, width=self.config.bar_width, color=colors)
        
        # Add value labels
        for bar, val, name in zip(bars, values, names):
            height = bar.get_height()
            label = f'{val:.3f}' if val < 1 else f'{val:.1f}'
            
            # Add delta if showing
            if show_deltas and baseline_val is not None and name != baseline_name:
                delta = val - baseline_val
                label += f'\n({delta:+.3f})'
            
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label, ha='center', va='bottom', fontsize=7)
        
        # Add baseline reference line
        if baseline_val is not None:
            ax.axhline(y=baseline_val, color='gray', linestyle='--', alpha=0.5, 
                      label=f'Baseline ({baseline_val:.3f})')
        
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha='right')
        ax.set_title(title or f"Ablation Study - {metric.title()}")
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_training_curves(self, data: Dict,
                            smooth: bool = False,
                            smooth_window: int = 5,
                            highlight_best: bool = True,
                            figsize: Optional[Tuple] = None,
                            title: Optional[str] = None,
                            **kwargs) -> Figure:
        """
        Plot training/validation curves.
        
        Args:
            data: Dict with training data
            smooth: Apply smoothing to curves
            smooth_window: Window size for smoothing
            highlight_best: Mark best validation point
            figsize: Figure size
            title: Plot title
        """
        epochs = data.get('epochs', data.get('data', {}).get('epochs', []))
        curves = data.get('curves', data.get('data', {}).get('curves', {}))
        
        if not curves:
            raise ValueError("No curve data provided")
        
        figsize = figsize or self.config.figure_size
        
        # Separate loss and accuracy curves
        loss_curves = {k: v for k, v in curves.items() if 'loss' in k.lower()}
        acc_curves = {k: v for k, v in curves.items() if any(x in k.lower() for x in ['acc', 'accuracy', 'metric'])}
        other_curves = {k: v for k, v in curves.items() 
                       if k not in loss_curves and k not in acc_curves}
        
        n_plots = sum([bool(loss_curves), bool(acc_curves), bool(other_curves)])
        
        fig, axes = plt.subplots(1, n_plots, figsize=(figsize[0] * n_plots, figsize[1]), squeeze=False)
        axes = axes.flatten()
        ax_idx = 0
        
        def smooth_curve(y, window=smooth_window):
            if len(y) < window:
                return y
            return np.convolve(y, np.ones(window)/window, mode='valid')
        
        colors = COLORBLIND_PALETTE
        
        # Plot loss curves
        if loss_curves:
            ax = axes[ax_idx]
            for idx, (name, values) in enumerate(loss_curves.items()):
                y = smooth_curve(values) if smooth else values
                x = epochs[:len(y)] if len(y) != len(epochs) else epochs
                ax.plot(x, y, label=name, color=colors[idx % len(colors)])
            ax.set_xlabel('Epoch')
            ax.set_ylabel('Loss')
            ax.set_title('Training Loss')
            ax.legend()
            ax_idx += 1
        
        # Plot accuracy curves
        if acc_curves:
            ax = axes[ax_idx]
            best_val = None
            best_epoch = None
            for idx, (name, values) in enumerate(acc_curves.items()):
                y = smooth_curve(values) if smooth else values
                x = epochs[:len(y)] if len(y) != len(epochs) else epochs
                ax.plot(x, y, label=name, color=colors[idx % len(colors)])
                
                # Track best validation
                if 'val' in name.lower() and highlight_best:
                    best_idx = np.argmax(y)
                    if best_val is None or y[best_idx] > best_val:
                        best_val = y[best_idx]
                        best_epoch = x[best_idx]
            
            if best_epoch is not None:
                ax.axvline(x=best_epoch, color='red', linestyle='--', alpha=0.5)
                ax.scatter([best_epoch], [best_val], color='red', s=50, zorder=5)
            
            ax.set_xlabel('Epoch')
            ax.set_ylabel('Accuracy')
            ax.set_title('Training Accuracy')
            ax.legend()
            ax_idx += 1
        
        # Plot other curves
        if other_curves:
            ax = axes[ax_idx]
            for idx, (name, values) in enumerate(other_curves.items()):
                y = smooth_curve(values) if smooth else values
                x = epochs[:len(y)] if len(y) != len(epochs) else epochs
                ax.plot(x, y, label=name, color=colors[idx % len(colors)])
            ax.set_xlabel('Epoch')
            ax.set_ylabel('Value')
            ax.set_title('Other Metrics')
            ax.legend()
        
        fig.suptitle(title or "Training Curves", y=1.02)
        plt.tight_layout()
        return fig
    
    def save(self, fig: Figure, output_path: str, formats: Optional[List[str]] = None):
        """
        Save figure to file(s).
        
        Args:
            fig: Matplotlib Figure
            output_path: Base output path (without extension)
            formats: List of formats ('png', 'pdf', 'svg'). Default: ['png', 'pdf']
        """
        formats = formats or ['png', 'pdf']
        output_path = Path(output_path)
        base_path = output_path.parent / output_path.stem
        
        saved_paths = []
        for fmt in formats:
            if fmt == 'png':
                path = f"{base_path}.png"
                fig.savefig(path, dpi=self.config.dpi, bbox_inches='tight', 
                           pad_inches=self.config.pad_inches)
                saved_paths.append(path)
            elif fmt == 'pdf':
                path = f"{base_path}.pdf"
                fig.savefig(path, format='pdf', bbox_inches='tight',
                           pad_inches=self.config.pad_inches)
                saved_paths.append(path)
            elif fmt == 'svg':
                path = f"{base_path}.svg"
                fig.savefig(path, format='svg', bbox_inches='tight')
                saved_paths.append(path)
        
        return saved_paths