"""
PDF Loader Module
Load and parse academic paper PDFs for experiment extraction.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import pdfplumber
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("Please install: pip install pdfplumber pymupdf")


class PaperLoader:
    """Load and parse academic paper PDFs."""
    
    def __init__(self):
        self.pdf_path = None
        self.doc = None
        self.text = ""
        self.pages = []
        
    def load(self, pdf_path: str) -> 'PaperLoader':
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
    
    def find_sections(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find sections containing experiment-related content."""
        sections = []
        
        # Common section headers in academic papers
        section_patterns = [
            r'(?:^|\n)\s*(\d+[.\s]+)?(?:' + '|'.join(keywords) + r')[^\n]*\n',
            r'(?:^|\n)\s*(?:' + '|'.join(keywords) + r')\s*[\n:]',
        ]
        
        for pattern in section_patterns:
            for match in re.finditer(pattern, self.text, re.IGNORECASE):
                start_pos = match.start()
                
                # Find section boundaries (next section header or end)
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
        
        # Remove duplicates and sort
        seen = set()
        unique_sections = []
        for s in sorted(sections, key=lambda x: x['start_pos']):
            key = s['start_pos'] // 500  # Group by approximate location
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
    
    def get_tables_with_pdfplumber(self) -> List[Dict]:
        """Extract tables using pdfplumber."""
        tables = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:
                        tables.append({
                            'page': page_num,
                            'data': table,
                            'headers': table[0] if table else [],
                            'rows': table[1:] if len(table) > 1 else []
                        })
        
        return tables
    
    def get_context_around_table(self, table: Dict, window: int = 200) -> str:
        """Get text context around a table."""
        page_num = table['page'] - 1
        if page_num < 0 or page_num >= len(self.pages):
            return ""
        
        page_text = self.pages[page_num]['text']
        
        # Simple approach: return surrounding text from the page
        # For more precise matching, would need table bounding boxes
        return page_text[:window] + "..." + page_text[-window:]