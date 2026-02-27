# Command Specification

CLI binary: **`aet`** (AWS Excalidraw Template)  
Build: `go build -o .bin/aet ./cmd`

---

## Command Tree

```
aet
├── generate
│   ├── frames    Copy AWS frame templates to output directory
│   └── catalog   Copy service-catalog template to output path
├── list
│   └── services  List available AWS service icons
└── add
    └── service   Add AWS service icon(s) to a .excalidraw file
```

---

## aet generate frames

Copy `.excalidraw` files from `templates/aws-frames/<variant>/` to an output directory.

```
aet generate frames [flags]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--variant` | `1cloud-1account-1region-2az-3subnet` | Layout variant name |
| `--size` | *(all)* | Filter by paper size prefix (e.g. `A4`) |
| `--output`, `-o` | `output/aws-frames/` | Output directory |
| `--list-variants` | — | Print all available variants and exit |

### Variant naming

```
<N>cloud-<N>account-<N>region-<N>az-<N>subnet[-staggered]
```

| Dimension | Values | Notes |
|-----------|--------|-------|
| cloud | 1–3 | Number of AWS Cloud boxes |
| account | 1–3 | Number of AWS Account boxes |
| region | 1–3 | Number of Region boxes |
| az | 1–4 | Number of AZs per Region |
| subnet | 2, 3, 4 | Subnet layers per AZ |
| staggered | optional suffix | Overlapping AZ depth layout (requires az ≥ 2) |

**Subnet layers:**

| Count | Layers |
|-------|--------|
| `2subnet` | Public + Private |
| `3subnet` | Public + Private 1 + Private 2 |
| `4subnet` | Public + Private 1 + Private 2 + Private 3 |

**AZ layout:**
- `grid` (default) — AZs arranged in a flat grid, uniform fill
- `staggered` — AZs overlap to show depth; AZ[0] = white (`#ffffff`), AZ[1] = light teal (`#c8e8e8`), AZ[2] = darker teal (`#92cecd`)

### Examples

```bash
aet generate frames                                                               # default: 3-subnet, 2 AZs
aet generate frames --variant 1cloud-1account-1region-2az-2subnet                # simpler layout
aet generate frames --variant 1cloud-1account-1region-2az-3subnet-staggered      # staggered depth
aet generate frames --variant 2cloud-3account-2region-3az-4subnet                # complex multi-account
aet generate frames --size A4 --output output/samples/web3tier/                  # A4 only
aet generate frames --list-variants                                               # show all 180+ variants
```

---

## aet generate catalog

Copy `templates/service-catalog.excalidraw` to an output path.

```
aet generate catalog [flags]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output`, `-o` | `output/service-catalog.excalidraw` | Output file path |

```bash
aet generate catalog
aet generate catalog --output /tmp/catalog.excalidraw
```

---

## aet list services

Read `etc/resources/service-catalog.csv` and print service names with categories.

```
aet list services [flags]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--category` | *(all)* | Filter by category (case-insensitive exact match) |
| `--query`, `-q` | *(all)* | Filter by service name substring (case-insensitive) |

```bash
aet list services                          # all services
aet list services --category Compute
aet list services --query lambda
aet list services -q "load balancing"
```

Output format: `<Category padded 40 chars>  <ServiceName>`

---

## aet add service

Search `Architecture-Service-Icons/` for icons and append them to a `.excalidraw` file.

```
aet add service [flags]
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--file` | `-f` | `output/aws-frames/A4-landscape.excalidraw` | Target `.excalidraw` file (read + written in-place) |
| `--name` | `-n` | — | Service name (single-add mode) |
| `--list` | `-l` | — | Path to a CSV/TXT service list (batch mode) |
| `--category` | — | *(auto)* | Narrow icon search to a specific category |
| `--size` | — | `64` | Icon size: `16 \| 32 \| 48 \| 64` |
| `--no-legend` | — | `false` | Omit legend entry |

### Placement rules

- **Icon** — placed outside-bottom of the frame, left-to-right
- **Label** — centered below icon, abbreviated (`Amazon `/ `AWS ` prefix stripped)
- **Legend** — placed outside the frame
  - `--list` (batch) mode → stacked on the **right** side
  - `--name` (single) mode → stacked on the **left** side

### Service list CSV format (`--list`)

```csv
# コメント行 (# で始まる行はスキップ)
正式名称,略語,サービス概要,用途,備考
Amazon EC2,EC2,Virtual servers in the cloud,Web tier,
Amazon RDS,RDS,Managed relational database,DB tier,
```

または ID 付きフォーマット（`service-catalog.csv` の行番号）:

```csv
id,正式名称,略語,サービス概要,用途,備考
42,Amazon EC2,EC2,Virtual servers,Web tier,
```

`id` 列が整数の場合、`service-catalog.csv` の直接ルックアップを使用（高速・確実）。

### Examples

```bash
aet add service --name "Amazon EC2" --file output/my.excalidraw
aet add service --name "Amazon RDS" --category Arch_Database --file output/my.excalidraw
aet add service --list services.csv --file output/my.excalidraw
aet add service --list services.csv --file output/my.excalidraw --no-legend
```

---

## Frame Hierarchy & Colors

Generated by `python3 etc/generate_aws_frames.py` → `templates/aws-frames/<variant>/`

```
AWS Cloud           stroke=#242F3E  solid 2px    fill=#F1F3F6
  └─ AWS Account    stroke=#E7157B  solid 2px    fill=#F8D7EB
       └─ Region    stroke=#00A4A6  dashed 2px   fill=#E6F7F8
            └─ VPC  stroke=#8C4FFF  solid 2px    fill=#EDE9FF
                 └─ AZ [×N]  stroke=#00A4A6  dashed 1px
                      │  grid: uniform fill
                      │  staggered: AZ[0]=#ffffff  AZ[1]=#c8e8e8  AZ[2+]=#92cecd
                      ├─ Public Subnet   stroke=#7AA116  solid 1px   fill=#F2F8E6
                      │    └─ Security Group  stroke=#9B0000  dashed 1px  (always present)
                      ├─ Private Subnet 1  stroke=#00A4A6  solid 1px   fill=#E6F7F8
                      │    └─ Security Group  stroke=#9B0000  dashed 1px
                      └─ Private Subnet 2  (3subnet/4subnet のみ)
                           └─ Security Group  stroke=#9B0000  dashed 1px
```

Icon + label: top-left corner of each frame, icon 32×32 px, font 12 px.

---

## Python Scripts

| Script | Command | Output |
|--------|---------|--------|
| `etc/generate_aws_frames.py` | `python3 etc/generate_aws_frames.py` | `templates/aws-frames/<variant>/*.excalidraw` (2880 files = 180 variants × 16 sizes) |
| `etc/generate_catalog_scene.py` | `python3 etc/generate_catalog_scene.py` | `templates/service-catalog.excalidraw` |

### Paper sizes (96 dpi)

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
