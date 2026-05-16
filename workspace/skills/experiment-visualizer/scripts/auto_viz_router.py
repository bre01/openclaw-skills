"""
Auto-Viz Router Module
Intelligently route data to appropriate visualization types.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class AutoVizRouter:
    """
    Automatically select the best visualization type based on data characteristics.
    """
    
    # Visualization type definitions with scoring criteria
    VIZ_TYPES = {
        'confusion_matrix_heatmap': {
            'score_fn': '_score_confusion_matrix',
            'generator': 'plot_confusion_matrix',
            'description': 'Heatmap for classification confusion matrix'
        },
        'model_comparison_bar': {
            'score_fn': '_score_model_comparison_bar',
            'generator': 'plot_comparison_bar',
            'description': 'Bar chart for comparing multiple models'
        },
        'model_comparison_radar': {
            'score_fn': '_score_model_comparison_radar',
            'generator': 'plot_comparison_radar',
            'description': 'Radar chart for multi-metric model comparison'
        },
        'ablation_study': {
            'score_fn': '_score_ablation',
            'generator': 'plot_ablation',
            'description': 'Bar chart showing ablation study results'
        },
        'training_curves': {
            'score_fn': '_score_training_curves',
            'generator': 'plot_training_curves',
            'description': 'Line plot for training/validation curves'
        },
        'grouped_comparison': {
            'score_fn': '_score_grouped_comparison',
            'generator': 'plot_grouped_comparison',
            'description': 'Grouped bar chart for multi-condition comparison'
        },
        'temporal_line': {
            'score_fn': '_score_temporal',
            'generator': 'plot_temporal',
            'description': 'Line chart for time-series data'
        }
    }
    
    def __init__(self):
        self.scores = {}
        self.recommendation = None
    
    def route(self, data: Dict) -> Dict:
        """
        Analyze data and recommend best visualization type.
        
        Args:
            data: Experiment data dictionary
            
        Returns:
            Recommendation with confidence scores
        """
        self.scores = {}
        
        # Score each visualization type
        for viz_type, config in self.VIZ_TYPES.items():
            score_fn = getattr(self, config['score_fn'])
            score, reasons = score_fn(data)
            self.scores[viz_type] = {
                'score': score,
                'reasons': reasons,
                'generator': config['generator'],
                'description': config['description']
            }
        
        # Sort by score
        sorted_scores = sorted(
            self.scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        # Get top recommendation
        best_viz, best_config = sorted_scores[0]
        
        # Get alternatives (scores within 0.2 of best)
        alternatives = [
            {'type': t, 'score': c['score'], 'reason': c['description']}
            for t, c in sorted_scores[1:]
            if c['score'] > 0.3 and best_config['score'] - c['score'] < 0.3
        ]
        
        self.recommendation = {
            'primary': {
                'type': best_viz,
                'generator': best_config['generator'],
                'confidence': best_config['score'],
                'reasons': best_config['reasons']
            },
            'alternatives': alternatives[:3],  # Top 3 alternatives
            'all_scores': {k: v['score'] for k, v in sorted_scores}
        }
        
        return self.recommendation
    
    def _score_confusion_matrix(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for confusion matrix heatmap."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        # Check for matrix structure
        if 'matrix' in exp_data:
            matrix = exp_data['matrix']
            if isinstance(matrix, (list, np.ndarray)):
                # Check if square matrix
                n = len(matrix)
                is_square = all(len(row) == n for row in matrix) if matrix else False
                
                if is_square and n >= 2:
                    score += 0.5
                    reasons.append(f"Square matrix ({n}x{n})")
                
                # Check for labels
                if 'labels' in exp_data and len(exp_data['labels']) == n:
                    score += 0.3
                    reasons.append("Labels match matrix dimensions")
        
        # Check experiment type hint
        if data.get('experiment_type') == 'confusion_matrix':
            score += 0.2
            reasons.append("Explicit confusion_matrix type")
        
        return min(score, 1.0), reasons
    
    def _score_model_comparison_bar(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for model comparison bar chart."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        # Check for models list
        if 'models' in exp_data:
            models = exp_data['models']
            n_models = len(models)
            
            if 2 <= n_models <= 10:
                score += 0.3
                reasons.append(f"{n_models} models (good for bar chart)")
            elif n_models > 10:
                score += 0.1
                reasons.append(f"{n_models} models (many, consider horizontal)")
            
            # Check for metrics
            if n_models > 0:
                first_model = models[0]
                metric_count = len([k for k in first_model.keys() if k != 'name'])
                
                if 1 <= metric_count <= 3:
                    score += 0.4
                    reasons.append(f"{metric_count} metrics (good for bar chart)")
                elif metric_count > 3:
                    score += 0.2
                    reasons.append(f"{metric_count} metrics (consider radar)")
        
        # Check experiment type
        if data.get('experiment_type') in ['model_comparison', 'hardware_comparison']:
            score += 0.3
            reasons.append("Comparison experiment type")
        
        return min(score, 1.0), reasons
    
    def _score_model_comparison_radar(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for radar chart."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        if 'models' in exp_data:
            models = exp_data['models']
            
            if len(models) >= 2:
                first_model = models[0]
                metrics = [k for k in first_model.keys() if k != 'name']
                
                if len(metrics) >= 3:
                    score += 0.5
                    reasons.append(f"{len(metrics)} metrics (good for radar)")
                
                if len(metrics) >= 5:
                    score += 0.2
                    reasons.append("Many metrics, radar shows trade-offs well")
                
                # Radar works better with fewer models
                if 2 <= len(models) <= 5:
                    score += 0.3
                    reasons.append(f"{len(models)} models (readable on radar)")
        
        if data.get('experiment_type') == 'model_comparison':
            score += 0.1
        
        return min(score, 1.0), reasons
    
    def _score_ablation(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for ablation study chart."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        # Check for variants
        if 'variants' in exp_data:
            variants = exp_data['variants']
            if len(variants) >= 2:
                score += 0.4
                reasons.append(f"{len(variants)} variants")
        
        # Check for baseline
        if 'baseline' in exp_data:
            score += 0.3
            reasons.append("Baseline defined")
        
        # Check for delta calculations
        if any('deltas' in v for v in exp_data.get('variants', [])):
            score += 0.2
            reasons.append("Delta values available")
        
        if data.get('experiment_type') == 'ablation':
            score += 0.1
            reasons.append("Explicit ablation type")
        
        return min(score, 1.0), reasons
    
    def _score_training_curves(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for training curves."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        # Check for epochs/iterations
        if 'epochs' in exp_data or 'iterations' in exp_data or 'steps' in exp_data:
            score += 0.4
            reasons.append("Temporal axis present")
        
        # Check for curves
        if 'curves' in exp_data:
            curves = exp_data['curves']
            n_curves = len(curves)
            if n_curves >= 1:
                score += 0.3
                reasons.append(f"{n_curves} curve(s)")
        
        # Check for loss/accuracy metrics
        curve_keys = [k.lower() for k in exp_data.get('curves', {}).keys()]
        if any(x in ' '.join(curve_keys) for x in ['loss', 'accuracy', 'acc', 'error']):
            score += 0.2
            reasons.append("Training metrics detected")
        
        if data.get('experiment_type') == 'training_curve':
            score += 0.1
        
        return min(score, 1.0), reasons
    
    def _score_grouped_comparison(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for grouped comparison."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        # Check for multiple conditions/platforms
        if 'models' in exp_data and len(exp_data['models']) >= 2:
            models = exp_data['models']
            
            # Check for condition-specific columns (e.g., linux_408mhz, zephyr_408mhz)
            if models:
                first_model = models[0]
                condition_cols = [k for k in first_model.keys() 
                                 if any(x in k.lower() for x in ['linux', 'zephyr', 'cpu', 'gpu', '408', '600', '816'])]
                
                if len(condition_cols) >= 4:
                    score += 0.5
                    reasons.append(f"{len(condition_cols)} condition columns")
                
                if 'frequencies' in exp_data or 'platforms' in exp_data:
                    score += 0.3
                    reasons.append("Multiple platforms/frequencies detected")
        
        if data.get('experiment_type') == 'hardware_comparison':
            score += 0.2
            reasons.append("Hardware comparison type")
        
        return min(score, 1.0), reasons
    
    def _score_temporal(self, data: Dict) -> Tuple[float, List[str]]:
        """Score suitability for temporal line chart."""
        score = 0.0
        reasons = []
        
        exp_data = data.get('data', data)
        
        # Check for temporal data
        temporal_keywords = ['time', 'epoch', 'iteration', 'step', 'round']
        
        if any(kw in str(exp_data.keys()).lower() for kw in temporal_keywords):
            score += 0.4
            reasons.append("Temporal keywords found")
        
        # Check for sequential numeric data
        for key, value in exp_data.items():
            if isinstance(value, list) and len(value) >= 5:
                if all(isinstance(v, (int, float)) for v in value[:5]):
                    # Check if values change sequentially
                    diffs = [value[i+1] - value[i] for i in range(min(len(value)-1, 10))]
                    if len(set(diffs)) <= 3:  # Roughly constant difference
                        score += 0.3
                        reasons.append(f"Sequential data in '{key}'")
                        break
        
        return min(score, 1.0), reasons


class VizConfigBuilder:
    """Build optimal visualization configuration based on data."""
    
    def __init__(self, router: AutoVizRouter):
        self.router = router
    
    def build_config(self, data: Dict, viz_type: str) -> Dict:
        """
        Build visualization configuration for specific type.
        
        Args:
            data: Experiment data
            viz_type: Visualization type
            
        Returns:
            Configuration dictionary
        """
        exp_data = data.get('data', data)
        
        if viz_type == 'confusion_matrix_heatmap':
            return self._build_confusion_config(exp_data)
        elif viz_type == 'model_comparison_bar':
            return self._build_comparison_bar_config(exp_data)
        elif viz_type == 'model_comparison_radar':
            return self._build_radar_config(exp_data)
        elif viz_type == 'ablation_study':
            return self._build_ablation_config(exp_data)
        elif viz_type == 'training_curves':
            return self._build_training_config(exp_data)
        elif viz_type == 'grouped_comparison':
            return self._build_grouped_config(exp_data)
        else:
            return {'type': viz_type, 'options': {}}
    
    def _build_confusion_config(self, data: Dict) -> Dict:
        """Build config for confusion matrix."""
        matrix = data.get('matrix', [])
        n_classes = len(matrix) if matrix else 0
        
        return {
            'type': 'confusion_matrix_heatmap',
            'options': {
                'normalize': True,
                'show_precision_recall': n_classes <= 10,
                'cmap': 'Blues',
                'figsize': (8, 6) if n_classes <= 10 else (12, 10),
                'annotate': n_classes <= 15  # Too many classes = cluttered
            }
        }
    
    def _build_comparison_bar_config(self, data: Dict) -> Dict:
        """Build config for model comparison bar chart."""
        models = data.get('models', [])
        n_models = len(models)
        
        # Determine orientation
        horizontal = n_models > 8
        
        # Determine subplot layout
        metrics = [k for k in models[0].keys() if k != 'name'] if models else []
        n_metrics = len(metrics)
        
        subplot_layout = '1xN'
        if n_metrics > 3:
            subplot_layout = '2x2' if n_metrics <= 4 else 'Nx1'
        
        return {
            'type': 'model_comparison_bar',
            'options': {
                'horizontal': horizontal,
                'subplot_layout': subplot_layout,
                'sort_by': metrics[0] if metrics else None,
                'show_values': True,
                'value_format': '{:.2f}' if any('acc' in m for m in metrics) else '{:.1f}'
            }
        }
    
    def _build_radar_config(self, data: Dict) -> Dict:
        """Build config for radar chart."""
        models = data.get('models', [])
        metrics = [k for k in models[0].keys() if k != 'name'] if models else []
        
        return {
            'type': 'model_comparison_radar',
            'options': {
                'metrics': metrics,
                'normalize': True,  # Normalize to 0-1 for radar
                'fill_area': True,
                'show_grid': True
            }
        }
    
    def _build_ablation_config(self, data: Dict) -> Dict:
        """Build config for ablation study."""
        variants = data.get('variants', [])
        
        # Find primary metric
        if variants:
            first_metrics = variants[0].get('metrics', {})
            primary_metric = list(first_metrics.keys())[0] if first_metrics else 'accuracy'
        else:
            primary_metric = 'accuracy'
        
        return {
            'type': 'ablation_study',
            'options': {
                'metric': primary_metric,
                'show_deltas': True,
                'sort_by_impact': True,
                'baseline_color': '#1f77b4',
                'variant_color': '#ff7f0e'
            }
        }
    
    def _build_training_config(self, data: Dict) -> Dict:
        """Build config for training curves."""
        curves = data.get('curves', {})
        
        # Detect loss and accuracy curves
        loss_keys = [k for k in curves.keys() if 'loss' in k.lower()]
        acc_keys = [k for k in curves.keys() if any(x in k.lower() for x in ['acc', 'accuracy'])]
        
        # Determine if we need dual axis
        dual_axis = bool(loss_keys and acc_keys)
        
        return {
            'type': 'training_curves',
            'options': {
                'smooth': True,
                'smooth_window': 5,
                'highlight_best': bool(acc_keys),
                'dual_axis': dual_axis,
                'y_labels': ['Loss', 'Accuracy'] if dual_axis else ['Value']
            }
        }
    
    def _build_grouped_config(self, data: Dict) -> Dict:
        """Build config for grouped comparison."""
        models = data.get('models', [])
        
        # Detect grouping structure
        if models:
            keys = [k for k in models[0].keys() if k != 'name']
            
            # Look for platform prefixes
            platforms = set()
            frequencies = set()
            
            for key in keys:
                if 'linux' in key.lower():
                    platforms.add('Linux')
                if 'zephyr' in key.lower():
                    platforms.add('Zephyr')
                
                mhz_match = __import__('re').search(r'(\d+)mhz', key.lower())
                if mhz_match:
                    frequencies.add(f"{mhz_match.group(1)} MHz")
        else:
            platforms = frequencies = set()
        
        return {
            'type': 'grouped_comparison',
            'options': {
                'group_by': 'platform',
                'platforms': list(platforms),
                'conditions': list(frequencies),
                'show_speedup': True,
                'n_cols': min(len(frequencies), 3) if frequencies else 1
            }
        }
