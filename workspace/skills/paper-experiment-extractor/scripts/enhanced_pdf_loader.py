#!/usr/bin/env python3
"""
Enhanced PDF Loader Module
Multi-engine PDF table extraction with LLM-assisted correction.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

try:
    import pdfplumber
    import fitz  # PyMuPDF
    import pandas as pd
    import numpy as np
except ImportError:
    raise ImportError("Please install: pip install pdfplumber pymupdf pandas numpy")


class MultiEngineTableExtractor:
    """Extract tables using multiple engines and select best results."""
    
    def __init__(self):
        self.engines = ['pdfplumber', 'pymupdf', 'heuristic']
        self.extraction_results = []
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables using multiple engines and merge results.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of extracted tables with confidence scores
        """
        all_tables = []
        
        # Try pdfplumber
        try:
            plumber_tables = self._extract_with_pdfplumber(pdf_path)
            for t in plumber_tables:
                t['engine'] = 'pdfplumber'
                t['confidence'] = self._calculate_confidence(t)
            all_tables.extend(plumber_tables)
        except Exception as e:
            print(f"  pdfplumber failed: {e}")
        
        # Try PyMuPDF
        try:
            pymupdf_tables = self._extract_with_pymupdf(pdf_path)
            for t in pymupdf_tables:
                t['engine'] = 'pymupdf'
                t['confidence'] = self._calculate_confidence(t)
            all_tables.extend(pymupdf_tables)
        except Exception as e:
            print(f"  pymupdf failed: {e}")
        
        # Try heuristic extraction for text-based tables
        try:
            heuristic_tables = self._extract_with_heuristics(pdf_path)
            for t in heuristic_tables:
                t['engine'] = 'heuristic'
                t['confidence'] = self._calculate_confidence(t)
            all_tables.extend(heuristic_tables)
        except Exception as e:
            print(f"  heuristic failed: {e}")
        
        # Merge duplicate tables and select best version
        merged_tables = self._merge_duplicate_tables(all_tables)
        
        return merged_tables
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> List[Dict]:
        """Extract tables using pdfplumber."""
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:
                        tables.append({
                            'page': page_num,
                            'data': self._clean_table_data(table),
                            'headers': table[0] if table else [],
                            'rows': table[1:] if len(table) > 1 else [],
                            'bbox': None  # Could add bounding box
                        })
        return tables
    
    def _extract_with_pymupdf(self, pdf_path: str) -> List[Dict]:
        """Extract tables using PyMuPDF's table detection."""
        tables = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # PyMuPDF can detect tables using find_tables()
            try:
                tab = page.find_tables()
                if tab and tab.tables:
                    for table in tab.tables:
                        data = table.extract()
                        if data and len(data) > 1:
                            tables.append({
                                'page': page_num + 1,
                                'data': self._clean_table_data(data),
                                'headers': data[0] if data else [],
                                'rows': data[1:] if len(data) > 1 else []
                            })
            except:
                # Fallback: extract text and parse
                pass
        
        doc.close()
        return tables
    
    def _extract_with_heuristics(self, pdf_path: str) -> List[Dict]:
        """Extract tables using text heuristics."""
        tables = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Look for table patterns
            table_patterns = [
                r'TABLE\s+[IVX\d]+[.:]\s*([^\n]+)',  # TABLE I: Caption
                r'Table\s+\d+[.:]\s*([^\n]+)',  # Table 1: Caption
            ]
            
            for pattern in table_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    # Extract table region
                    start = match.start()
                    end = min(start + 2000, len(text))
                    region = text[start:end]
                    
                    # Try to parse table structure
                    lines = region.split('\n')
                    table_data = self._parse_text_table(lines)
                    
                    if table_data and len(table_data) > 1:
                        tables.append({
                            'page': page_num + 1,
                            'data': table_data,
                            'headers': table_data[0],
                            'rows': table_data[1:],
                            'caption': match.group(1).strip()
                        })
        
        doc.close()
        return tables
    
    def _clean_table_data(self, data: List[List]) -> List[List]:
        """Clean table data by removing empty rows and normalizing."""
        cleaned = []
        for row in data:
            if row and any(cell is not None and str(cell).strip() for cell in row):
                cleaned_row = [
                    str(cell).strip() if cell is not None else ''
                    for cell in row
                ]
                cleaned.append(cleaned_row)
        return cleaned
    
    def _parse_text_table(self, lines: List[str]) -> List[List]:
        """Parse table from text lines."""
        # Simple heuristic: look for lines with multiple whitespace-separated values
        table_data = []
        for line in lines[:50]:  # Check first 50 lines
            if len(line.strip()) > 0:
                # Split by multiple spaces or tabs
                cells = re.split(r'\s{2,}|\t', line.strip())
                if len(cells) >= 2 and len(cells) <= 10:  # Reasonable number of columns
                    table_data.append(cells)
        
        # Filter out rows that don't match the column count pattern
        if len(table_data) >= 2:
            col_counts = [len(row) for row in table_data]
            most_common = max(set(col_counts), key=col_counts.count)
            table_data = [row for row in table_data if len(row) == most_common]
        
        return table_data if len(table_data) >= 2 else []
    
    def _calculate_confidence(self, table: Dict) -> float:
        """Calculate confidence score for extracted table."""
        score = 0.0
        data = table.get('data', [])
        
        if not data or len(data) < 2:
            return 0.0
        
        # Check for consistent column counts
        col_counts = [len(row) for row in data]
        if len(set(col_counts)) == 1:
            score += 0.3
        
        # Check for header row (typically contains strings)
        header = data[0]
        if any(isinstance(cell, str) and not cell.replace('.', '').isdigit() for cell in header):
            score += 0.2
        
        # Check for numeric data in body
        numeric_count = 0
        total_cells = 0
        for row in data[1:]:
            for cell in row:
                total_cells += 1
                try:
                    float(str(cell).replace(',', '').replace('%', ''))
                    numeric_count += 1
                except:
                    pass
        
        if total_cells > 0:
            numeric_ratio = numeric_count / total_cells
            score += numeric_ratio * 0.3
        
        # Check for reasonable table size
        if 2 <= len(data) <= 50 and 2 <= col_counts[0] <= 20:
            score += 0.2
        
        return min(score, 1.0)
    
    def _merge_duplicate_tables(self, tables: List[Dict]) -> List[Dict]:
        """Merge tables that appear to be duplicates and select best version."""
        if not tables:
            return []
        
        # Group by page
        by_page = {}
        for t in tables:
            page = t.get('page', 0)
            if page not in by_page:
                by_page[page] = []
            by_page[page].append(t)
        
        merged = []
        for page, page_tables in by_page.items():
            # For each page, select table with highest confidence
            if len(page_tables) == 1:
                merged.append(page_tables[0])
            else:
                # Select best based on confidence and data completeness
                best = max(page_tables, key=lambda t: (t.get('confidence', 0), len(t.get('data', []))))
                # Add alternative extractions as metadata
                best['alternatives'] = [t for t in page_tables if t != best]
                merged.append(best)
        
        return merged


