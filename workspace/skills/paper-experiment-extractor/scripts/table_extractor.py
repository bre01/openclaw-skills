"""
Table Extractor Module
Detect and extract tables from paper sections.
"""

import re
from typing import List, Dict, Any, Optional
import numpy as np


class TableExtractor:
    """Extract and classify tables from academic papers."""
    
    # Keywords for identifying table types
    TABLE_TYPE_PATTERNS = {
        'confusion_matrix': [
            r'confusion\s*matrix',
            r'predicted.*actual|actual.*predicted',
        ],
        'ablation': [
            r'ablation',
            r'w/o\s+\w+',
            r'without\s+\w+',
            r'remove',
        ],
        'comparison': [
            r'comparison',
            r'sota|state.*art',
            r'vs\.?|versus',
            r'baseline',
        ],
        'training': [
            r'training\s*(curve|loss|accuracy)',
            r'epoch',
            r'convergence',
        ]
    }
    
    def __init__(self):
        self.tables = []
    
    def extract_tables(self, paper_loader, sections: List[Dict] = None) -> List[Dict]:
        """
        Extract all tables from paper.
        
        Args:
            paper_loader: Loaded PaperLoader instance
            sections: Optional list of sections to focus on
        """
        # Get raw tables from PDF
        raw_tables = paper_loader.get_tables_with_pdfplumber()
        
        processed_tables = []
        for table in raw_tables:
            processed = self._process_table(table, paper_loader)
            if processed:
                processed_tables.append(processed)
        
        self.tables = processed_tables
        return processed_tables
    
    def _process_table(self, table: Dict, paper_loader) -> Optional[Dict]:
        """Process a single table and extract metadata."""
        data = table['data']
        if not data or len(data) < 2:
            return None
        
        # Get context for classification
        context = paper_loader.get_context_around_table(table)
        
        # Detect table type
        table_type = self._classify_table(data, context)
        
        # Extract metrics based on type
        metrics = self._extract_metrics(data, table_type)
        
        return {
            'page': table['page'],
            'type': table_type,
            'raw_data': data,
            'headers': data[0] if data else [],
            'rows': data[1:] if len(data) > 1 else [],
            'metrics': metrics,
            'context': context[:500],  # First 500 chars of context
            'caption': self._extract_caption(context)
        }
    
    def _classify_table(self, data: List[List], context: str) -> str:
        """Classify table type based on content and context."""
        context_lower = context.lower()
        
        # Check for square matrix (confusion matrix indicator)
        if len(data) > 1 and len(data) == len(data[0]):
            is_square = all(len(row) == len(data) for row in data)
            if is_square:
                return 'confusion_matrix'
        
        # Check context patterns
        for table_type, patterns in self.TABLE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, context_lower):
                    return table_type
        
        # Default to comparison if multiple models mentioned
        if len(data) > 2 and self._looks_like_model_names(data[0]):
            return 'comparison'
        
        return 'unknown'
    
    def _looks_like_model_names(self, headers: List) -> bool:
        """Check if headers look like model names."""
        header_str = ' '.join(str(h) for h in headers if h)
        model_indicators = ['resnet', 'vit', 'bert', 'gpt', 'model', 'method', 'network']
        return any(ind in header_str.lower() for ind in model_indicators)
    
    def _extract_metrics(self, data: List[List], table_type: str) -> Dict[str, Any]:
        """Extract numerical metrics from table."""
        metrics = {}
        
        if table_type == 'confusion_matrix':
            metrics = self._extract_confusion_matrix(data)
        elif table_type in ['comparison', 'ablation']:
            metrics = self._extract_comparison_metrics(data)
        
        return metrics
    
    def _extract_confusion_matrix(self, data: List[List]) -> Dict:
        """Extract confusion matrix structure."""
        if len(data) < 2:
            return {}
        
        headers = data[0]
        rows = data[1:]
        
        # Assume first column is labels
        labels = [row[0] for row in rows if row]
        
        # Extract matrix values
        matrix = []
        for row in rows:
            if len(row) > 1:
                try:
                    values = [float(x) if x else 0 for x in row[1:]]
                    matrix.append(values)
                except (ValueError, TypeError):
                    continue
        
        # Calculate per-class metrics
        per_class = self._calculate_per_class_metrics(matrix, labels)
        
        return {
            'labels': labels,
            'matrix': matrix,
            'per_class_precision': per_class['precision'],
            'per_class_recall': per_class['recall'],
            'overall_accuracy': self._calculate_accuracy(matrix)
        }
    
    def _calculate_per_class_metrics(self, matrix: List[List], labels: List) -> Dict:
        """Calculate precision and recall for each class."""
        matrix_np = np.array(matrix)
        n_classes = len(labels)
        
        precision = []
        recall = []
        
        for i in range(n_classes):
            tp = matrix_np[i, i]
            col_sum = matrix_np[:, i].sum()
            row_sum = matrix_np[i, :].sum()
            
            prec = tp / col_sum if col_sum > 0 else 0
            rec = tp / row_sum if row_sum > 0 else 0
            
            precision.append(round(prec, 4))
            recall.append(round(rec, 4))
        
        return {'precision': precision, 'recall': recall}
    
    def _calculate_accuracy(self, matrix: List[List]) -> float:
        """Calculate overall accuracy from confusion matrix."""
        if not matrix:
            return 0.0
        
        matrix_np = np.array(matrix)
        correct = np.trace(matrix_np)
        total = matrix_np.sum()
        
        return round(correct / total, 4) if total > 0 else 0.0
    
    def _extract_comparison_metrics(self, data: List[List]) -> Dict:
        """Extract comparison metrics (accuracy, params, FLOPs, etc.)."""
        metrics = {}
        
        if not data or len(data) < 2:
            return metrics
        
        headers = [str(h).lower() if h else '' for h in data[0]]
        
        # Map common header variations to standard metric names
        metric_mapping = {
            'accuracy': ['acc', 'accuracy', 'top-1', 'top1'],
            'precision': ['prec', 'precision'],
            'recall': ['recall', 'rec'],
            'f1': ['f1', 'f-score', 'fscore'],
            'params': ['param', 'params', 'parameters', '#param'],
            'flops': ['flop', 'flops', 'gflops', 'mflops', 'computation'],
        }
        
        for col_idx, header in enumerate(headers):
            for metric_name, patterns in metric_mapping.items():
                if any(p in header for p in patterns):
                    values = []
                    for row in data[1:]:
                        if col_idx < len(row) and row[col_idx]:
                            try:
                                # Clean and parse value
                                val_str = str(row[col_idx]).replace(',', '').replace('%', '')
                                val = float(val_str)
                                if '%' in str(row[col_idx]):
                                    val = val / 100
                                values.append(val)
                            except (ValueError, TypeError):
                                continue
                    
                    if values:
                        if metric_name not in metrics:
                            metrics[metric_name] = []
                        metrics[metric_name].extend(values)
        
        return metrics
    
    def _extract_caption(self, context: str) -> str:
        """Extract table caption from context."""
        # Look for Table X: ... or Table X. ... patterns
        caption_patterns = [
            r'Table\s+\d+[:.]\s*([^\n]+)',
            r'TAB\.?\s*\d+[:.]\s*([^\n]+)',
        ]
        
        for pattern in caption_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""