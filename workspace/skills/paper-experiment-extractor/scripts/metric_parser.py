"""
Metric Parser Module
Parse and normalize metrics from extracted tables.
"""

import re
from typing import Dict, List, Any, Optional, Union


class MetricParser:
    """Parse and normalize experimental metrics."""
    
    # Standard metric names and their common variations
    METRIC_ALIASES = {
        'accuracy': ['acc', 'accuracy', 'top-1', 'top1', 'top_1', 'acc@1'],
        'top5_accuracy': ['top-5', 'top5', 'top_5', 'acc@5'],
        'precision': ['prec', 'precision', 'prec.'],
        'recall': ['recall', 'rec', 'sensitivity'],
        'f1_score': ['f1', 'f-score', 'fscore', 'f1-score'],
        'params': ['param', 'params', 'parameters', '#param', '#params'],
        'flops': ['flop', 'flops', 'gflops', 'mflops', 'tflops', 'computation'],
        'latency': ['latency', 'inference time', 'speed'],
        'memory': ['memory', 'ram', 'gpu mem'],
    }
    
    # Units and their conversion factors to base units
    UNIT_CONVERSIONS = {
        'params': {
            'k': 1e3, 'K': 1e3,
            'm': 1e6, 'M': 1e6,
            'g': 1e9, 'G': 1e9,
            'b': 1e9, 'B': 1e9,
        },
        'flops': {
            'k': 1e3, 'K': 1e3,
            'm': 1e6, 'M': 1e6,
            'g': 1e9, 'G': 1e9,
            't': 1e12, 'T': 1e12,
        },
        'latency': {
            'ms': 1e-3, 's': 1, 'us': 1e-6,
        },
        'memory': {
            'kb': 1e3, 'KB': 1e3, 'k': 1e3,
            'mb': 1e6, 'MB': 1e6, 'm': 1e6,
            'gb': 1e9, 'GB': 1e9, 'g': 1e9,
        }
    }
    
    def __init__(self):
        self.parsed_metrics = []
    
    def parse(self, tables: List[Dict]) -> List[Dict]:
        """
        Parse metrics from extracted tables.
        
        Args:
            tables: List of table dictionaries from TableExtractor
        
        Returns:
            List of parsed metric dictionaries
        """
        results = []
        
        for table in tables:
            parsed = self._parse_table(table)
            if parsed:
                results.append(parsed)
        
        self.parsed_metrics = results
        return results
    
    def _parse_table(self, table: Dict) -> Optional[Dict]:
        """Parse a single table into structured metrics."""
        table_type = table.get('type', 'unknown')
        raw_data = table.get('raw_data', [])
        
        result = {
            'source': {
                'page': table.get('page'),
                'caption': table.get('caption', ''),
                'type': table_type
            },
            'data': {}
        }
        
        if table_type == 'confusion_matrix':
            result['data'] = self._parse_confusion_matrix(table)
        elif table_type == 'ablation':
            result['data'] = self._parse_ablation(table)
        elif table_type == 'comparison':
            result['data'] = self._parse_comparison(table)
        else:
            result['data'] = self._parse_generic(table)
        
        return result
    
    def _parse_confusion_matrix(self, table: Dict) -> Dict:
        """Parse confusion matrix table."""
        metrics = table.get('metrics', {})
        
        return {
            'experiment_type': 'confusion_matrix',
            'labels': metrics.get('labels', []),
            'matrix': metrics.get('matrix', []),
            'per_class_precision': metrics.get('per_class_precision', []),
            'per_class_recall': metrics.get('per_class_recall', []),
            'overall_accuracy': metrics.get('overall_accuracy', 0)
        }
    
    def _parse_ablation(self, table: Dict) -> Dict:
        """Parse ablation study table."""
        rows = table.get('rows', [])
        headers = table.get('headers', [])
        
        variants = []
        baseline = None
        
        for row in rows:
            if not row:
                continue
            
            variant_name = str(row[0]) if row else ''
            
            # Identify baseline (full model)
            if any(x in variant_name.lower() for x in ['full', 'complete', 'baseline', 'ours']):
                baseline = variant_name
            
            # Extract metrics for this variant
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
            'metrics_summary': all_metrics
        }
    
    def _parse_generic(self, table: Dict) -> Dict:
        """Parse generic table."""
        return {
            'experiment_type': 'unknown',
            'headers': table.get('headers', []),
            'rows': table.get('rows', []),
            'raw_metrics': table.get('metrics', {})
        }
    
    def _normalize_metric_name(self, header: Any) -> str:
        """Normalize metric name to standard form."""
        if not header:
            return 'unknown'
        
        header_str = str(header).lower().strip()
        
        for standard, aliases in self.METRIC_ALIASES.items():
            if any(alias in header_str for alias in aliases):
                return standard
        
        # Clean up the header
        cleaned = re.sub(r'[^\w\s]', '', header_str)
        cleaned = re.sub(r'\s+', '_', cleaned)
        return cleaned
    
    def _parse_value(self, value: Any) -> Optional[Union[float, int, str]]:
        """Parse and convert a value to appropriate numeric type."""
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
        for metric_type, units in self.UNIT_CONVERSIONS.items():
            for suffix, factor in units.items():
                if value_str.lower().endswith(suffix.lower()):
                    try:
                        num = float(value_str[:-len(suffix)].replace(',', ''))
                        return num * factor
                    except ValueError:
                        continue
        
        # Try direct numeric conversion
        try:
            if '.' in value_str:
                return float(value_str.replace(',', ''))
            else:
                return int(float(value_str.replace(',', '')))
        except ValueError:
            pass
        
        # Return as string if not numeric
        return value_str if value_str else None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all parsed metrics."""
        if not self.parsed_metrics:
            return {}
        
        summary = {
            'total_tables': len(self.parsed_metrics),
            'experiment_types': {},
            'available_metrics': set()
        }
        
        for metric in self.parsed_metrics:
            exp_type = metric.get('data', {}).get('experiment_type', 'unknown')
            summary['experiment_types'][exp_type] = summary['experiment_types'].get(exp_type, 0) + 1
            
            # Collect all metric names
            data = metric.get('data', {})
            if 'metrics_summary' in data:
                summary['available_metrics'].update(data['metrics_summary'].keys())
            elif 'variants' in data:
                for v in data['variants']:
                    summary['available_metrics'].update(v.get('metrics', {}).keys())
            elif 'models' in data:
                for m in data['models']:
                    summary['available_metrics'].update(m.keys())
        
        summary['available_metrics'] = sorted(list(summary['available_metrics']))
        return summary