class SmartTableClassifier:
    """Intelligently classify table types based on content."""
    
    TYPE_INDICATORS = {
        'confusion_matrix': {
            'headers': ['predicted', 'actual', 'true', 'pred', 'class'],
            'patterns': [r'confusion\s*matrix', r'predicted\s*vs\s*actual'],
            'structure': 'square'  # NxN matrix
        },
        'ablation': {
            'headers': ['w/o', 'without', 'remove', 'ablation', 'variant'],
            'patterns': [r'ablation', r'w/o\s+\w+', r'without\s+\w+'],
            'structure': 'comparison'
        },
        'model_comparison': {
            'headers': ['model', 'method', 'accuracy', 'acc', 'f1', 'params', 'flops'],
            'patterns': [r'comparison', r'vs\.?', r'baseline', r'sota'],
            'structure': 'comparison'
        },
        'training_curve': {
            'headers': ['epoch', 'iteration', 'step', 'loss', 'accuracy'],
            'patterns': [r'training', r'convergence', r'epoch'],
            'structure': 'temporal'
        },
        'hardware_comparison': {
            'headers': ['cpu', 'gpu', 'latency', 'time', 'memory', 'mhz', 'frequency'],
            'patterns': [r'inference\s*time', r'latency', r'memory\s*consumption', r'mhz', r'frequency'],
            'structure': 'comparison'
        }
    }
    
    def classify(self, table: Dict, context: str = '') -> Tuple[str, float]:
        """
        Classify table type and return confidence.
        
        Returns:
            (table_type, confidence)
        """
        data = table.get('data', [])
        headers = [str(h).lower() for h in table.get('headers', [])]
        caption = table.get('caption', '').lower()
        context_lower = context.lower()
        
        scores = {}
        
        for table_type, indicators in self.TYPE_INDICATORS.items():
            score = 0.0
            
            # Check header matches
            header_matches = sum(1 for h in indicators['headers'] if any(h in hdr for hdr in headers))
            score += header_matches * 0.2
            
            # Check pattern matches in caption/context
            for pattern in indicators['patterns']:
                if re.search(pattern, caption, re.IGNORECASE):
                    score += 0.3
                if re.search(pattern, context_lower, re.IGNORECASE):
                    score += 0.2
            
            # Check structure
            if indicators['structure'] == 'square' and len(data) > 1:
                n_cols = len(data[0])
                if len(data) == n_cols:
                    score += 0.3
            
            scores[table_type] = score
        
        # Get best match
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            if best_score > 0.3:
                return best_type, min(best_score, 1.0)
        
        return 'unknown', 0.0


