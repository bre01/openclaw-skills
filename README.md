# OpenClaw Skills

A curated collection of **OpenClaw Skills** for automation and productivity. These skills are designed to extend AI agent capabilities across enterprise collaboration (Feishu/Lark) and academic research workflows.

---

## 📁 Repository Structure

```
openclaw-skills/
├── lark/                           # Feishu/Lark enterprise skills
│   └── skills/
│       ├── feishu-bitable/         # Bitable (smart table) operations
│       ├── feishu-calendar/        # Calendar & scheduling
│       ├── feishu-channel-rules/   # Channel/group rules
│       ├── feishu-create-doc/      # Create cloud documents
│       ├── feishu-fetch-doc/       # Fetch document content
│       ├── feishu-im-read/         # Instant message reading
│       ├── feishu-task/            # Task management
│       ├── feishu-troubleshoot/    # Troubleshooting guides
│       └── feishu-update-doc/      # Update existing documents
│
└── workspace/                      # Research & academic skills
    └── skills/
        ├── paper-experiment-extractor/   # Extract experiment data from PDFs
        ├── experiment-visualizer/        # Generate publication-ready figures
        ├── latex-figure-integrator/      # Integrate figures into LaTeX
        └── complete_pipeline.py          # End-to-end pipeline demo
```

---

## 🚀 Skill Categories

### 1. Feishu/Lark Enterprise Skills (`lark/skills/`)

Skills for integrating with Feishu (Lark) enterprise platform. Each skill provides structured tool definitions and usage patterns for the OpenClaw agent framework.

| Skill | Description |
|-------|-------------|
| `feishu-calendar` | Calendar event management, attendee coordination, free/busy queries |
| `feishu-create-doc` | Create cloud documents from Lark-flavored Markdown |
| `feishu-update-doc` | Update existing documents with new content |
| `feishu-fetch-doc` | Retrieve document content for analysis or summarization |
| `feishu-im-read` | Read and process instant message content |
| `feishu-bitable` | Smart table operations — records, fields, and views |
| `feishu-task` | Task creation, assignment, and tracking |
| `feishu-channel-rules` | Channel and group management rules |
| `feishu-troubleshoot` | Diagnostic guides and common issue resolution |

### 2. Research & Academic Skills (`workspace/skills/`)

A coordinated skill suite for automating the paper writing workflow — from experiment extraction to publication-ready figures.

| Skill | Description |
|-------|-------------|
| `paper-experiment-extractor` | Extract tables, metrics, and results from academic PDFs |
| `experiment-visualizer` | Generate IEEE/ACM/NeurIPS-styled charts and plots |
| `latex-figure-integrator` | Auto-generate LaTeX figure environments with smart captions |

**Pipeline Overview:**

```
PDF Paper → [Extractor] → Structured Data → [Visualizer] → Figures → [Integrator] → LaTeX
```

Run the complete pipeline:

```bash
python workspace/skills/complete_pipeline.py paper.pdf -o output/
```

---

## 🛠️ Using a Skill

Each skill is self-contained with:

- `SKILL.md` — Tool definitions, parameters, constraints, and usage examples
- `scripts/` — Reference implementation (for workspace skills)
- `references/` — Supplementary documentation (for lark skills)

To use a skill in your OpenClaw agent configuration, reference the skill directory path and the framework will load the `SKILL.md` definition.

---

## 📦 Requirements

**Lark skills:**
- Feishu/Lark app credentials (app_id / app_secret)
- Appropriate permissions scopes for each API

**Workspace skills:**

```bash
pip install pdfplumber pymupdf pandas numpy matplotlib seaborn
```

---

## 📄 License

MIT License — free to use and modify.
