# Lark / Feishu Skills

A collection of OpenClaw skills for integrating with **Feishu** (Lark) — the enterprise collaboration platform.

These skills enable AI agents to interact with Feishu documents, calendars, tasks, tables, and messaging services through structured tool definitions.

---

## 📋 Available Skills

| Skill | Capability |
|-------|-----------|
| `feishu-bitable` | Smart table (多维表格) — records, fields, views, and batch operations |
| `feishu-calendar` | Calendar events, scheduling, attendee management, free/busy queries |
| `feishu-channel-rules` | Channel and group management rules |
| `feishu-create-doc` | Create cloud documents from Lark-flavored Markdown |
| `feishu-fetch-doc` | Retrieve and read document content |
| `feishu-im-read` | Read instant messages and chat history |
| `feishu-task` | Task and to-do list creation, assignment, and tracking |
| `feishu-troubleshoot` | Diagnostic guides and common issue resolution |
| `feishu-update-doc` | Update existing documents with new content |

---

## 🚀 Quick Start

Each skill is self-contained:

- `SKILL.md` — Tool schema, parameters, constraints, and usage examples
- `references/` — Supplementary docs (field properties, syntax guides, etc.)

To use a skill, point your OpenClaw agent configuration at the skill directory:

```
lark/skills/<skill-name>/
```

The framework will automatically load the `SKILL.md` definition.

---

## 🔑 Common Conventions

Most Feishu skills share these patterns:

- **User IDs**: Use `ou_...` (open_id) format, obtained from message `SenderId`
- **Time format**: ISO 8601 / RFC 3339 with timezone — e.g. `2026-02-25T14:00:00+08:00`
- **Timezone**: Fixed to `Asia/Shanghai` (UTC+8)
- **Group IDs**: `oc_...` format
- **Meeting room IDs**: `omm_...` format

See individual `SKILL.md` files for specific constraints and error handling.

---

## 📦 Prerequisites

- A Feishu/Lark app with appropriate API permissions
- `app_id` and `app_secret` for authentication
- Required scopes vary by skill (see each `SKILL.md`)
