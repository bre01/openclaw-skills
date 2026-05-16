"""
LaTeX Generator Module
Generate LaTeX figure environments from figure specifications.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentConfig:
    """Configuration for LaTeX document style."""
    document_class: str = "article"
    figure_width: str = r"\textwidth"
    use_subcaption: bool = True
    caption_style: str = "default"
    path_prefix: str = ""


# Document class presets
DOCUMENT_PRESETS = {
    "ieee": DocumentConfig(
        document_class="ieee",
        figure_width=r"\columnwidth",
        use_subcaption=True,
        caption_style="ieee"
    ),
    "acm": DocumentConfig(
        document_class="acm",
        figure_width=r"\linewidth",
        use_subcaption=True,
        caption_style="acm"
    ),
    "neurips": DocumentConfig(
        document_class="neurips",
        figure_width=r"\textwidth",
        use_subcaption=True,
        caption_style="neurips"
    ),
    "article": DocumentConfig(
        document_class="article",
        figure_width=r"\textwidth",
        use_subcaption=True,
        caption_style="default"
    )
}


class LatexFigureGenerator:
    """Generate LaTeX figure code."""
    
    def __init__(self, document_class: str = "ieee", 
                 use_subcaption: bool = True,
                 figure_path_prefix: str = ""):
        """
        Initialize generator.
        
        Args:
            document_class: 'ieee', 'acm', 'neurips', or 'article'
            use_subcaption: Whether to use subcaption package
            figure_path_prefix: Prefix path for all figure files
        """
        if document_class in DOCUMENT_PRESETS:
            self.config = DOCUMENT_PRESETS[document_class]
        else:
            self.config = DocumentConfig(document_class=document_class)
        
        self.config.use_subcaption = use_subcaption
        if figure_path_prefix:
            self.config.path_prefix = figure_path_prefix
    
    def generate(self, figure_manager) -> str:
        """
        Generate complete LaTeX code for all figures.
        
        Args:
            figure_manager: FigureManager instance
        
        Returns:
            LaTeX code as string
        """
        lines = []
        
        for fig in figure_manager.figures:
            lines.append(self._generate_figure(fig))
            lines.append("")  # Blank line between figures
        
        return "\n".join(lines)
    
    def _generate_figure(self, fig: Dict[str, Any]) -> str:
        """Generate LaTeX for a single figure specification."""
        fig_type = fig.get('type', 'single')
        
        if fig_type == 'single':
            return self._generate_single_figure(fig)
        elif fig_type == 'multi':
            return self._generate_multi_figure(fig)
        else:
            raise ValueError(f"Unknown figure type: {fig_type}")
    
    def _generate_single_figure(self, fig: Dict) -> str:
        """Generate LaTeX for single figure."""
        position = fig.get('position', 't')
        image_path = self._format_path(fig['image_path'])
        width = fig.get('width', self.config.figure_width)
        caption = self._build_caption(fig)
        label = fig.get('label', '')
        
        lines = [
            f"\\begin{{figure}}[{position}]",
            r"\centering",
            f"\\includegraphics[width={width}]{{{image_path}}}",
        ]
        
        # Add caption
        if caption:
            lines.append(f"\\caption{{{caption}}}")
        
        # Add label
        if label:
            lines.append(f"\\label{{{label}}}")
        
        lines.append(r"\end{figure}")
        
        return "\n".join(lines)
    
    def _generate_multi_figure(self, fig: Dict) -> str:
        """Generate LaTeX for multi-panel figure."""
        position = fig.get('position', 't')
        layout = fig.get('layout', '2x1')  # columns x rows
        subfigures = fig.get('subfigures', [])
        caption = self._build_caption(fig)
        label = fig.get('label', '')
        
        # Parse layout
        cols = int(layout.split('x')[0]) if 'x' in layout else 2
        
        lines = [
            f"\\begin{{figure}}[{position}]",
            r"\centering",
        ]
        
        # Calculate subfigure width
        sub_width = 0.95 / cols
        
        # Generate subfigures
        for i, sub in enumerate(subfigures):
            sub_path = self._format_path(sub['path'])
            sub_caption = sub.get('subcaption', f"({chr(97+i)})")  # (a), (b), etc.
            sub_label = sub.get('label', '')
            
            if self.config.use_subcaption:
                lines.append(f"\\begin{{subfigure}}[t]{{{sub_width}\\textwidth}}")
                lines.append(r"\centering")
                lines.append(f"\\includegraphics[width=\\linewidth]{{{sub_path}}}")
                lines.append(f"\\caption{{{sub_caption}}}")
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
            
            # Add line break after each row
            if (i + 1) % cols == 0 and i < len(subfigures) - 1:
                lines.append("")
        
        # Add main caption and label
        if caption:
            lines.append(f"\\caption{{{caption}}}")
        if label:
            lines.append(f"\\label{{{label}}}")
        
        lines.append(r"\end{figure}")
        
        return "\n".join(lines)
    
    def _build_caption(self, fig: Dict) -> str:
        """Build caption text with source attribution."""
        caption = fig.get('caption', '')
        source = fig.get('source', '')
        source_table = fig.get('source_table', '')
        source_section = fig.get('source_section', '')
        
        # Determine source reference
        source_ref = ""
        if source_table:
            source_ref = f"Based on Table~\\ref{{{self._ref_to_label(source_table)}}}."
        elif source_section:
            source_ref = f"Based on {source_section}."
        elif source:
            source_ref = f"Based on {source}."
        
        # Combine caption and source
        if caption and source_ref:
            return f"{caption} {source_ref}"
        elif caption:
            return caption
        elif source_ref:
            return source_ref
        
        return ""
    
    def _ref_to_label(self, ref: str) -> str:
        """Convert reference (e.g., 'Table 3') to label (e.g., 'tab:results')."""
        # Simple conversion - could be more sophisticated
        ref_lower = ref.lower()
        if 'table' in ref_lower or 'tab.' in ref_lower:
            # Extract number
            import re
            match = re.search(r'(\d+)', ref)
            if match:
                return f"tab:{match.group(1)}"
        return ref.replace(' ', '_').lower()
    
    def _format_path(self, path: str) -> str:
        """Format image path with prefix."""
        if self.config.path_prefix:
            # Remove leading slash if present
            prefix = self.config.path_prefix.rstrip('/')
            path = path.lstrip('/')
            return f"{prefix}/{path}"
        return path
    
    def generate_preamble(self) -> str:
        """Generate required LaTeX preamble."""
        lines = [
            "% Required packages for figures",
            r"\usepackage{graphicx}",
            r"\usepackage{caption}",
        ]
        
        if self.config.use_subcaption:
            lines.append(r"\usepackage{subcaption}")
        
        lines.append("")
        lines.append("% Figure path configuration")
        prefix = self.config.path_prefix.rstrip('/')
        lines.append(r"\graphicspath{{" + prefix + "/}}")
        
        return "\n".join(lines)
    
    def generate_full_document(self, figure_manager, title: str = "Figures") -> str:
        """Generate a standalone LaTeX document with all figures."""
        lines = [
            r"\documentclass{article}",
            r"\usepackage[margin=1in]{geometry}",
            self.generate_preamble(),
            "",
            r"\begin{document}",
            f"\\section*{{{title}}}",
            "",
            self.generate(figure_manager),
            "",
            r"\end{document}",
        ]
        
        return "\n".join(lines)