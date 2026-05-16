# 论文实验可视化 Skill 套装

三个协同工作的 OpenClaw Skill，实现从论文 PDF 提取实验数据 → 生成可视化图表 → 集成到 LaTeX 论文的完整工作流。

---

## 📁 Skill 结构

```
skills/
├── paper-experiment-extractor/     # Skill 1: 数据提取
│   ├── SKILL.md
│   └── scripts/
│       ├── pdf_loader.py           # PDF 加载和章节检测
│       ├── table_extractor.py      # 表格提取和分类
│       ├── metric_parser.py        # 指标解析和标准化
│       └── exporter.py             # JSON/CSV 导出
│
├── experiment-visualizer/          # Skill 2: 可视化生成
│   ├── SKILL.md
│   └── scripts/
│       ├── style_config.py         # 学术样式配置
│       └── visualizer.py           # 图表生成主类
│
├── latex-figure-integrator/        # Skill 3: LaTeX 集成
│   ├── SKILL.md
│   └── scripts/
│       ├── latex_generator.py      # LaTeX 代码生成
│       └── figure_manager.py       # 图表管理
│
└── complete_pipeline.py            # 完整流程示例
```

---

## 🚀 快速开始

### 安装依赖

```bash
pip install pdfplumber pymupdf pandas numpy matplotlib seaborn
```

### 使用单个 Skill

#### 1. 提取论文数据

```python
from paper_experiment_extractor.scripts.pdf_loader import PaperLoader
from paper_experiment_extractor.scripts.table_extractor import TableExtractor
from paper_experiment_extractor.scripts.metric_parser import MetricParser
from paper_experiment_extractor.scripts.exporter import DataExporter

# 加载论文
loader = PaperLoader()
paper = loader.load("paper.pdf")

# 提取表格
tables = TableExtractor().extract_tables(paper)

# 解析指标
metrics = MetricParser().parse(tables)

# 导出
DataExporter().to_json(metrics, "output.json")
```

#### 2. 生成可视化

```python
from experiment_visualizer.scripts.visualizer import ExperimentVisualizer

viz = ExperimentVisualizer(style='ieee')  # 或 'acm', 'neurips'

for metric in metrics:
    fig = viz.plot(metric)  # 自动选择图表类型
    viz.save(fig, "figure.pdf")
```

#### 3. 生成 LaTeX

```python
from latex_figure_integrator.scripts.latex_generator import LatexFigureGenerator
from latex_figure_integrator.scripts.figure_manager import FigureManager

manager = FigureManager()
manager.add_figure(
    image_path="figure.pdf",
    caption="Classification results",
    label="fig:results",
    source_table="Table 3"
)

generator = LatexFigureGenerator(document_class="ieee")
latex_code = generator.generate(manager)
```

### 完整流程

```bash
python skills/complete_pipeline.py paper.pdf -o output/
```

---

## 📊 支持的图表类型

| 实验类型 | 自动匹配图表 | 样式 |
|---------|-------------|------|
| 混淆矩阵 | 热力图 (Heatmap) | 带精确率/召回率标注 |
| 模型对比 | 柱状图 (Bar Chart) | 支持误差棒和显著性标记 |
| 消融实验 | 分组柱状图 (Grouped Bar) | 显示与基线的差距 |
| 训练曲线 | 折线图 (Line Chart) | 支持平滑和最佳点标记 |
| 多指标对比 | 雷达图 (Radar Chart) | 多维度可视化 |

---

## 🎨 学术样式

预配置的论文样式：

- **IEEE** - 小字体 (8pt)，紧凑布局，适合双栏论文
- **ACM** - Linux Libertine 字体，适度留白
- **NeurIPS** - 现代简洁风格，sans-serif 字体
- **自定义** - 完全可配置的样式参数

---

## 📦 输出格式

每个图表生成：
- **PDF** - 矢量格式，无限缩放
- **PNG** - 300 DPI，快速预览

LaTeX 生成：
- 标准 `figure` 环境
- 支持 `subfigure` 多面板
- 自动数据源引用
- 跨引用标签

---

## 🔧 高级用法

### 自定义图表参数

```python
# 混淆矩阵详细配置
viz.plot_confusion_matrix(
    data,
    normalize=True,           # 显示百分比
    show_precision_recall=True,  # 添加精确率/召回率
    cmap='Blues',            # 蓝色色板
    figsize=(8, 6)
)

# 对比图添加显著性标记
viz.plot_comparison_bar(
    data,
    error_bars={'Accuracy': [0.01, 0.01, 0.02]},
    significance={('Model A', 'Model B'): '*'}
)
```

### 多面板图表

```python
manager.add_subfigure_group(
    label="fig:comprehensive",
    caption="Complete analysis",
    subfigures=[
        {"path": "acc.pdf", "subcaption": "(a) Accuracy"},
        {"path": "prec.pdf", "subcaption": "(b) Precision"},
        {"path": "rec.pdf", "subcaption": "(c) Recall"},
        {"path": "f1.pdf", "subcaption": "(d) F1 Score"}
    ],
    layout="2x2"
)
```

---

## 📝 数据结构

### 输入数据格式 (JSON)

```json
{
  "experiment_type": "confusion_matrix",
  "labels": ["Class A", "Class B", "Class C"],
  "matrix": [[95, 3, 2], [4, 91, 5], [1, 2, 97]],
  "per_class_precision": [0.95, 0.95, 0.93],
  "per_class_recall": [0.95, 0.91, 0.97]
}
```

### 生成的 LaTeX

```latex
\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/confusion_matrix.pdf}
\caption{Classification performance across all categories. 
         Based on Table~\ref{tab:results}.}
\label{fig:confusion}
\end{figure}
```

---

## 🔍 故障排除

### PDF 表格提取失败
- 确保 PDF 是文本型而非扫描版
- 尝试使用 `camelot-py` 作为备选

### 图表中文显示问题
- 在 `style_config.py` 中设置中文字体
- 或使用 LaTeX 方式渲染中文

### LaTeX 编译错误
- 确保包含所需包：`graphicx`, `caption`, `subcaption`
- 检查图片路径是否正确

---

## 📄 许可证

MIT License - 可自由使用和修改