---
name: paper-experiment-extractor
description: Extract structured experimental data from academic papers (PDF). Enhanced with multi-engine table extraction, LLM-assisted correction, and automatic visualization type detection. Output standardized JSON/CSV with clear visualization recommendations.

**当以下情况时使用此 Skill**：
(1) 需要从论文 PDF 中提取实验表格
(2) 需要识别混淆矩阵、准确率、参数量、FLOPs 等指标
(3) 需要识别消融实验、对比实验、硬件对比等实验类型
(4) 需要获取可视化建议（自动匹配图表类型）
(5) 用户提到"提取表格"、"解析论文"、"实验数据"
---

# Paper Experiment Extractor (Enhanced)

Extract structured experimental data from academic paper PDFs with enhanced accuracy and intelligent type detection.

## What's New in v2.0

### 🔧 Multi-Engine Table Extraction
- **pdfplumber**: Best for simple tables
- **PyMuPDF**: Handles complex layouts
- **Heuristic Parser**: Text-based table detection
- **Smart Merging**: Combines results from all engines

### 🧠 Smart Table Classification
Automatically classifies tables into types:
- `confusion_matrix` - Classification results
- `model_comparison` - Multi-model performance comparison
- `hardware_comparison` - Platform/frequency comparisons
- `ablation` - Ablation study results
- `training_curve` - Training metrics over time

### 📊 Automatic Visualization Recommendations
Each parsed experiment includes:
- Recommended chart type (heatmap, bar chart, radar, etc.)
- Confidence score for the recommendation
- Alternative visualization options
- Required data fields check

## Quick Start

### Basic Usage

```python
from scripts.enhanced_pdf_loader import EnhancedPaperLoader
from scripts.enhanced_metric_parser import EnhancedMetricParser

# Load and extract
loader = EnhancedPaperLoader()
loader.load("paper.pdf")
tables = loader.extract_all_tables()

# Parse with visualization recommendations
parser = EnhancedMetricParser()
parsed = parser.parse(tables)

# Each result includes visualization recommendations
for exp in parsed:
    viz_rec = exp['visualization']
    print(f"Recommended: {viz_rec['chart_type']} (confidence: {viz_rec['confidence']})")
```

### Unified Pipeline

```python
from scripts.unified_pipeline import PaperToFiguresPipeline

pipeline = PaperToFiguresPipeline(output_dir="./output")
report = pipeline.run("paper.pdf", auto_viz=True)

print(f"Extracted: {report['parsing']['total_experiments']} experiments")
print(f"Generated: {report['visualizations']['total_figures']} figures")
```

## Extraction Results

### Table Structure
```json
{
  "page": 5,
  "type": "hardware_comparison",
  "type_confidence": 0.85,
  "confidence": 0.92,
  "engine": "pdfplumber",
  "data": [...],
  "headers": [...],
  "caption": "Inference time at different CPU frequencies",
  "context": "...",
  "metadata": {
    "suggested_units": {"time_ms": "milliseconds"},
    "suggested_metrics": ["time_ms"]
  }
}
```

### Parsed Experiment with Viz Recommendation
```json
{
  "source": {
    "page": 5,
    "type": "hardware_comparison",
    "confidence": 0.85
  },
  "data": {
    "experiment_type": "hardware_comparison",
    "models": [...],
    "frequencies": ["408 MHz", "600 MHz", "816 MHz"],
    "platforms": ["Linux", "Zephyr"]
  },
  "visualization": {
    "chart_type": "grouped_comparison",
    "confidence": 0.88,
    "requirements_met": true,
    "alternatives": [
      {"chart_type": "multi_subplot", "reason": "Many frequency conditions"}
    ]
  }
}
```

## Supported Table Types

### Confusion Matrix
- Square matrix structure
- Class labels
- Automatic precision/recall calculation

**Recommended Viz:** Heatmap with annotations

### Model Comparison
- Multiple models
- Various metrics (accuracy, F1, params, FLOPs)

**Recommended Viz:** 
- Bar chart (2-3 metrics)
- Radar chart (3+ metrics)

### Hardware Comparison
- Multiple platforms (Linux, GPU, etc.)
- Multiple conditions (frequencies, batch sizes)

**Recommended Viz:** Grouped bar chart

### Ablation Study
- Baseline + variants
- Performance deltas

**Recommended Viz:** Ablation bar chart with delta annotations

### Training Curves
- Epochs/iterations
- Loss and accuracy metrics

**Recommended Viz:** Line plot with smoothing

## Data Export

### JSON Export
```python
from scripts.exporter import DataExporter

exporter = DataExporter()
exporter.to_json(parsed, "output.json")
```

### CSV Export
```python
# Exports tabular data only (comparison, ablation)
exporter.to_csv(parsed, "output.csv")

# Separate CSV for each table type
exporter.export_comparison_csv(parsed, "comparison.csv")
exporter.export_ablation_csv(parsed, "ablation.csv")
```

## Advanced Features

### Table Correction
```python
from enhanced_pdf_loader import LLMAssistedCorrector

corrector = LLMAssistedCorrector()
corrected_table = corrector.correct_table_structure(table)
```

### Custom Classification
```python
from enhanced_pdf_loader import SmartTableClassifier

classifier = SmartTableClassifier()
table_type, confidence = classifier.classify(table, context)
```

## Dependencies

```bash
pip install pdfplumber pymupdf pandas numpy
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `enhanced_pdf_loader.py` | Multi-engine PDF table extraction |
| `enhanced_metric_parser.py` | Metric parsing with viz recommendations |
| `unified_pipeline.py` | Complete pipeline from PDF to figures |
| `exporter.py` | JSON/CSV export utilities |

## Migration from v1.0

Old code:
```python
from scripts.pdf_loader import PaperLoader
from scripts.table_extractor import TableExtractor

loader = PaperLoader()
loader.load("paper.pdf")
tables = loader.get_tables_with_pdfplumber()
```

New code:
```python
from scripts.enhanced_pdf_loader import EnhancedPaperLoader

loader = EnhancedPaperLoader()
loader.load("paper.pdf")
tables = loader.extract_all_tables()  # Multi-engine extraction
```
