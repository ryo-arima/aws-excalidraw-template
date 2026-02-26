# aws-excalidraw-template

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A template repository for drawing AWS architecture diagrams with [Excalidraw](https://excalidraw.com).  
Includes the official AWS Asset Package icons, ready-to-use Excalidraw templates, and an MCP (Model Context Protocol) server integration so GitHub Copilot can control the canvas directly.

## Features

| Feature | Description |
|---------|-------------|
| **MCP canvas server** | Excalidraw canvas exposed via REST API (port 3000) |
| **MCP server (VS Code)** | Control the canvas from GitHub Copilot agent mode via MCP tools |
| **Paper-size frames** | Excalidraw templates with frames sized to standard paper (A1–A5, Letter, Legal, Tabloid) |
| **AWS architecture frames** | Templates with nested AWS group frames (Account → Cloud → Region → VPC → AZ → Subnet → SG / ASG) |
| **Service catalog** | `.excalidraw` file listing all AWS icons (Architecture / Resource / Group / Category) |

## Prerequisites

- Docker / Docker Compose
- VS Code + GitHub Copilot extension
- Python 3.10+ (only required for template generation scripts)

## Directory Structure

```
.
├── docker-compose.yml              # MCP canvas server (port 3000)
├── Asset-Package/                  # Official AWS icon SVGs
│   ├── Architecture-Service-Icons/ #   Service icons (64 px)
│   ├── Resource-Icons/             #   Resource icons (48 px)
│   ├── Architecture-Group-Icons/   #   Group icons   (32 px)
│   └── Category-Icons/             #   Category icons (64 px)
├── etc/
│   ├── generate_catalog_scene.py   # Generates service-catalog.excalidraw
│   ├── generate_aws_frames.py      # Generates templates/aws-frames/*.excalidraw
│   └── service-catalog.csv         # AWS service list (reference)
└── templates/
    ├── service-catalog.excalidraw  # Pre-generated service catalog
    ├── paper-frames/               # Paper-size frame templates
    │   ├── A4-portrait.excalidraw
    │   ├── A4-landscape.excalidraw
    │   └── ...  (A1–A5, Letter, Legal, Tabloid × portrait/landscape)
    └── aws-frames/                 # AWS architecture frame templates
        ├── A4-portrait.excalidraw
        ├── A4-landscape.excalidraw
        └── ...  (same 16 paper sizes)
```

## Setup

### 1. Start the MCP canvas server

```bash
docker compose up -d
```

This starts the `mcp-excalidraw-canvas` container on port 3000.  
Open http://localhost:3000 to view and interact with the canvas in a browser.

### 2. Enable the MCP server in VS Code

`.vscode/mcp.json` is already committed.  
When you open this workspace in VS Code, the `excalidraw` MCP server is automatically recognised by GitHub Copilot.

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

> **Note**: VS Code manages the MCP client container (`mcp_excalidraw`) automatically.  
> You only need to start `mcp-excalidraw-canvas` manually (step 1).

## Templates

### Paper frames (`templates/paper-frames/`)

16 files covering 8 paper sizes × portrait/landscape.  
Each file contains a single Excalidraw `frame` element sized to the paper at 96 dpi.

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

### AWS architecture frames (`templates/aws-frames/`)

Same 16 paper sizes, each pre-populated with nested AWS group frames following the official [AWS Architecture Icons Deck for Light BG](https://aws.amazon.com/architecture/icons/) color guidelines.

Frame hierarchy and colors:

| Frame | Border color | Style |
|-------|-------------|-------|
| AWS Cloud | `#242F3E` | solid 2px |
| AWS Account | `#E7157B` | solid 2px |
| Region | `#00A4A6` | dashed 2px |
| VPC | `#8C4FFF` | solid 2px |
| Availability Zone | `#00A4A6` | dashed 1px |
| Public Subnet | `#7AA116` | solid 1px |
| Security Group | `#7D8998` | dashed 1px |
| Private Subnet | `#00A4A6` | solid 1px |
| Auto Scaling Group | `#ED7100` | dashed 2px |

To regenerate after changing the script:

```bash
python3 etc/generate_aws_frames.py
```

## Service Catalog

Scans all SVG icons under `Asset-Package/` and generates a single `.excalidraw` file.

```bash
python3 etc/generate_catalog_scene.py
```

Output: `templates/service-catalog.excalidraw`

| Directory | Size | Prefix |
|-----------|------|--------|
| `Architecture-Service-Icons/*/64/` | 64 px | `[Service]` |
| `Resource-Icons/*/` | 48 px | `[Resource]` |
| `Architecture-Group-Icons/` | 32 px | `[Group]` |
| `Category-Icons/Arch-Category_64/` | 64 px | `[Category]` |

## Using MCP Tools with GitHub Copilot

Open the Copilot chat in agent mode and describe what you want:

```
Draw a web application architecture using EC2, RDS, and S3.

Import templates/service-catalog.excalidraw onto the canvas.
```

## Network Architecture

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
