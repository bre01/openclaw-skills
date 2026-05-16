"""
Figure Manager Module
Manage and organize figures for LaTeX integration.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json


class FigureManager:
    """Manage figure specifications for LaTeX generation."""
    
    def __init__(self):
        self.figures = []
        self._counter = 0
    
    def add_figure(self, 
                   image_path: str,
                   caption: str = "",
                   label: Optional[str] = None,
                   source_table: str = "",
                   source_section: str = "",
                   source: str = "",
                   position: str = "t",
                   width: Optional[str] = None,
                   **kwargs) -> Dict:
        """
        Add a single figure.
        
        Args:
            image_path: Path to image file (without extension for auto-format)
            caption: Figure caption text
            label: LaTeX label (auto-generated if not provided)
            source_table: Reference to source table (e.g., "Table 3")
            source_section: Reference to source section (e.g., "Section 4.2")
            source: Generic source reference
            position: Figure position [t, b, h, p, H]
            width: Figure width (e.g., "\\columnwidth", "8cm")
            **kwargs: Additional parameters
        
        Returns:
            Figure specification dictionary
        """
        self._counter += 1
        
        if label is None:
            label = f"fig:exp{self._counter}"
        
        fig = {
            'type': 'single',
            'image_path': image_path,
            'caption': caption,
            'label': label,
            'source_table': source_table,
            'source_section': source_section,
            'source': source,
            'position': position,
        }
        
        if width:
            fig['width'] = width
        
        fig.update(kwargs)
        
        self.figures.append(fig)
        return fig
    
    def add_subfigure_group(self,
                           subfigures: List[Dict],
                           caption: str = "",
                           label: Optional[str] = None,
                           source_table: str = "",
                           source_section: str = "",
                           source: str = "",
                           position: str = "t",
                           layout: str = "2x1",
                           **kwargs) -> Dict:
        """
        Add a multi-panel figure with subfigures.
        
        Args:
            subfigures: List of subfigure dicts with 'path', 'subcaption', 'label'
            caption: Main figure caption
            label: Main figure label
            source_table: Reference to source table
            source_section: Reference to source section
            source: Generic source reference
            position: Figure position
            layout: Layout specification (e.g., "2x1", "2x2", "3x1")
            **kwargs: Additional parameters
        
        Returns:
            Figure specification dictionary
        """
        self._counter += 1
        
        if label is None:
            label = f"fig:multi{self._counter}"
        
        # Validate subfigures
        for i, sub in enumerate(subfigures):
            if 'path' not in sub:
                raise ValueError(f"Subfigure {i} missing required 'path'")
            if 'subcaption' not in sub:
                sub['subcaption'] = f"({chr(97+i)})"  # (a), (b), etc.
            if 'label' not in sub:
                sub['label'] = f"{label}:{chr(97+i)}"
        
        fig = {
            'type': 'multi',
            'subfigures': subfigures,
            'caption': caption,
            'label': label,
            'source_table': source_table,
            'source_section': source_section,
            'source': source,
            'position': position,
            'layout': layout,
        }
        
        fig.update(kwargs)
        
        self.figures.append(fig)
        return fig
    
    def remove_figure(self, label: str) -> bool:
        """Remove a figure by label."""
        for i, fig in enumerate(self.figures):
            if fig.get('label') == label:
                del self.figures[i]
                return True
        return False
    
    def get_figure(self, label: str) -> Optional[Dict]:
        """Get figure by label."""
        for fig in self.figures:
            if fig.get('label') == label:
                return fig
        return None
    
    def update_figure(self, label: str, **kwargs) -> bool:
        """Update figure properties."""
        fig = self.get_figure(label)
        if fig:
            fig.update(kwargs)
            return True
        return False
    
    def reorder(self, labels: List[str]):
        """Reorder figures based on label list."""
        new_order = []
        for label in labels:
            fig = self.get_figure(label)
            if fig:
                new_order.append(fig)
        
        # Add any figures not in the label list at the end
        for fig in self.figures:
            if fig not in new_order:
                new_order.append(fig)
        
        self.figures = new_order
    
    def clear(self):
        """Remove all figures."""
        self.figures = []
        self._counter = 0
    
    def to_dict(self) -> Dict:
        """Export to dictionary."""
        return {
            'figures': self.figures,
            'count': len(self.figures)
        }
    
    def to_json(self, path: str):
        """Export to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FigureManager':
        """Create from dictionary."""
        manager = cls()
        manager.figures = data.get('figures', [])
        manager._counter = len(manager.figures)
        return manager
    
    @classmethod
    def from_json(cls, path: str) -> 'FigureManager':
        """Create from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_summary(self) -> Dict:
        """Get summary of managed figures."""
        single_count = sum(1 for f in self.figures if f['type'] == 'single')
        multi_count = sum(1 for f in self.figures if f['type'] == 'multi')
        subfigure_count = sum(len(f.get('subfigures', [])) for f in self.figures)
        
        return {
            'total_figures': len(self.figures),
            'single_figures': single_count,
            'multi_panel_figures': multi_count,
            'total_subfigures': subfigure_count,
            'labels': [f.get('label') for f in self.figures]
        }
    
    def validate(self) -> List[str]:
        """Validate all figures and return list of issues."""
        issues = []
        
        for fig in self.figures:
            label = fig.get('label', 'unnamed')
            
            # Check for duplicate labels
            label_count = sum(1 for f in self.figures if f.get('label') == label)
            if label_count > 1:
                issues.append(f"Duplicate label: {label}")
            
            # Check required fields
            if fig['type'] == 'single':
                if 'image_path' not in fig:
                    issues.append(f"Figure {label}: missing image_path")
            elif fig['type'] == 'multi':
                if 'subfigures' not in fig or not fig['subfigures']:
                    issues.append(f"Figure {label}: missing or empty subfigures")
                else:
                    for i, sub in enumerate(fig['subfigures']):
                        if 'path' not in sub:
                            issues.append(f"Figure {label}, subfigure {i}: missing path")
        
        return issues
    
    def print_summary(self):
        """Print human-readable summary."""
        summary = self.get_summary()
        
        print(f"Figure Manager Summary")
        print(f"=" * 40)
        print(f"Total figures: {summary['total_figures']}")
        print(f"  Single figures: {summary['single_figures']}")
        print(f"  Multi-panel figures: {summary['multi_panel_figures']}")
        print(f"  Total subfigures: {summary['total_subfigures']}")
        print()
        print("Labels:")
        for label in summary['labels']:
            print(f"  - {label}")
        
        # Validation
        issues = self.validate()
        if issues:
            print()
            print("Validation Issues:")
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print()
            print("✓ All figures valid")