"""
Complete Pipeline Example
Demonstrates how all three skills work together.
"""

import sys
sys.path.insert(0, 'skills/paper-experiment-extractor/scripts')
sys.path.insert(0, 'skills/experiment-visualizer/scripts')
sys.path.insert(0, 'skills/latex-figure-integrator/scripts')

from paper_experiment_extractor.scripts.pdf_loader import PaperLoader
from paper_experiment_extractor.scripts.table_extractor import TableExtractor
from paper_experiment_extractor.scripts.metric_parser import MetricParser
from paper_experiment_extractor.scripts.exporter import DataExporter

from experiment_visualizer.scripts.visualizer import ExperimentVisualizer
from experiment_visualizer.scripts.style_config import StyleManager

from latex_figure_integrator.scripts.latex_generator import LatexFigureGenerator
from latex_figure_integrator.scripts.figure_manager import FigureManager


def run_complete_pipeline(pdf_path: str, output_dir: str = "output"):
    """
    Run the complete paper-to-figures pipeline.
    
    Args:
        pdf_path: Path to paper PDF
        output_dir: Output directory for all generated files
    """
    from pathlib import Path
    Path(output_dir).mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Paper-to-Figures Pipeline")
    print("=" * 60)
    
    # ============================================================
    # STEP 1: Extract Data from Paper
    # ============================================================
    print("\n📄 Step 1: Extracting experimental data from paper...")
    
    # Load PDF
    loader = PaperLoader()
    paper = loader.load(pdf_path)
    print(f"   Loaded {len(paper.pages)} pages")
    
    # Find experiment sections
    exp_sections = paper.find_sections([
        "experiment", "result", "evaluation", 
        "ablation", "comparison", "performance"
    ])
    print(f"   Found {len(exp_sections)} experiment sections")
    
    # Extract tables
    extractor = TableExtractor()
    tables = extractor.extract_tables(paper, sections=exp_sections)
    print(f"   Extracted {len(tables)} tables")
    for t in tables:
        print(f"     - Page {t['page']}: {t['type']} table")
    
    # Parse metrics
    parser = MetricParser()
    metrics = parser.parse(tables)
    print(f"   Parsed {len(metrics)} metric sets")
    
    # Export data
    exporter = DataExporter()
    json_path = f"{output_dir}/extracted_data.json"
    csv_path = f"{output_dir}/extracted_data.csv"
    
    exporter.to_json(metrics, json_path)
    exporter.to_csv(metrics, csv_path)
    print(f"   ✓ Exported to {json_path}")
    print(f"   ✓ Exported to {csv_path}")
    
    # ============================================================
    # STEP 2: Generate Visualizations
    # ============================================================
    print("\n📊 Step 2: Generating visualizations...")
    
    # Create visualizer with IEEE style
    viz = ExperimentVisualizer(style='ieee')
    
    figure_manager = FigureManager()
    figure_paths = []
    
    for i, metric in enumerate(metrics):
        exp_data = metric['data']
        exp_type = exp_data.get('experiment_type', 'unknown')
        
        try:
            # Generate figure
            fig = viz.plot(metric)
            
            # Determine filename
            base_name = f"figure_{i+1:02d}_{exp_type}"
            pdf_path_out = f"{output_dir}/{base_name}.pdf"
            png_path_out = f"{output_dir}/{base_name}.png"
            
            # Save both formats
            viz.save(fig, pdf_path_out, formats=['pdf'])
            viz.save(fig, png_path_out, formats=['png'])
            
            figure_paths.append({
                'pdf': pdf_path_out,
                'png': png_path_out,
                'type': exp_type,
                'caption': f"{exp_type.replace('_', ' ').title()} results."
            })
            
            print(f"   ✓ Generated {base_name}.pdf")
            
            # Add to figure manager
            source = metric.get('source', {})
            figure_manager.add_figure(
                image_path=pdf_path_out,
                caption=f"{exp_type.replace('_', ' ').title()} results.",
                label=f"fig:{exp_type}_{i+1}",
                source_table=f"Table {source.get('page', '?')}",
                position="t"
            )
            
        except Exception as e:
            print(f"   ⚠️  Could not generate figure for {exp_type}: {e}")
    
    # ============================================================
    # STEP 3: Generate LaTeX Integration
    # ============================================================
    print("\n📝 Step 3: Generating LaTeX integration...")
    
    # Create LaTeX generator
    latex_gen = LatexFigureGenerator(
        document_class="ieee",
        figure_path_prefix="figures/"
    )
    
    # Generate LaTeX code
    latex_code = latex_gen.generate(figure_manager)
    
    # Save LaTeX
    latex_path = f"{output_dir}/figures.tex"
    with open(latex_path, 'w') as f:
        f.write(latex_code)
    print(f"   ✓ Generated {latex_path}")
    
    # Generate preamble
    preamble_path = f"{output_dir}/preamble.tex"
    with open(preamble_path, 'w') as f:
        f.write(latex_gen.generate_preamble())
    print(f"   ✓ Generated {preamble_path}")
    
    # Generate full standalone document
    full_doc_path = f"{output_dir}/figures_standalone.tex"
    with open(full_doc_path, 'w') as f:
        f.write(latex_gen.generate_full_document(figure_manager))
    print(f"   ✓ Generated {full_doc_path}")
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}/")
    print(f"  - Data files: extracted_data.json, extracted_data.csv")
    print(f"  - Figures: {len(figure_paths)} PDF/PNG pairs")
    print(f"  - LaTeX: figures.tex, preamble.tex")
    print(f"\nTo use in your paper:")
    print(f"  1. Copy figures to your paper's figures/ directory")
    print(f"  2. \\input{{{output_dir}/figures}} in your main .tex file")
    print(f"  3. Include required packages from preamble.tex")
    print()
    
    return {
        'metrics': metrics,
        'figures': figure_paths,
        'latex': latex_code
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper-to-Figures Pipeline")
    parser.add_argument("pdf", help="Path to paper PDF")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    
    args = parser.parse_args()
    
    run_complete_pipeline(args.pdf, args.output)