class LLMAssistedCorrector:
    """LLM-assisted table correction and enhancement."""
    
    def __init__(self):
        self.enable_llm = False  # Will be enabled if LLM API available
    
    def correct_table_structure(self, table: Dict) -> Dict:
        """Apply heuristic corrections to improve table structure."""
        data = table.get('data', [])
        if not data:
            return table
        
        # Detect and fix common issues
        corrections = []
        
        # 1. Fix merged header cells
        if len(data) > 0:
            header = data[0]
            # If first row has many empty cells, it might be a multi-level header
            empty_count = sum(1 for cell in header if not cell.strip())
            if empty_count > len(header) * 0.3 and len(data) > 1:
                # Try to merge with second row
                new_header = []
                for i, (h1, h2) in enumerate(zip(header, data[1])):
                    if h1.strip() and h2.strip():
                        new_header.append(f"{h1} {h2}")
                    elif h1.strip():
                        new_header.append(h1)
                    else:
                        new_header.append(h2)
                data[0] = new_header
                data.pop(1)
                corrections.append("Merged multi-level header")
        
        # 2. Detect and fix unit annotations
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                # Extract units like (ms), (MB), (%)
                unit_match = re.search(r'\(([^)]+)\)$', cell.strip())
                if unit_match and i == 0:  # Header row
                    unit = unit_match.group(1)
                    # Could add unit to metadata
                    pass
        
        # 3. Normalize numeric values
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                if i > 0:  # Data rows
                    # Try to extract numeric value
                    try:
                        # Remove commas, handle percentages
                        cleaned = str(cell).replace(',', '').replace('%', '').strip()
                        float(cleaned)  # Validate
                    except:
                        pass
        
        table['data'] = data
        table['corrections'] = corrections
        return table
    
    def suggest_table_metadata(self, table: Dict) -> Dict:
        """Suggest metadata for the table."""
        data = table.get('data', [])
        headers = table.get('headers', [])
        
        metadata = {
            'suggested_title': '',
            'suggested_units': {},
            'suggested_metrics': []
        }
        
        # Infer units from headers
        unit_patterns = {
            r'\(ms\)|time|latency': 'milliseconds',
            r'\(mb\)|memory|ram': 'megabytes',
            r'\(%\)|percent|reduction': 'percentage',
            r'\(mhz\)|frequency': 'megahertz'
        }
        
        for header in headers:
            header_str = str(header).lower()
            for pattern, unit in unit_patterns.items():
                if re.search(pattern, header_str):
                    metadata['suggested_units'][header] = unit
        
        # Detect metric columns
        metric_keywords = ['accuracy', 'acc', 'precision', 'recall', 'f1', 'loss', 'time', 'memory']
        for header in headers:
            if any(kw in str(header).lower() for kw in metric_keywords):
                metadata['suggested_metrics'].append(header)
        
        return metadata


