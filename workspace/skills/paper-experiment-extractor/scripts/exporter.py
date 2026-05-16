"""
Data Exporter Module
Export parsed metrics to JSON and CSV formats.
"""

import json
import csv
from typing import Dict, List, Any, Union
from pathlib import Path


class DataExporter:
    """Export parsed metrics to various formats."""
    
    def to_json(self, metrics: List[Dict], output_path: str, indent: int = 2) -> str:
        """
        Export metrics to JSON file.
        
        Args:
            metrics: List of parsed metric dictionaries
            output_path: Output file path
            indent: JSON indentation level
        
        Returns:
            Path to output file
        """
        output = {
            'metadata': {
                'version': '1.0',
                'source': 'paper-experiment-extractor',
                'total_tables': len(metrics)
            },
            'experiments': metrics
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=indent, ensure_ascii=False)
        
        return output_path
    
    def to_csv(self, metrics: List[Dict], output_path: str) -> str:
        """
        Export metrics to CSV file.
        
        Note: Only exports tabular data (comparison and ablation tables).
        Confusion matrices are skipped for CSV export.
        
        Args:
            metrics: List of parsed metric dictionaries
            output_path: Output file path
        
        Returns:
            Path to output file
        """
        rows = []
        
        for metric in metrics:
            data = metric.get('data', {})
            exp_type = data.get('experiment_type', 'unknown')
            source = metric.get('source', {})
            
            if exp_type == 'model_comparison':
                rows.extend(self._flatten_comparison(data, source))
            elif exp_type == 'ablation':
                rows.extend(self._flatten_ablation(data, source))
        
        if not rows:
            # Create empty file with headers
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['experiment_type', 'name', 'metric', 'value', 'source_page', 'source_caption'])
            return output_path
        
        # Get all unique columns
        all_keys = set()
        for row in rows:
            all_keys.update(row.keys())
        
        # Standard column order
        priority_cols = ['experiment_type', 'name', 'metric', 'value', 'source_page', 'source_caption']
        columns = priority_cols + sorted([k for k in all_keys if k not in priority_cols])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        
        return output_path
    
    def _flatten_comparison(self, data: Dict, source: Dict) -> List[Dict]:
        """Flatten comparison data into CSV rows."""
        rows = []
        models = data.get('models', [])
        
        for model in models:
            model_name = model.get('name', 'unknown')
            
            for key, value in model.items():
                if key == 'name':
                    continue
                
                row = {
                    'experiment_type': 'model_comparison',
                    'name': model_name,
                    'metric': key,
                    'value': value,
                    'source_page': source.get('page'),
                    'source_caption': source.get('caption', '')
                }
                rows.append(row)
        
        return rows
    
    def _flatten_ablation(self, data: Dict, source: Dict) -> List[Dict]:
        """Flatten ablation data into CSV rows."""
        rows = []
        variants = data.get('variants', [])
        baseline = data.get('baseline')
        
        for variant in variants:
            variant_name = variant.get('name', 'unknown')
            is_baseline = (variant_name == baseline)
            
            for metric_name, value in variant.get('metrics', {}).items():
                row = {
                    'experiment_type': 'ablation',
                    'name': variant_name,
                    'metric': metric_name,
                    'value': value,
                    'is_baseline': is_baseline,
                    'source_page': source.get('page'),
                    'source_caption': source.get('caption', '')
                }
                rows.append(row)
        
        return rows
    
    def export_confusion_matrix(self, metric: Dict, output_path: str) -> str:
        """
        Export confusion matrix to separate CSV for detailed analysis.
        
        Args:
            metric: Single confusion matrix metric dict
            output_path: Output file path
        
        Returns:
            Path to output file
        """
        data = metric.get('data', {})
        labels = data.get('labels', [])
        matrix = data.get('matrix', [])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row
            writer.writerow([''] + labels + ['Recall'])
            
            # Data rows
            for i, row in enumerate(matrix):
                row_label = labels[i] if i < len(labels) else ''
                row_data = [row_label] + row
                
                # Add recall if available
                recalls = data.get('per_class_recall', [])
                if i < len(recalls):
                    row_data.append(recalls[i])
                
                writer.writerow(row_data)
            
            # Precision row
            precisions = data.get('per_class_precision', [])
            if precisions:
                prec_row = ['Precision'] + precisions + ['']
                writer.writerow(prec_row)
            
            # Overall accuracy
            acc = data.get('overall_accuracy')
            if acc is not None:
                writer.writerow([])
                writer.writerow(['Overall Accuracy', acc])
        
        return output_path
    
    def generate_summary_report(self, metrics: List[Dict], output_path: str) -> str:
        """Generate a human-readable summary report."""
        lines = [
            "# Paper Experiment Extraction Report",
            "",
            f"**Total Experiments Found:** {len(metrics)}",
            "",
            "## Experiment Summary",
            ""
        ]
        
        for i, metric in enumerate(metrics, 1):
            source = metric.get('source', {})
            data = metric.get('data', {})
            exp_type = data.get('experiment_type', 'unknown')
            
            lines.append(f"### Experiment {i}")
            lines.append(f"- **Type:** {exp_type}")
            lines.append(f"- **Page:** {source.get('page')}")
            lines.append(f"- **Caption:** {source.get('caption', 'N/A')}")
            
            if exp_type == 'confusion_matrix':
                labels = data.get('labels', [])
                acc = data.get('overall_accuracy')
                lines.append(f"- **Classes:** {len(labels)} ({', '.join(labels[:5])}{'...' if len(labels) > 5 else ''})")
                if acc:
                    lines.append(f"- **Accuracy:** {acc:.2%}")
            
            elif exp_type == 'model_comparison':
                models = data.get('models', [])
                lines.append(f"- **Models compared:** {len(models)}")
                for m in models[:3]:
                    lines.append(f"  - {m.get('name', 'Unknown')}")
                if len(models) > 3:
                    lines.append(f"  - ... and {len(models) - 3} more")
            
            elif exp_type == 'ablation':
                variants = data.get('variants', [])
                baseline = data.get('baseline')
                lines.append(f"- **Variants:** {len(variants)}")
                lines.append(f"- **Baseline:** {baseline}")
            
            lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_path