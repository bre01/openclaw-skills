"""
Unified Paper-to-Figures Pipeline
Complete workflow from PDF extraction to visualization.
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/skills/paper-experiment-extractor/scripts')
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/skills/experiment-visualizer/scripts')
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/skills/latex-figure-integrator/scripts')

import argparse
import json
import os
from pathlib import Path
from typing import Dict
from enhanced_pdf_loader import EnhancedPaperLoader
from enhanced_metric_parser import EnhancedMetricParser
from visualizer import ExperimentVisualizer
from figure_manager import FigureManager
from latex_generator import LatexFigureGenerator


class PaperToFiguresPipeline:
    """Complete pipeline from paper to publication figures."""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.loader = None
        self.parser = EnhancedMetricParser()
        self.visualizer = ExperimentVisualizer(style='ieee')
        self.figure_manager = FigureManager()
        
        self.extracted_data = []
        self.generated_figures = []
        
    def run(self, pdf_path: str, auto_viz: bool = True) -> Dict:
        """
        Run complete pipeline.
        
        Args:
            pdf_path: Path to PDF file
            auto_viz: Automatically generate visualizations
            
        Returns:
            Pipeline results summary
        """
        print("=" * 60)
        print("Paper-to-Figures Pipeline")
        print("=" * 60)
        
        # Step 1: Extract tables
        print("\n📄 Step 1: Extracting tables from PDF...")
        self.loader = EnhancedPaperLoader()
        self.loader.load(pdf_path)
        tables = self.loader.extract_all_tables()
        
        print(f"   Found {len(tables)} tables")
        for t in tables:
            print(f"   - Page {t.get('page')}: {t.get('type')} (confidence: {t.get('type_confidence', 0):.2f})")
        
        # Step 2: Parse metrics
        print("\n📊 Step 2: Parsing metrics and recommending visualizations...")
        self.extracted_data = self.parser.parse(tables)
        
        for d in self.extracted_data:
            exp_type = d.get('data', {}).get('experiment_type', 'unknown')
            viz = d.get('visualization', {})
            print(f"   - {exp_type}: {viz.get('chart_type')} (confidence: {viz.get('confidence', 0):.2f})")
        
        # Step 3: Generate visualizations
        if auto_viz and self.extracted_data:
            print("\n📈 Step 3: Generating visualizations...")
            self._generate_visualizations()
        
        # Step 4: Export data
        print("\n💾 Step 4: Exporting data...")
        self._export_data()
        
        # Step 5: Generate LaTeX
        print("\n📝 Step 5: Generating LaTeX integration files...")
        self._generate_latex()
        
        # Generate report
        print("\n📋 Generating final report...")
        report = self._generate_report()
        
        print("\n" + "=" * 60)
        print("Pipeline Complete!")
        print("=" * 60)
        
        return report
    
    def _generate_visualizations(self):
        """Generate visualizations based on recommendations."""
        figures_dir = self.output_dir / "figures"
        figures_dir.mkdir(exist_ok=True)
        
        for i, data in enumerate(self.extracted_data):
            exp_type = data.get('data', {}).get('experiment_type', 'unknown')
            viz_rec = data.get('visualization', {})
            chart_type = viz_rec.get('chart_type', 'auto')
            
            try:
                if chart_type == 'heatmap' or exp_type == 'confusion_matrix':
                    fig = self.visualizer.plot_confusion_matrix(data['data'])
                elif chart_type in ['bar_chart', 'grouped_bar'] or exp_type in ['model_comparison', 'hardware_comparison']:
                    fig = self.visualizer.plot_comparison_bar(data['data'])
                elif chart_type == 'ablation_bar' or exp_type == 'ablation':
                    # Use first available metric for ablation
                    metrics = data['data'].get('variants', [{}])[0].get('metrics', {}).keys()
                    metric = list(metrics)[0] if metrics else 'accuracy'
                    fig = self.visualizer.plot_ablation(data['data'], metric=metric)
                elif chart_type == 'line_plot' or exp_type == 'training_curve':
                    fig = self.visualizer.plot_training_curves(data['data'])
                else:
                    # Default to auto
                    fig = self.visualizer.plot(data)
                
                # Save figure
                fig_path = figures_dir / f"figure_{i+1:02d}_{exp_type}"
                saved = self.visualizer.save(fig, str(fig_path), formats=['png', 'pdf'])
                
                self.generated_figures.append({
                    'index': i + 1,
                    'type': exp_type,
                    'chart_type': chart_type,
                    'path': str(fig_path),
                    'files': saved
                })
                
                print(f"   ✓ Figure {i+1}: {exp_type} ({chart_type})")
                
            except Exception as e:
                print(f"   ✗ Figure {i+1}: Failed - {e}")
    
    def _export_data(self):
        """Export extracted data to JSON and CSV."""
        from exporter import DataExporter
        
        exporter = DataExporter()
        
        # Export JSON
        json_path = self.output_dir / "extracted_data.json"
        output = {
            'metadata': {
                'version': '2.0',
                'source': 'paper-to-figures-pipeline',
                'total_experiments': len(self.extracted_data)
            },
            'experiments': self.extracted_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"   ✓ JSON: {json_path}")
        
        # Export individual CSVs for each table type
        for i, exp in enumerate(self.extracted_data):
            exp_type = exp.get('data', {}).get('experiment_type', 'unknown')
            
            if exp_type == 'model_comparison':
                csv_path = self.output_dir / f"comparison_{i+1}.csv"
                exporter.to_csv([exp], str(csv_path))
                print(f"   ✓ CSV: {csv_path}")
    
    def _generate_latex(self):
        """Generate LaTeX integration files."""
        # Add figures to manager
        for fig in self.generated_figures:
            fig_path = f"figures/{Path(fig['path']).name}.pdf"
            
            self.figure_manager.add_figure(
                image_path=fig_path,
                caption=f"{fig['type'].replace('_', ' ').title()} results.",
                label=f"fig:{fig['type']}_{fig['index']}",
                position='t',
                width=r'\textwidth'
            )
        
        # Generate LaTeX files
        generator = LatexFigureGenerator(document_class='ieee')
        
        # Preamble
        preamble = generator.generate_preamble()
        preamble_path = self.output_dir / "preamble.tex"
        with open(preamble_path, 'w') as f:
            f.write(preamble)
        print(f"   ✓ LaTeX preamble: {preamble_path}")
        
        # Figures
        figures_tex = generator.generate(self.figure_manager)
        figures_path = self.output_dir / "figures.tex"
        with open(figures_path, 'w') as f:
            f.write(figures_tex)
        print(f"   ✓ LaTeX figures: {figures_path}")
    
    def _generate_report(self) -> Dict:
        """Generate final report."""
        report = {
            'pipeline_version': '2.0',
            'output_directory': str(self.output_dir),
            'extraction': self.loader.get_extraction_report() if self.loader else {},
            'parsing': self.parser.get_summary(),
            'visualizations': {
                'total_figures': len(self.generated_figures),
                'figures': self.generated_figures
            },
            'files_generated': {
                'data': ['extracted_data.json'],
                'visualizations': [f"figures/{Path(f['path']).name}.{{pdf,png}}" for f in self.generated_figures],
                'latex': ['preamble.tex', 'figures.tex']
            }
        }
        
        # Save report
        report_path = self.output_dir / "pipeline_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Paper-to-Figures Pipeline')
    parser.add_argument('pdf', help='Path to PDF file')
    parser.add_argument('-o', '--output', default='./output', help='Output directory')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization generation')
    
    args = parser.parse_args()
    
    pipeline = PaperToFiguresPipeline(output_dir=args.output)
    report = pipeline.run(args.pdf, auto_viz=not args.no_viz)
    
    print(f"\n📁 Output directory: {report['output_directory']}")
    print(f"📊 Total experiments: {report['parsing']['total_experiments']}")
    print(f"📈 Total figures: {report['visualizations']['total_figures']}")


if __name__ == '__main__':
    main()