class EnhancedPaperLoader:
    """Enhanced paper loader with multi-engine extraction."""
    
    def __init__(self):
        self.pdf_path = None
        self.doc = None
        self.text = ""
        self.pages = []
        self.table_extractor = MultiEngineTableExtractor()
        self.table_classifier = SmartTableClassifier()
        self.table_corrector = LLMAssistedCorrector()
        self.extracted_tables = []
        
    def load(self, pdf_path: str) -> 'EnhancedPaperLoader':
        """Load PDF from file path."""
        self.pdf_path = Path(pdf_path)
        
        # Load with PyMuPDF for general parsing
        self.doc = fitz.open(pdf_path)
        
        # Extract text from all pages
        self.pages = []
        for page_num, page in enumerate(self.doc):
            page_text = page.get_text()
            self.pages.append({
                'number': page_num + 1,
                'text': page_text
            })
        
        self.text = "\n".join([p['text'] for p in self.pages])
        return self
    
    def extract_all_tables(self) -> List[Dict]:
        """Extract all tables using multiple engines."""
        print("Extracting tables with multiple engines...")
        
        raw_tables = self.table_extractor.extract_tables(str(self.pdf_path))
        
        print(f"Found {len(raw_tables)} potential tables")
        
        processed_tables = []
        for i, table in enumerate(raw_tables):
            print(f"  Processing table {i+1} (page {table.get('page', '?')}, confidence: {table.get('confidence', 0):.2f})")
            
            # Get context
            context = self._get_context_for_table(table)
            
            # Classify table type
            table_type, type_confidence = self.table_classifier.classify(table, context)
            table['type'] = table_type
            table['type_confidence'] = type_confidence
            
            # Apply corrections
            table = self.table_corrector.correct_table_structure(table)
            
            # Add metadata
            table['context'] = context[:500]
            table['metadata'] = self.table_corrector.suggest_table_metadata(table)
            
            processed_tables.append(table)
        
        self.extracted_tables = processed_tables
        return processed_tables
    
    def _get_context_for_table(self, table: Dict) -> str:
        """Get text context around a table."""
        page_num = table.get('page', 1) - 1
        if page_num < 0 or page_num >= len(self.pages):
            return ""
        
        page_text = self.pages[page_num]['text']
        
        # Look for caption patterns
        caption = table.get('caption', '')
        
        # Get surrounding text (before and after table)
        lines = page_text.split('\n')
        context_lines = []
        
        for i, line in enumerate(lines):
            if caption and caption[:20] in line:
                # Found caption, get context around it
                start = max(0, i - 5)
                end = min(len(lines), i + 20)
                context_lines = lines[start:end]
                break
        
        if not context_lines:
            # Fallback: return first part of page
            context_lines = lines[:30]
        
        return '\n'.join(context_lines)
    
    def find_sections(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find sections containing keywords."""
        sections = []
        
        # Common section header patterns
        patterns = [
            r'(?:^|\n)\s*(?:\d+[.\s]+)?(' + '|'.join(keywords) + r')[^\n]*\n',
            r'(?:^|\n)\s*(' + '|'.join(keywords) + r')\s*[\n:]',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, self.text, re.IGNORECASE):
                start_pos = match.start()
                
                # Find section end
                section_end = len(self.text)
                next_section = re.search(r'\n\s*(?:\d+[.\s]+)?[A-Z][A-Za-z\s]{2,50}\n', 
                                        self.text[start_pos + 100:])
                if next_section:
                    section_end = start_pos + 100 + next_section.start()
                
                section_text = self.text[start_pos:section_end]
                
                sections.append({
                    'start_pos': start_pos,
                    'end_pos': section_end,
                    'text': section_text,
                    'page': self._get_page_number(start_pos)
                })
        
        # Remove duplicates
        seen = set()
        unique_sections = []
        for s in sorted(sections, key=lambda x: x['start_pos']):
            key = s['start_pos'] // 500
            if key not in seen:
                seen.add(key)
                unique_sections.append(s)
        
        return unique_sections
    
    def _get_page_number(self, char_pos: int) -> int:
        """Get page number for a character position."""
        cum_len = 0
        for page in self.pages:
            cum_len += len(page['text']) + 1
            if cum_len >= char_pos:
                return page['number']
        return len(self.pages)
    
    def get_extraction_report(self) -> Dict:
        """Generate extraction report."""
        return {
            'pdf_path': str(self.pdf_path),
            'total_pages': len(self.pages),
            'total_tables': len(self.extracted_tables),
            'tables_by_type': self._count_tables_by_type(),
            'tables': [
                {
                    'page': t.get('page'),
                    'type': t.get('type'),
                    'type_confidence': t.get('type_confidence'),
                    'confidence': t.get('confidence'),
                    'engine': t.get('engine'),
                    'rows': len(t.get('data', [])),
                    'cols': len(t.get('data', [[]])[0]) if t.get('data') else 0
                }
                for t in self.extracted_tables
            ]
        }
    
    def _count_tables_by_type(self) -> Dict[str, int]:
        """Count tables by type."""
        counts = {}
        for t in self.extracted_tables:
            table_type = t.get('type', 'unknown')
            counts[table_type] = counts.get(table_type, 0) + 1
        return counts
