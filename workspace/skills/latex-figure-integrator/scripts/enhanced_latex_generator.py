"""
Enhanced LaTeX Generator with Smart Features.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class SmartLatexConfig:
    """Configuration for smart LaTeX generation."""
    document_class: str = "ieee"
    figure_width: str = r"\columnwidth"
    use_subcaption: bool = True
    use_cleveref: bool = True
    auto_label_tables: bool = True
    auto_cite_source: bool = True
    path_prefix: str = ""


class EnhancedLatexGenerator:
    """Enhanced LaTeX generator with smart features."""
    
    # Document class presets
    DOCUMENT_PRESETS = {
        "ieee": {
            "class": "IEEEtran",
            "figure_width": r"\columnwidth",
            "figure_star_width": r"\textwidth",
            "use_subcaption": True
        },
        "acm": {
            "class": "acmart",
            "figure_width": r"\linewidth",
            "figure_star_width": r"\linewidth",
            "use_subcaption": True
        },
        "neurips": {
            "class": "article",
            "figure_width": r"\textwidth",
            "use_subcaption": True
        }
    }
    
    def __init__(self, document_class: str = "ieee", 
                 use_subcaption: bool = True,
                 use_cleveref: bool = True,
                 figure_path_prefix: str = ""):
        """
        Initialize generator.
        
        Args:
            document_class: Document class preset
            use_subcaption: Use subcaption package
            use_cleveref: Use cleveref for smart references
            figure_path_prefix: Prefix for figure paths
        """
        self.config = self.DOCUMENT_PRESETS.get(document_class, 
                                               self.DOCUMENT_PRESETS["ieee"])
        self.config["use_subcaption"] = use_subcaption
        self.config["use_cleveref"] = use_cleveref
        if figure_path_prefix:
            self.config["path_prefix"] = figure_path_prefix
    
    def generate_smart_figures(self, figure_manager, data_manager=None) -> str:
        """
        Generate LaTeX code with smart features.
        
        Args:
            figure_manager: FigureManager with figure specifications
            data_manager: Optional DataManager with table info
            
        Returns:
            LaTeX code string
        """
        lines = []
        
        # Add table labels if data manager provided
        if data_manager and self.config.get("auto_label_tables"):
            table_labels = self._generate_table_labels(data_manager)
            lines.append("% Auto-generated table labels")
            lines.extend(table_labels)
            lines.append("")
        
        # Generate figures
        for fig in figure_manager.figures:
            lines.append(self._generate_smart_figure(fig, data_manager))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_table_labels(self, data_manager) -> List[str]:
        """Generate table label definitions."""
        lines = []
        tables = data_manager.get("tables", [])
        
        for i, table in enumerate(tables, 1):
            table_id = table.get("id", i)
            caption = table.get("caption", f"Table {i}")
            
            # Create label
            label = f"tab:{table_id}"
            
            lines.append(f"% {caption}")
            lines.append(f"% \\label{{{label}}}")
        
        return lines
    
    def _generate_smart_figure(self, fig: Dict, data_manager=None) -> str:
        """Generate smart LaTeX for a single figure."""
        fig_type = fig.get("type", "single")
        
        if fig_type == "single":
            return self._generate_smart_single_figure(fig, data_manager)
        elif fig_type == "multi":
            return self._generate_smart_multi_figure(fig, data_manager)
        else:
            raise ValueError(f"Unknown figure type: {fig_type}")
    
    def _generate_smart_single_figure(self, fig: Dict, data_manager=None) -> str:
        """Generate smart single figure."""
        position = fig.get("position", "t")
        image_path = self._format_path(fig["image_path"])
        width = fig.get("width", self.config["figure_width"])
        
        # Build smart caption
        caption = self._build_smart_caption(fig, data_manager)
        label = fig.get("label", "")
        
        # Determine if figure should be wide (span both columns)
        is_wide = fig.get("wide", False)
        figure_env = "figure*" if is_wide else "figure"
        actual_width = self.config.get("figure_star_width", r"\textwidth") if is_wide else width
        
        lines = [
            f"\\begin{{{figure_env}}}[{position}]",
            r"\centering",
        ]
        
        # Add includegraphics with options
        include_opts = f"width={actual_width}"
        if fig.get("keepaspectratio", True):
            include_opts += ",keepaspectratio"
        
        lines.append(f"\\includegraphics[{include_opts}]{{{image_path}}}")
        
        # Add caption with source attribution
        if caption:
            lines.append(f"\\caption{{{caption}}}")
        
        # Add label
        if label:
            lines.append(f"\\label{{{label}}}")
        
        lines.append(f"\\end{{{figure_env}}}")
        
        return "\n".join(lines)
    
    def _generate_smart_multi_figure(self, fig: Dict, data_manager=None) -> str:
        """Generate smart multi-panel figure."""
        position = fig.get("position", "t")
        layout = fig.get("layout", "2x1")
        subfigures = fig.get("subfigures", [])
        caption = self._build_smart_caption(fig, data_manager)
        label = fig.get("label", "")
        
        # Parse layout
        cols = int(layout.split("x")[0]) if "x" in layout else 2
        is_wide = fig.get("wide", False)
        figure_env = "figure*" if is_wide else "figure"
        
        lines = [
            f"\\begin{{{figure_env}}}[{position}]",
            r"\centering",
        ]
        
        # Calculate subfigure width
        sub_width = 0.95 / cols
        
        # Generate subfigures
        for i, sub in enumerate(subfigures):
            sub_path = self._format_path(sub["path"])
            sub_caption = sub.get("subcaption", f"({chr(97+i)})")
            sub_label = sub.get("label", "")
            
            if self.config["use_subcaption"]:
                lines.append(f"\\begin{{subfigure}}[t]{{{sub_width}\\textwidth}}")
                lines.append(r"\centering")
                lines.append(f"\\includegraphics[width=\\linewidth]{{{sub_path}}}")
                
                # Add subcaption
                if sub.get("caption_above", False):
                    lines.append(f"\\caption{{{sub_caption}}}")
                else:
                    lines.append(f"\\caption*{{{sub_caption}}}")  # Unnumbered
                
                if sub_label:
                    lines.append(f"\\label{{{sub_label}}}")
                lines.append(r"\end{subfigure}")
            else:
                # Without subcaption package
                lines.append(r"\begin{minipage}[t]" + f"{{{sub_width}\\textwidth}}")
                lines.append(r"\centering")
                lines.append(f"\\includegraphics[width=\\linewidth]{{{sub_path}}}")
                lines.append(f"{sub_caption}")
                if sub_label:
                    lines.append(f"\\label{{{sub_label}}}")
                lines.append(r"\end{minipage}")
            
            # Add horizontal space or line break
            if (i + 1) % cols == 0 and i < len(subfigures) - 1:
                lines.append("")
            elif i < len(subfigures) - 1:
                lines.append(r"\hfill")
        
        # Main caption and label
        if caption:
            lines.append(f"\\caption{{{caption}}}")
        if label:
            lines.append(f"\\label{{{label}}}")
        
        lines.append(f"\\end{{{figure_env}}}")
        
        return "\n".join(lines)
    
    def _build_smart_caption(self, fig: Dict, data_manager=None) -> str:
        """Build caption with smart source attribution."""
        caption = fig.get("caption", "")
        sources = []
        
        # Check for table reference
        source_table = fig.get("source_table", "")
        if source_table:
            label = self._table_ref_to_label(source_table)
            if self.config.get("use_cleveref", False):
                sources.append(f"Based on \\Cref{{{label}}}")
            else:
                sources.append(f"Based on Table~\\ref{{{label}}}")
        
        # Check for section reference
        source_section = fig.get("source_section", "")
        if source_section:
            sources.append(f"Based on {source_section}")
        
        # Check for equation reference
        source_eq = fig.get("source_equation", "")
        if source_eq:
            sources.append(f"Based on {source_eq}")
        
        # Combine caption and sources
        if caption and sources:
            return f"{caption} {'. '.join(sources)}."
        elif caption:
            return caption
        elif sources:
            return " ".join(sources) + "."
        
        return ""
    
    def _table_ref_to_label(self, ref: str) -> str:
        """Convert table reference to LaTeX label."""
        ref_lower = ref.lower()
        
        # Extract table number
        import re
        match = re.search(r'(\d+)', ref)
        if match:
            return f"tab:{match.group(1)}"
        
        # Roman numerals
        roman_match = re.search(r'([ivx]+)', ref_lower)
        if roman_match:
            roman = roman_match.group(1)
            return f"tab:{roman}"
        
        return ref.replace(" ", "_").lower()
    
    def _format_path(self, path: str) -> str:
        """Format image path with prefix."""
        if self.config.get("path_prefix"):
            prefix = self.config["path_prefix"].rstrip("/")
            path = path.lstrip("/")
            return f"{prefix}/{path}"
        return path
    
    def generate_enhanced_preamble(self, additional_packages: List[str] = None) -> str:
        """Generate enhanced preamble with all required packages."""
        lines = [
            "% Enhanced LaTeX Preamble",
            "% Generated by Enhanced LaTeX Generator",
            "",
            "% Graphics and figures",
            r"\usepackage{graphicx}",
            r"\usepackage[font=small,labelfont=bf]{caption}",
        ]
        
        if self.config["use_subcaption"]:
            lines.append(r"\usepackage{subcaption}")
        
        if self.config["use_cleveref"]:
            lines.append(r"\usepackage{cleveref}")
            lines.append(r"\crefname{table}{Table}{Tables}")
            lines.append(r"\crefname{figure}{Figure}{Figures}")
        
        lines.extend([
            "",
            "% Math",
            r"\usepackage{amsmath}",
            r"\usepackage{amssymb}",
            "",
            "% Tables",
            r"\usepackage{booktabs}",
            r"\usepackage{array}",
            r"\usepackage{multirow}",
            "",
            "% Colors",
            r"\usepackage{xcolor}",
            "",
            "% Links (load last)",
            r"\usepackage{hyperref}",
        ])
        
        if additional_packages:
            lines.extend(["", "% Additional packages"])
            for pkg in additional_packages:
                lines.append(rf"\usepackage{{{pkg}}}")
        
        lines.extend([
            "",
            "% Graphics path",
            f"\\graphicspath{{{{figures/}}}}"
        ])
        
        return "\n".join(lines)
    
    def generate_standalone_document(self, figure_manager, 
                                     title: str = "Figures",
                                     author: str = "",
                                     data_manager=None) -> str:
        """Generate complete standalone LaTeX document."""
        lines = [
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[margin=1in]{geometry}",
            "",
            self.generate_enhanced_preamble(),
            "",
            r"\title{" + title + r"}",
        ]
        
        if author:
            lines.append(r"\author{" + author + r"}")
        
        lines.extend([
            r"\date{\today}",
            "",
            r"\begin{document}",
            "",
            r"\maketitle",
            "",
            self.generate_smart_figures(figure_manager, data_manager),
            "",
            r"\end{document}",
        ])
        
        return "\n".join(lines)
    
    def generate_figure_page(self, figure_manager, page_number: int = 1) -> str:
        """Generate LaTeX for a specific page of figures."""
        # This could be used to split figures across pages
        pass


class FigurePlacementOptimizer:
    """Optimize figure placement in LaTeX document."""
    
    def __init__(self):
        self.figures = []
        self.constraints = []
    
    def add_figure(self, figure: Dict, preferred_page: Optional[int] = None):
        """Add figure with optional placement preference."""
        self.figures.append({
            "figure": figure,
            "preferred_page": preferred_page
        })
    
    def add_constraint(self, figure_a: str, figure_b: str, 
                      relation: str = "after"):
        """
        Add ordering constraint.
        
        Args:
            figure_a: Label of first figure
            figure_b: Label of second figure
            relation: "after", "before", "same_page", "facing"
        """
        self.constraints.append({
            "a": figure_a,
            "b": figure_b,
            "relation": relation
        })
    
    def optimize(self) -> List[Dict]:
        """Optimize figure ordering and placement."""
        # Simple implementation: sort by preferred page
        sorted_figures = sorted(
            self.figures,
            key=lambda x: x.get("preferred_page", 999)
        )
        
        # Apply constraints (simplified)
        for constraint in self.constraints:
            # TODO: Implement constraint satisfaction
            pass
        
        return [f["figure"] for f in sorted_figures]
    
    def suggest_placements(self) -> Dict[str, str]:
        """Suggest optimal figure placements."""
        suggestions = {}
        
        for fig in self.figures:
            label = fig["figure"].get("label", "")
            pref_page = fig.get("preferred_page")
            
            if pref_page:
                suggestions[label] = f"page {pref_page}"
            else:
                suggestions[label] = "floating (tbp)"
        
        return suggestions
