# aws-excalidraw-template

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A template repository for drawing AWS architecture diagrams with [Excalidraw](https://excalidraw.com).  
Includes the official AWS Asset Package icons, ready-to-use Excalidraw templates, and two ways to create diagrams.

## Features

| Feature | Description |
|---------|-------------|
| **Script-based generation** | Any agent writes a Python script and runs it to produce a `.excalidraw` file — no Docker, no VS Code required |
| **`aet` CLI** | Go binary: copy frame templates, list service icons, add icons to diagrams |
| **Paper-size frames** | Excalidraw templates sized to standard paper (A1–A5, Letter, Legal, Tabloid × portrait/landscape) |
| **AWS architecture frames** | 180+ variants with pre-built nested group frames (Cloud → Account → Region → VPC → AZ → Subnets) |
| **Service catalog** | `.excalidraw` file listing all AWS icons (Architecture / Resource / Group / Category) |
| **MCP live canvas** | Optional: control a live Excalidraw canvas from GitHub Copilot via MCP tools |

## Prerequisites

### Script-based diagram generation *(no extra setup)*
- **Python 3.10+** — standard library only, no third-party packages needed

### `aet` CLI *(optional)*
- **Go 1.21+** — `go build -o .bin/aet ./cmd`

### MCP live canvas *(optional)*
- Docker / Docker Compose
- VS Code + GitHub Copilot extension

## Directory Structure

```
.
├── docker-compose.yml              # MCP canvas server (port 3000)
├── doc/
│   └── COMMAND_SPEC.md             # Full CLI command reference
├── Asset-Package/                  # Official AWS icon SVGs
│   ├── Architecture-Service-Icons/ #   Service icons (16/32/48/64 px per category)
│   ├── Resource-Icons/             #   Resource icons (48 px per category)
│   ├── Architecture-Group-Icons/   #   Group icons   (32 px)
│   └── Category-Icons/             #   Category icons (64 px)
├── etc/
│   ├── generate_aws_frames.py      # Generates templates/aws-frames/**/*.excalidraw
│   ├── generate_catalog_scene.py   # Generates templates/service-catalog.excalidraw
│   ├── excalidraw_helpers.py       # Shared Python helpers (make_rect, make_text, …)
│   └── resources/
│       └── service-catalog.csv    # AWS service list (name, category, SVG path, base64)
├── pkg/                            # Go source (controller / repository / entity)
├── cmd/                            # Go CLI entry point
├── output/                         # Generated diagram output (git-ignored)
├── templates/
│   ├── service-catalog.excalidraw  # Pre-generated service catalog
│   ├── paper-frames/               # Paper-size frame templates (16 files)
│   │   ├── A4-portrait.excalidraw
│   │   └── ...  (A1–A5, Letter, Legal, Tabloid × portrait/landscape)
│   └── aws-frames/                 # AWS architecture frame templates
│       ├── 1cloud-1account-1region-2az-3subnet/    # default variant
│       │   ├── A4-portrait.excalidraw
│       │   └── ...  (16 paper sizes)
│       ├── 1cloud-1account-1region-2az-3subnet-staggered/
│       └── ...  (180+ variants total)
└── README.md
```

---

## `aet` CLI Quick Reference

> Full specification: [doc/COMMAND_SPEC.md](doc/COMMAND_SPEC.md)
> Agent playbook: [AGENTS.md](AGENTS.md)

```bash
# Build
go build -o .bin/aet ./cmd

# Copy frame templates (default: 3-subnet, 2 AZs)
aet generate frames --size A4 --output output/my-diagram/

# List all layout variants
aet generate frames --list-variants

# Copy service catalog
aet generate catalog

# List available service icons
aet list services --category Compute
aet list services --query "load balancing"

# Add icons to a diagram (single)
aet add service --name "Amazon EC2" --file output/my-diagram/A4-portrait.excalidraw

# Add icons from a CSV list (batch)
aet add service --list services.csv --file output/my-diagram/A4-portrait.excalidraw
```

### Variant naming

```
<N>cloud-<N>account-<N>region-<N>az-<N>subnet[-staggered]
```

| Suffix | Subnet layers |
|--------|---------------|
| `2subnet` | Public + Private |
| `3subnet` | Public + Private 1 + Private 2 *(default)* |
| `4subnet` | Public + Private 1 + Private 2 + Private 3 |

AZ layout: `grid` (default flat layout) or `staggered` (overlapping depth effect, AZ ≥ 2).

## Script-Based Diagram Generation

Any agent (GitHub Copilot, Claude, Cursor, CI, etc.) can generate architecture diagrams by writing a Python script and running it. No Docker or VS Code needed.

### Workflow

```bash
# 1. Write a generation script  →  etc/my_diagram.py
# 2. Run it
python3 etc/my_diagram.py
# 3. Open output in Excalidraw (https://excalidraw.com or VS Code extension)
```

### Script template

```python
#!/usr/bin/env python3
import json, os, base64, hashlib

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
GROUP_ICONS = os.path.join(BASE_DIR, "..", "Asset-Package", "Architecture-Group-Icons")
SVC_ICONS   = os.path.join(BASE_DIR, "..", "Asset-Package", "Architecture-Service-Icons")
OUT_DIR     = os.path.join(BASE_DIR, "..", "output")

W, H = 794, 1122   # A4 portrait @ 96 dpi (see paper sizes table below)
SEED = 1000

# --- helpers (copy from generate_aws_frames.py or implement inline) ---
# make_rect / make_text / make_image / make_frame / make_arrow / ensure_icon

elements, files = [], {}
# ... build elements ...

os.makedirs(OUT_DIR, exist_ok=True)
scene = dict(type="excalidraw", version=2,
             source="https://excalidraw.com",
             elements=elements,
             appState={"gridSize": None, "viewBackgroundColor": "#ffffff"},
             files=files)
with open(os.path.join(OUT_DIR, "my-diagram-a4-portrait.excalidraw"), "w") as f:
    json.dump(scene, f, ensure_ascii=False, indent=2)
```

### Element builder reference

| Function signature | Description |
|-------------------|-------------|
| `make_rect(id, x, y, w, h, stroke, stroke_style, fill, stroke_width)` | Rectangle / group border. `roundness=None` (sharp corners) |
| `make_text(id, x, y, w, h, text, font_size=12, color, bold)` | Text label — Helvetica, 12 px |
| `make_image(id, x, y, w, h, file_id)` | SVG icon (register first with `ensure_icon`) |
| `make_arrow(id, x1, y1, x2, y2)` | Directed arrow |
| `make_frame(id, x, y, w, h, name)` | Named Excalidraw frame |
| `ensure_icon(svg_path, files_dict)` | Base64-encode SVG, register in files dict, return `file_id` |

Key conventions:
- `roundness=None` — sharp corners on all rectangles
- Group icons: **32 × 32 px** (from `Architecture-Group-Icons/*.svg`)
- Service icons: display at **48 × 48 px**, use the 64 px SVG files
- Font size: **12 px** for all labels

### Icon paths

```
# Service icons
Asset-Package/Architecture-Service-Icons/{Category}/64/{Name}_64.svg

# Group icons
Asset-Package/Architecture-Group-Icons/{Name}_32.svg
```

Common service icon categories: `Arch_Compute`, `Arch_Database`, `Arch_Storage`,
`Arch_Containers`, `Arch_Networking-Content-Delivery`, `Arch_Management-Governance`,
`Arch_Security-Identity-Compliance`, `Arch_App-Integration`

### Paper sizes @ 96 dpi

| Size | Portrait (px) | Landscape (px) |
|------|--------------|----------------|
| A5   | 559 × 794    | 794 × 559      |
| A4   | 794 × 1122   | 1122 × 794     |
| A3   | 1122 × 1587  | 1587 × 1122    |
| A2   | 1587 × 2245  | 2245 × 1587    |
| A1   | 2245 × 3179  | 3179 × 2245    |
| Letter  | 816 × 1056  | 1056 × 816  |
| Legal   | 816 × 1344  | 1344 × 816  |
| Tabloid | 1056 × 1632 | 1632 × 1056 |

---

## Templates

### Paper frames (`templates/paper-frames/`)

16 files — 8 paper sizes × portrait/landscape.  
Each contains a single Excalidraw `frame` element at the exact paper size.

### AWS architecture frames (`templates/aws-frames/`)

180+ variants, each containing 16 paper sizes.  
Colors follow the official [AWS Architecture Icons Deck for Light BG](https://aws.amazon.com/architecture/icons/).

```
AWS Cloud           #242F3E  solid 2px
  └─ AWS Account    #E7157B  solid 2px
       └─ Region    #00A4A6  dashed 2px
            └─ VPC  #8C4FFF  solid 2px
                 └─ AZ [×N]  #00A4A6  dashed 1px
                      ├─ Public Subnet     #7AA116  solid 1px
                      │    └─ Security Group  #9B0000  dashed 1px
                      ├─ Private Subnet 1  #00A4A6  solid 1px
                      │    └─ Security Group  #9B0000  dashed 1px
                      └─ Private Subnet 2  (3subnet / 4subnet)
                           └─ Security Group  #9B0000  dashed 1px
```

Regenerate:

```bash
python3 etc/generate_aws_frames.py
# → templates/aws-frames/<variant>/*.excalidraw
# → 180 variants × 16 paper sizes = 2,880 files
```

## Service Catalog

```bash
python3 etc/generate_catalog_scene.py
# → templates/service-catalog.excalidraw
```

| Directory | Size | Prefix |
|-----------|------|--------|
| `Architecture-Service-Icons/*/64/` | 64 px | `[Service]` |
| `Resource-Icons/*/` | 48 px | `[Resource]` |
| `Architecture-Group-Icons/` | 32 px | `[Group]` |
| `Category-Icons/Arch-Category_64/` | 64 px | `[Category]` |

---

## MCP Live Canvas Setup

> Only needed for interactive editing via GitHub Copilot. Skip this if using script-based generation.

### 1. Start the canvas server

```bash
docker compose up -d
```

- Container: `mcp-excalidraw-canvas` · Port: `3000`
- Browser: http://localhost:3000

### 2. VS Code MCP configuration

`.vscode/mcp.json` is already committed — VS Code recognises the `excalidraw` MCP server automatically.

```json
{
  "servers": {
    "excalidraw": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--network", "mcp-net",
        "-e", "EXPRESS_SERVER_URL=http://mcp-excalidraw-canvas:3000",
        "-e", "ENABLE_CANVAS_SYNC=true",
        "ghcr.io/yctimlin/mcp_excalidraw:latest"
      ]
    }
  }
}
```

> VS Code manages the `mcp_excalidraw` client container automatically. You only start `mcp-excalidraw-canvas` manually (step 1).

### Network architecture

```
[You]
  docker compose up -d
    └─ mcp-excalidraw-canvas  (ghcr.io/yctimlin/mcp_excalidraw-canvas)
         port 3000:3000  |  network: mcp-net
         browser: http://localhost:3000

[VS Code manages automatically]
  GitHub Copilot (MCP client)
    │  stdio
    ▼
  ghcr.io/yctimlin/mcp_excalidraw   [--network mcp-net, --rm]
    │  HTTP
    ▼
  mcp-excalidraw-canvas  [mcp-net]
