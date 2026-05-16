"""
Enhanced Metric Parser with automatic visualization type matching.
"""

import re
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np


class EnhancedMetricParser:
    """Parse metrics with automatic visualization type detection."""
    
    # Visualization type mappings
    VIZ_TYPE_MAPPINGS = {
        'confusion_matrix': {
            'chart_type': 'heatmap',
            'requirements': ['matrix', 'labels'],
            'options': ['normalize', 'show_precision_recall', 'cmap']
        },
        'model_comparison': {
            'chart_type': 'bar_chart',
            'alt_chart_types': ['radar_chart', 'grouped_bar'],
            'requirements': ['models', 'metrics'],
            'options': ['error_bars', 'significance', 'horizontal']
        },
        'ablation': {
            'chart_type': 'ablation_bar',
            'requirements': ['variants', 'baseline'],
            'options': ['show_deltas', 'sort_by_impact']
        },
        'training_curve': {
            'chart_type': 'line_plot',
            'requirements': ['epochs', 'curves'],
            'options': ['smooth', 'highlight_best', 'multi_axis']
        },
        'hardware_comparison': {
            'chart_type': 'grouped_bar',
            'alt_chart_types': ['multi_subplot'],
            'requirements': ['models', 'conditions', 'metric_values'],
            'options': ['group_by', 'show_speedup']
        }
    }
    
    def __init__(self):
        self.parsed_metrics = []
        self.viz_recommendations = []
    
    def parse(self, tables: List[Dict]) -> List[Dict]:
        """
        Parse metrics and recommend visualization types.
        
        Args:
            tables: List of extracted tables with type classification
            
        Returns:
            List of parsed metrics with visualization recommendations
        """
        results = []
        
        for table in tables:
            parsed = self._parse_table(table)
            if parsed:
                # Add visualization recommendation
                viz_rec = self._recommend_visualization(parsed)
                parsed['visualization'] = viz_rec
                results.append(parsed)
        
        self.parsed_metrics = results
        return results
    
    def _parse_table(self, table: Dict) -> Optional[Dict]:
        """Parse a single table based on its type."""
        table_type = table.get('type', 'unknown')
        raw_data = table.get('data', [])
        
        if not raw_data:
            return None
        
        result = {
            'source': {
                'page': table.get('page'),
                'caption': table.get('caption', ''),
                'type': table_type,
                'confidence': table.get('type_confidence', 0)
            },
            'data': {},
            'raw_table': table
        }
        
        # Route to appropriate parser
        if table_type == 'confusion_matrix':
            result['data'] = self._parse_confusion_matrix(table)
        elif table_type == 'ablation':
            result['data'] = self._parse_ablation(table)
        elif table_type == 'model_comparison':
            result['data'] = self._parse_comparison(table)
        elif table_type == 'hardware_comparison':
            result['data'] = self._parse_hardware_comparison(table)
        elif table_type == 'training_curve':
            result['data'] = self._parse_training_curve(table)
        else:
            result['data'] = self._parse_generic(table)
        
        return result
    
    def _parse_confusion_matrix(self, table: Dict) -> Dict:
        """Parse confusion matrix with metrics calculation."""
        data = table.get('data', [])
        
        if len(data) < 2:
            return {'experiment_type': 'confusion_matrix', 'error': 'Insufficient data'}
        
        # Extract labels and matrix
        labels = [str(row[0]) for row in data[1:] if row]
        
        matrix = []
        for row in data[1:]:
            if len(row) > 1:
                try:
                    values = []
                    for cell in row[1:]:
                        val_str = str(cell).replace(',', '').replace('%', '')
                        values.append(float(val_str))
                    matrix.append(values)
                except (ValueError, TypeError):
                    continue
        
        # Calculate per-class metrics
        per_class = self._calculate_per_class_metrics(matrix, labels)
        overall_acc = self._calculate_overall_accuracy(matrix)
        
        return {
            'experiment_type': 'confusion_matrix',
            'labels': labels,
            'matrix': matrix,
            'per_class_precision': per_class['precision'],
            'per_class_recall': per_class['recall'],
            'per_class_f1': per_class['f1'],
            'overall_accuracy': overall_acc
        }
    
    def _calculate_per_class_metrics(self, matrix: List[List], labels: List) -> Dict:
        """Calculate precision, recall, and F1 for each class."""
        matrix_np = np.array(matrix)
        n_classes = len(labels)
        
        precision = []
        recall = []
        f1 = []
        
        for i in range(n_classes):
            tp = matrix_np[i, i]
            col_sum = matrix_np[:, i].sum()
            row_sum = matrix_np[i, :].sum()
            
            prec = tp / col_sum if col_sum > 0 else 0
            rec = tp / row_sum if row_sum > 0 else 0
            f1_score = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
            
            precision.append(round(prec, 4))
            recall.append(round(rec, 4))
            f1.append(round(f1_score, 4))
        
        return {'precision': precision, 'recall': recall, 'f1': f1}
    
    def _calculate_overall_accuracy(self, matrix: List[List]) -> float:
        """Calculate overall accuracy from confusion matrix."""
        if not matrix:
            return 0.0
        
        matrix_np = np.array(matrix)
        correct = np.trace(matrix_np)
        total = matrix_np.sum()
        
        return round(correct / total, 4) if total > 0 else 0.0
    
    def _parse_ablation(self, table: Dict) -> Dict:
        """Parse ablation study table."""
        rows = table.get('rows', [])
        headers = table.get('headers', [])
        
        variants = []
        baseline = None
        baseline_metrics = {}
        
        for row in rows:
            if not row:
                continue
            
            variant_name = str(row[0]) if row else ''
            
            # Identify baseline
            if any(x in variant_name.lower() for x in ['full', 'complete', 'baseline', 'ours', 'original']):
                baseline = variant_name
            
            # Extract metrics
            variant_metrics = {}
            for i, header in enumerate(headers[1:], 1):
                if i < len(row):
                    metric_name = self._normalize_metric_name(header)
                    value = self._parse_value(row[i])
                    if value is not None:
                        variant_metrics[metric_name] = value
            
            variants.append({
                'name': variant_name,
                'metrics': variant_metrics
            })
            
            if variant_name == baseline:
                baseline_metrics = variant_metrics
        
        # Calculate deltas
        for variant in variants:
            if variant['name'] != baseline and baseline_metrics:
                variant['deltas'] = {}
                for metric, value in variant['metrics'].items():
                    if metric in baseline_metrics:
                        delta = value - baseline_metrics[metric]
                        variant['deltas'][metric] = round(delta, 4)
        
        return {
            'experiment_type': 'ablation',
            'baseline': baseline or (variants[0]['name'] if variants else None),
            'variants': variants
        }
    
    def _parse_comparison(self, table: Dict) -> Dict:
        """Parse model comparison table."""
        rows = table.get('rows', [])
        headers = table.get('headers', [])
        
        models = []
        all_metrics = {}
        
        for row in rows:
            if not row:
                continue
            
            model_name = str(row[0]) if row else ''
            model_data = {'name': model_name}
            
            for i, header in enumerate(headers[1:], 1):
                if i < len(row):
                    metric_name = self._normalize_metric_name(header)
                    value = self._parse_value(row[i])
                    if value is not None:
                        model_data[metric_name] = value
                        if metric_name not in all_metrics:
                            all_metrics[metric_name] = []
                        all_metrics[metric_name].append(value)
            
            models.append(model_data)
        
        return {
            'experiment_type': 'model_comparison',
            'models': models,
            'available_metrics': list(all_metrics.keys()),
            'metrics_summary': all_metrics
        }
    
    def _parse_hardware_comparison(self, table: Dict) -> Dict:
        """Parse hardware/inference time comparison."""
        # Similar to model comparison but with hardware-specific processing
        data = self._parse_comparison(table)
        data['experiment_type'] = 'hardware_comparison'
        
        # Detect frequency columns
        headers = table.get('headers', [])
        frequencies = []
        platforms = []
        
        for header in headers:
            header_str = str(header).lower()
            # Look for MHz values
            mhz_match = re.search(r'(\d+)\s*mhz', header_str)
            if mhz_match:
                frequencies.append(int(mhz_match.group(1)))
            
            # Look for platform names
            if any(p in header_str for p in ['linux', 'zephyr', 'cpu', 'gpu']):
                platforms.append(str(header).strip())
        
        data['frequencies'] = list(set(frequencies))
        data['platforms'] = list(set(platforms))
        
        return data
    
    def _parse_training_curve(self, table: Dict) -> Dict:
        """Parse training curve data."""
        rows = table.get('rows', [])
        headers = table.get('headers', [])
        
        curves = {}
        epochs = []
        
        for i, row in enumerate(rows):
            if not row:
                continue
            
            # First column is typically epoch/iteration
            if i == 0:
                epochs = list(range(len(rows)))
            
            for j, header in enumerate(headers[1:], 1):
                if j < len(row):
                    header_name = str(header)
                    if header_name not in curves:
                        curves[header_name] = []
                    
                    value = self._parse_value(row[j])
                    curves[header_name].append(value if value is not None else 0)
        
        return {
            'experiment_type': 'training_curve',
            'epochs': epochs,
            'curves': curves
        }
    
    def _parse_generic(self, table: Dict) -> Dict:
        """Parse generic table."""
        return {
            'experiment_type': 'unknown',
            'headers': table.get('headers', []),
            'rows': table.get('rows', []),
            'raw_metrics': table.get('metrics', {})
        }
    
    def _recommend_visualization(self, parsed: Dict) -> Dict:
        """Recommend visualization type based on data."""
        exp_type = parsed.get('data', {}).get('experiment_type', 'unknown')
        
        if exp_type not in self.VIZ_TYPE_MAPPINGS:
            return {
                'chart_type': 'auto',
                'confidence': 0.0,
                'alternatives': []
            }
        
        mapping = self.VIZ_TYPE_MAPPINGS[exp_type]
        
        # Check if requirements are met
        requirements_met = self._check_requirements(parsed['data'], mapping['requirements'])
        
        recommendation = {
            'chart_type': mapping['chart_type'],
            'confidence': 0.8 if requirements_met else 0.5,
            'requirements_met': requirements_met,
            'available_options': mapping.get('options', []),
            'alternatives': []
        }
        
        # Suggest alternatives based on data characteristics
        if exp_type == 'model_comparison':
            n_models = len(parsed['data'].get('models', []))
            n_metrics = len(parsed['data'].get('available_metrics', []))
            
            if n_metrics >= 3:
                recommendation['alternatives'].append({
                    'chart_type': 'radar_chart',
                    'reason': f'Multiple metrics ({n_metrics}) available'
                })
            
            if n_models > 5:
                recommendation['alternatives'].append({
                    'chart_type': 'horizontal_bar',
                    'reason': 'Many models, horizontal layout may be better'
                })
        
        return recommendation
    
    def _check_requirements(self, data: Dict, requirements: List[str]) -> bool:
        """Check if data meets visualization requirements."""
        for req in requirements:
            if req not in data:
                return False
            if not data[req]:
                return False
        return True
    
    def _normalize_metric_name(self, header: Any) -> str:
        """Normalize metric name to standard form."""
        if not header:
            return 'unknown'
        
        header_str = str(header).lower().strip()
        
        # Standard metric aliases
        aliases = {
            'accuracy': ['acc', 'accuracy', 'top-1', 'top1', 'acc@1'],
            'top5_accuracy': ['top-5', 'top5', 'acc@5'],
            'precision': ['prec', 'precision'],
            'recall': ['recall', 'rec'],
            'f1_score': ['f1', 'f-score'],
            'params': ['param', 'params', 'parameters'],
            'flops': ['flop', 'flops', 'gflops'],
            'latency': ['latency', 'time', 'inference time'],
            'memory': ['memory', 'ram', 'mem'],
        }
        
        for standard, patterns in aliases.items():
            if any(p in header_str for p in patterns):
                return standard
        
        # Clean up
        cleaned = re.sub(r'[^\w\s]', '', header_str)
        cleaned = re.sub(r'\s+', '_', cleaned)
        return cleaned
    
    def _parse_value(self, value: Any) -> Optional[Union[float, int, str]]:
        """Parse and convert value to appropriate type."""
        if value is None:
            return None
        
        value_str = str(value).strip()
        
        # Handle percentage
        if '%' in value_str:
            try:
                return float(value_str.replace('%', '').replace(',', '')) / 100
            except ValueError:
                pass
        
        # Handle unit suffixes
        unit_multipliers = {
            'k': 1e3, 'm': 1e6, 'g': 1e9, 't': 1e12,
            'kb': 1e3, 'mb': 1e6, 'gb': 1e9,
            'ms': 1, 's': 1000, 'us': 0.001  # Convert to ms
        }
        
        for suffix, multiplier in unit_multipliers.items():
            if value_str.lower().endswith(suffix.lower()):
                try:
                    num = float(value_str[:-len(suffix)].replace(',', ''))
                    return num * multiplier
                except ValueError:
                    continue
        
        # Try direct numeric conversion
        try:
            return float(value_str.replace(',', ''))
        except ValueError:
            pass
        
        return value_str if value_str else None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary with visualization recommendations."""
        if not self.parsed_metrics:
            return {}
        
        summary = {
            'total_experiments': len(self.parsed_metrics),
            'experiment_types': {},
            'visualization_recommendations': []
        }
        
        for metric in self.parsed_metrics:
            exp_type = metric.get('data', {}).get('experiment_type', 'unknown')
            summary['experiment_types'][exp_type] = summary['experiment_types'].get(exp_type, 0) + 1
            
            viz = metric.get('visualization', {})
            summary['visualization_recommendations'].append({
                'type': exp_type,
                'recommended_chart': viz.get('chart_type'),
                'confidence': viz.get('confidence'),
                'alternatives': viz.get('alternatives', [])
            })
        
        return summary
