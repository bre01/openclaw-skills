"""
Enhanced Visualizer with Auto-Routing and Advanced Chart Types.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns

from style_config import StyleConfig, StyleManager, COLORBLIND_PALETTE
from auto_viz_router import AutoVizRouter, VizConfigBuilder


class EnhancedVisualizer:
    """Enhanced visualizer with auto-routing and advanced charts."""
    
    def __init__(self, style: Union[str, StyleConfig] = 'ieee', auto_route: bool = True):
        """
        Initialize visualizer.
        
        Args:
            style: Style name or StyleConfig
            auto_route: Enable automatic visualization type selection
        """
        if isinstance(style, str):
            self.config = StyleManager.get_style(style)
        else:
            self.config = style
        
        self.style_name = style if isinstance(style, str) else 'custom'
        StyleManager.apply_style(self.config)
        
        self.auto_route = auto_route
        self.router = AutoVizRouter()
        self.config_builder = VizConfigBuilder(self.router)
        
    def plot(self, data: Dict[str, Any], viz_type: Optional[str] = None, **kwargs) -> Figure:
        """
        Generate visualization with automatic or manual type selection.
        
        Args:
            data: Experiment data
            viz_type: Optional explicit visualization type
            **kwargs: Additional parameters
            
        Returns:
            Matplotlib Figure
        """
        # Handle wrapper structure
        if 'data' in data and 'source' in data:
            exp_data = data['data']
        else:
            exp_data = data
        
        # Determine visualization type
        if viz_type is None and self.auto_route:
            recommendation = self.router.route(data)
            viz_type = recommendation['primary']['type']
            print(f"Auto-selected: {viz_type} (confidence: {recommendation['primary']['confidence']:.2f})")
        elif viz_type is None:
            # Fallback to experiment type
            exp_type = exp_data.get('experiment_type', 'unknown')
            viz_type = self._experiment_type_to_viz_type(exp_type)
        
        # Build configuration
        config = self.config_builder.build_config(data, viz_type)
        
        # Route to appropriate generator
        if viz_type == 'confusion_matrix_heatmap':
            return self.plot_confusion_matrix(exp_data, **config['options'], **kwargs)
        elif viz_type == 'model_comparison_bar':
            return self.plot_comparison_bar(exp_data, **config['options'], **kwargs)
        elif viz_type == 'model_comparison_radar':
            return self.plot_comparison_radar(exp_data, **config['options'], **kwargs)
        elif viz_type == 'ablation_study':
            return self.plot_ablation(exp_data, **config['options'], **kwargs)
        elif viz_type == 'training_curves':
            return self.plot_training_curves(exp_data, **config['options'], **kwargs)
        elif viz_type == 'grouped_comparison':
            return self.plot_grouped_comparison(exp_data, **config['options'], **kwargs)
        else:
            raise ValueError(f"Unknown visualization type: {viz_type}")
    
    def _experiment_type_to_viz_type(self, exp_type: str) -> str:
        """Map experiment type to visualization type."""
        mapping = {
            'confusion_matrix': 'confusion_matrix_heatmap',
            'model_comparison': 'model_comparison_bar',
            'ablation': 'ablation_study',
            'training_curve': 'training_curves',
            'hardware_comparison': 'grouped_comparison'
        }
        return mapping.get(exp_type, 'model_comparison_bar')
    
    def plot_confusion_matrix(self, data: Dict, 
                             normalize: bool = True,
                             show_precision_recall: bool = True,
                             cmap: str = 'Blues',
                             figsize: Optional[Tuple] = None,
                             title: Optional[str] = None,
                             annotate: bool = True,
                             **kwargs) -> Figure:
        """Plot confusion matrix as heatmap."""
        matrix = np.array(data.get('matrix', []))
        labels = data.get('labels', [f'Class {i}' for i in range(len(matrix))])
        
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
        ax.set_xticklabels(labels, fontsize=self.config.tick_size)
        ax.set_yticklabels(labels, fontsize=self.config.tick_size)
        
        if len(labels) > 5:
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        # Colorbar
        cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.set_ylabel('Percentage (%)' if normalize else 'Count', 
                          rotation=-90, va="bottom", fontsize=self.config.label_size)
        
        # Annotations
        if annotate:
            for i in range(len(labels)):
                for j in range(len(labels)):
                    val = matrix_norm[i, j]
                    text_color = "white" if val > matrix_norm.max() * 0.6 else "black"
                    text = f"{val:.1f}" if normalize else f"{int(val)}"
                    ax.text(j, i, text, ha="center", va="center", 
                           color=text_color, fontsize=max(6, self.config.tick_size - 1))
        
        ax.set_xlabel("Predicted Label", fontsize=self.config.label_size)
        ax.set_ylabel("True Label", fontsize=self.config.label_size)
        ax.set_title(title or "Confusion Matrix", fontsize=self.config.title_size)
        
        # Add precision/recall table
        if show_precision_recall and len(labels) <= 10:
            precision = data.get('per_class_precision', [])
            recall = data.get('per_class_recall', [])
            
            if precision and recall:
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
                           horizontal: bool = False,
                           sort_by: Optional[str] = None,
                           show_values: bool = True,
                           value_format: str = '{:.2f}',
                           error_bars: Optional[Dict] = None,
                           figsize: Optional[Tuple] = None,
                           title: Optional[str] = None,
                           **kwargs) -> Figure:
        """Plot model comparison as bar chart."""
        models_data = data.get('models', [])
        
        if not models_data:
            raise ValueError("No model data provided")
        
        model_names = [m['name'] for m in models_data]
        
        # Get metrics
        all_metrics = set()
        for m in models_data:
            all_metrics.update(k for k in m.keys() if k != 'name')
        metrics = sorted(list(all_metrics))
        
        if not metrics:
            raise ValueError("No metrics found")
        
        # Sort models if requested
        if sort_by and sort_by in metrics:
            models_data = sorted(models_data, key=lambda x: x.get(sort_by, 0), reverse=True)
            model_names = [m['name'] for m in models_data]
        
        # Determine layout
        n_metrics = len(metrics)
        if n_metrics <= 2:
            n_cols, n_rows = n_metrics, 1
        elif n_metrics <= 4:
            n_cols, n_rows = 2, 2
        else:
            n_cols, n_rows = 3, (n_metrics + 2) // 3
        
        figsize = figsize or (4 * n_cols, 3 * n_rows)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, squeeze=False)
        axes = axes.flatten()
        
        colors = COLORBLIND_PALETTE[:len(model_names)]
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            values = [m.get(metric, 0) for m in models_data]
            
            errs = error_bars.get(metric) if error_bars else None
            
            x = np.arange(len(model_names))
            
            if horizontal:
                bars = ax.barh(x, values, height=self.config.bar_width, 
                              color=colors, xerr=errs)
                ax.set_yticks(x)
                ax.set_yticklabels(model_names)
                ax.set_xlabel(metric.replace('_', ' ').title())
                
                if show_values:
                    for bar, val in zip(bars, values):
                        width = bar.get_width()
                        ax.text(width, bar.get_y() + bar.get_height()/2.,
                               value_format.format(val),
                               ha='left', va='center', fontsize=7, 
                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
            else:
                bars = ax.bar(x, values, width=self.config.bar_width, 
                             color=colors, yerr=errs)
                ax.set_xticks(x)
                ax.set_xticklabels(model_names, rotation=30, ha='right')
                ax.set_ylabel(metric.replace('_', ' ').title())
                
                if show_values:
                    for bar, val in zip(bars, values):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               value_format.format(val),
                               ha='center', va='bottom', fontsize=7)
            
            ax.set_title(metric.replace('_', ' ').title(), fontsize=self.config.title_size)
            ax.grid(axis='x' if horizontal else 'y', alpha=0.3)
        
        # Hide unused subplots
        for idx in range(n_metrics, len(axes)):
            axes[idx].axis('off')
        
        fig.suptitle(title or "Model Comparison", fontsize=self.config.title_size + 1, y=1.02)
        plt.tight_layout()
        return fig
    
    def plot_comparison_radar(self, data: Dict,
                             metrics: Optional[List[str]] = None,
                             normalize: bool = True,
                             fill_area: bool = True,
                             show_grid: bool = True,
                             figsize: Optional[Tuple] = None,
                             title: Optional[str] = None,
                             **kwargs) -> Figure:
        """Plot model comparison as radar chart."""
        models_data = data.get('models', [])
        
        if not models_data:
            raise ValueError("No model data")
        
        model_names = [m['name'] for m in models_data]
        
        # Get metrics
        if metrics is None:
            metrics = sorted([k for k in models_data[0].keys() if k != 'name'])
        
        n_metrics = len(metrics)
        if n_metrics < 3:
            raise ValueError("Radar chart requires at least 3 metrics")
        
        # Prepare data
        values = []
        for m in models_data:
            model_values = [m.get(metric, 0) for metric in metrics]
            values.append(model_values)
        
        # Normalize if requested
        if normalize:
            values_np = np.array(values)
            min_vals = values_np.min(axis=0)
            max_vals = values_np.max(axis=0)
            ranges = max_vals - min_vals
            ranges[ranges == 0] = 1  # Avoid division by zero
            values_np = (values_np - min_vals) / ranges
            values = values_np.tolist()
        
        # Create radar chart
        figsize = figsize or (8, 8)
        fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        colors = COLORBLIND_PALETTE[:len(model_names)]
        
        for i, (model_name, model_values) in enumerate(zip(model_names, values)):
            model_values += model_values[:1]  # Complete the circle
            
            ax.plot(angles, model_values, 'o-', linewidth=2, 
                   label=model_name, color=colors[i])
            
            if fill_area:
                ax.fill(angles, model_values, alpha=0.15, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax.set_ylim(0, 1 if normalize else None)
        
        if show_grid:
            ax.grid(True)
        
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.set_title(title or "Model Comparison (Radar)", 
                    fontsize=self.config.title_size, y=1.08)
        
        return fig
    
    def plot_ablation(self, data: Dict,
                     metric: str = 'accuracy',
                     show_deltas: bool = True,
                     sort_by_impact: bool = True,
                     baseline_color: str = '#1f77b4',
                     variant_color: str = '#ff7f0e',
                     figsize: Optional[Tuple] = None,
                     title: Optional[str] = None,
                     **kwargs) -> Figure:
        """Plot ablation study results."""
        variants = data.get('variants', [])
        baseline_name = data.get('baseline')
        
        if not variants:
            raise ValueError("No ablation variants")
        
        # Extract values
        names = []
        values = []
        deltas = []
        is_baseline = []
        
        for v in variants:
            name = v['name']
            val = v.get('metrics', {}).get(metric, v.get(metric, 0))
            
            names.append(name)
            values.append(val)
            is_baseline.append(name == baseline_name)
            
            if show_deltas and 'deltas' in v and metric in v['deltas']:
                deltas.append(v['deltas'][metric])
            else:
                deltas.append(0)
        
        # Sort by impact if requested
        if sort_by_impact and not all(d == 0 for d in deltas):
            # Sort by absolute delta (descending)
            sorted_indices = sorted(range(len(deltas)), 
                                   key=lambda i: abs(deltas[i]), reverse=True)
            names = [names[i] for i in sorted_indices]
            values = [values[i] for i in sorted_indices]
            deltas = [deltas[i] for i in sorted_indices]
            is_baseline = [is_baseline[i] for i in sorted_indices]
        
        figsize = figsize or (max(6, len(names) * 0.6), 4)
        fig, ax = plt.subplots(figsize=figsize)
        
        # Colors
        colors = [baseline_color if b else variant_color for b in is_baseline]
        
        x = np.arange(len(names))
        bars = ax.bar(x, values, width=self.config.bar_width, color=colors, 
                     edgecolor='black', linewidth=0.5)
        
        # Add value labels
        for bar, val, name, delta in zip(bars, values, names, deltas):
            height = bar.get_height()
            label = f'{val:.3f}' if val < 1 else f'{val:.1f}'
            
            if show_deltas and name != baseline_name and delta != 0:
                label += f'\n({delta:+.3f})'
            
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label, ha='center', va='bottom', fontsize=8)
        
        # Baseline reference line
        if baseline_name:
            baseline_val = values[names.index(baseline_name)] if baseline_name in names else None
            if baseline_val:
                ax.axhline(y=baseline_val, color='gray', linestyle='--', 
                          alpha=0.5, label=f'Baseline ({baseline_val:.3f})')
        
        ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=self.config.label_size)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha='right', fontsize=self.config.tick_size)
        ax.set_title(title or f"Ablation Study - {metric.title()}", 
                    fontsize=self.config.title_size)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_training_curves(self, data: Dict,
                            smooth: bool = True,
                            smooth_window: int = 5,
                            highlight_best: bool = True,
                            dual_axis: bool = False,
                            y_labels: List[str] = ['Loss', 'Accuracy'],
                            figsize: Optional[Tuple] = None,
                            title: Optional[str] = None,
                            **kwargs) -> Figure:
        """Plot training curves."""
        epochs = data.get('epochs', list(range(len(list(data.get('curves', {}).values())[0]))))
        curves = data.get('curves', {})
        
        if not curves:
            raise ValueError("No curve data")
        
        figsize = figsize or (10, 4)
        
        # Separate curves by type
        loss_curves = {k: v for k, v in curves.items() if 'loss' in k.lower()}
        acc_curves = {k: v for k, v in curves.items() 
                     if any(x in k.lower() for x in ['acc', 'accuracy'])}
        other_curves = {k: v for k, v in curves.items() 
                       if k not in loss_curves and k not in acc_curves}
        
        n_plots = sum([bool(loss_curves), bool(acc_curves)])
        if n_plots == 0:
            n_plots = 1
        
        if dual_axis and loss_curves and acc_curves:
            fig, ax1 = plt.subplots(figsize=figsize)
            ax2 = ax1.twinx()
            
            colors = COLORBLIND_PALETTE
            
            # Plot loss on left axis
            for idx, (name, values) in enumerate(loss_curves.items()):
                y = self._smooth(values, smooth_window) if smooth else values
                x = epochs[:len(y)]
                ax1.plot(x, y, label=name, color=colors[idx], linewidth=2)
            
            ax1.set_xlabel('Epoch', fontsize=self.config.label_size)
            ax1.set_ylabel(y_labels[0] if y_labels else 'Loss', 
                          color=colors[0], fontsize=self.config.label_size)
            ax1.tick_params(axis='y', labelcolor=colors[0])
            ax1.grid(alpha=0.3)
            
            # Plot accuracy on right axis
            best_val, best_epoch = None, None
            for idx, (name, values) in enumerate(acc_curves.items()):
                y = self._smooth(values, smooth_window) if smooth else values
                x = epochs[:len(y)]
                ax2.plot(x, y, label=name, color=colors[len(loss_curves) + idx], 
                        linewidth=2, linestyle='--')
                
                if highlight_best and 'val' in name.lower():
                    best_idx = np.argmax(y)
                    best_val = y[best_idx]
                    best_epoch = x[best_idx]
            
            ax2.set_ylabel(y_labels[1] if len(y_labels) > 1 else 'Accuracy',
                          color=colors[len(loss_curves)], fontsize=self.config.label_size)
            ax2.tick_params(axis='y', labelcolor=colors[len(loss_curves)])
            
            if best_epoch is not None:
                ax2.axvline(x=best_epoch, color='red', linestyle=':', alpha=0.5)
                ax2.scatter([best_epoch], [best_val], color='red', s=100, zorder=5)
            
            # Combined legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
            
        else:
            fig, axes = plt.subplots(1, n_plots, figsize=(figsize[0] * n_plots, figsize[1]), 
                                    squeeze=False)
            axes = axes.flatten()
            ax_idx = 0
            
            colors = COLORBLIND_PALETTE
            
            if loss_curves:
                ax = axes[ax_idx]
                for idx, (name, values) in enumerate(loss_curves.items()):
                    y = self._smooth(values, smooth_window) if smooth else values
                    x = epochs[:len(y)]
                    ax.plot(x, y, label=name, color=colors[idx], linewidth=2)
                ax.set_xlabel('Epoch')
                ax.set_ylabel('Loss')
                ax.set_title('Training Loss')
                ax.legend()
                ax.grid(alpha=0.3)
                ax_idx += 1
            
            if acc_curves:
                ax = axes[ax_idx]
                best_val, best_epoch = None, None
                for idx, (name, values) in enumerate(acc_curves.items()):
                    y = self._smooth(values, smooth_window) if smooth else values
                    x = epochs[:len(y)]
                    ax.plot(x, y, label=name, color=colors[idx], linewidth=2)
                    
                    if highlight_best and 'val' in name.lower():
                        best_idx = np.argmax(y)
                        best_val = y[best_idx]
                        best_epoch = x[best_idx]
                
                if best_epoch is not None:
                    ax.axvline(x=best_epoch, color='red', linestyle=':', alpha=0.5)
                    ax.scatter([best_epoch], [best_val], color='red', s=100, zorder=5)
                
                ax.set_xlabel('Epoch')
                ax.set_ylabel('Accuracy')
                ax.set_title('Training Accuracy')
                ax.legend()
                ax.grid(alpha=0.3)
        
        fig.suptitle(title or "Training Curves", fontsize=self.config.title_size + 1, y=1.02)
        plt.tight_layout()
        return fig
    
    def plot_grouped_comparison(self, data: Dict,
                               platforms: List[str] = None,
                               conditions: List[str] = None,
                               show_speedup: bool = True,
                               n_cols: int = 3,
                               figsize: Optional[Tuple] = None,
                               title: Optional[str] = None,
                               **kwargs) -> Figure:
        """Plot grouped comparison (e.g., hardware platforms at different frequencies)."""
        models_data = data.get('models', [])
        
        if not models_data:
            raise ValueError("No model data")
        
        # Auto-detect platforms and conditions from column names
        if platforms is None or conditions is None:
            first_model = models_data[0]
            keys = [k for k in first_model.keys() if k != 'name']
            
            platforms = set()
            conditions = set()
            
            for key in keys:
                key_lower = key.lower()
                if 'linux' in key_lower:
                    platforms.add('Linux')
                if 'zephyr' in key_lower:
                    platforms.add('Zephyr')
                
                import re
                mhz_match = re.search(r'(\d+)mhz', key_lower)
                if mhz_match:
                    conditions.add(f"{mhz_match.group(1)} MHz")
            
            platforms = sorted(list(platforms))
            conditions = sorted(list(conditions))
        
        n_models = len(models_data)
        n_conditions = len(conditions)
        
        # Create subplots: one per condition
        figsize = figsize or (4 * n_conditions, 3)
        fig, axes = plt.subplots(1, n_conditions, figsize=figsize, squeeze=False)
        axes = axes.flatten()
        
        colors = COLORBLIND_PALETTE[:len(platforms)]
        x = np.arange(n_models)
        width = 0.8 / len(platforms)
        
        for cond_idx, condition in enumerate(conditions):
            ax = axes[cond_idx]
            
            for plat_idx, platform in enumerate(platforms):
                # Construct column name (e.g., "linux_408mhz")
                col_name = f"{platform.lower()}_{condition.replace(' ', '').lower()}"
                
                values = [m.get(col_name, 0) for m in models_data]
                offset = (plat_idx - len(platforms)/2 + 0.5) * width
                
                bars = ax.bar(x + offset, values, width, label=platform, color=colors[plat_idx])
                
                # Add value labels
                for bar, val in zip(bars, values):
                    if val > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                               f'{val:.1f}', ha='center', va='bottom', fontsize=6)
            
            ax.set_ylabel('Time (ms)' if 'time' in str(data.get('experiment_type', '')) else 'Value',
                         fontsize=self.config.label_size)
            ax.set_title(condition, fontsize=self.config.title_size)
            ax.set_xticks(x)
            ax.set_xticklabels([m['name'] for m in models_data], 
                              rotation=30, ha='right', fontsize=self.config.tick_size)
            ax.legend(fontsize=self.config.legend_size)
            ax.grid(axis='y', alpha=0.3)
        
        fig.suptitle(title or "Hardware Comparison", fontsize=self.config.title_size + 1, y=1.02)
        plt.tight_layout()
        return fig
    
    def _smooth(self, y: List[float], window: int = 5) -> List[float]:
        """Apply moving average smoothing."""
        if len(y) < window:
            return y
        return np.convolve(y, np.ones(window)/window, mode='valid').tolist()
    
    def save(self, fig: Figure, output_path: str, formats: Optional[List[str]] = None):
        """Save figure to file(s)."""
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
