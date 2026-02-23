# aws-excalidraw-template

AWS アーキテクチャ図を Excalidraw で描くためのテンプレートリポジトリです。  
AWS 公式アイコン（Asset-Package）を含むサービスカタログと、MCP (Model Context Protocol) 経由で GitHub Copilot から Excalidraw キャンバスを操作できる環境を提供します。

## 概要

| 機能 | 説明 |
|------|------|
| **Excalidraw アプリ** | セルフホスト版 Excalidraw（ポート 3030）|
| **MCP キャンバスサーバー** | Excalidraw キャンバスを REST API で操作（ポート 3000）|
| **MCP サーバー** | VS Code Copilot から MCP ツール経由でキャンバスを制御 |
| **サービスカタログ** | AWS 全アイコン（Architecture / Resource / Group / Category）を一覧表示する `.excalidraw` ファイル |

## 前提条件

- Docker / Docker Compose
- VS Code + GitHub Copilot 拡張機能
- Python 3.10 以上（カタログ生成スクリプト実行時）

## ディレクトリ構成

```
.
├── docker-compose.yml          # MCP キャンバスサーバー (port 3000)
├── excalidraw/
│   ├── docker-compose.yml      # Excalidraw アプリ (port 3030)
│   └── Dockerfile              # Node 20 ベース
├── Asset-Package/              # AWS 公式アイコン SVG
│   ├── Architecture-Service-Icons/   # サービスアイコン（64px）
│   ├── Resource-Icons/               # リソースアイコン（48px）
│   ├── Architecture-Group-Icons/     # グループアイコン（32px）
│   └── Category-Icons/               # カテゴリアイコン（64px）
├── generate_catalog_scene.py   # カタログ .excalidraw 生成スクリプト
├── service-catalog.csv         # サービス一覧 CSV（参照用）
├── service-catalog.excalidraw  # 生成済みサービスカタログ（要インポート）
├── template.excalidraw         # 空のテンプレートファイル
└── .vscode/
    └── mcp.json                # VS Code MCP サーバー定義
```

## セットアップ

### 1. MCP キャンバスサーバーを起動

```bash
docker compose up -d
```

`mcp-net` という Docker ネットワーク上に `mcp-excalidraw-canvas` コンテナが起動します。

### 2. Excalidraw アプリを起動（任意）

```bash
cd excalidraw
docker compose up -d
```

http://localhost:3030 でセルフホスト版 Excalidraw にアクセスできます。

### 3. VS Code で MCP サーバーを有効化

`.vscode/mcp.json` が配置済みのため、VS Code を開くと自動的に MCP サーバー（`excalidraw`）が認識されます。  
GitHub Copilot のエージェントモードから Excalidraw キャンバスへの操作が可能になります。

キャンバスの確認は http://localhost:3000 で行えます。

## サービスカタログの生成

`Asset-Package` 配下の全 SVG アイコンをスキャンして `.excalidraw` ファイルを生成します。

```bash
python3 generate_catalog_scene.py
```

出力: `service-catalog.excalidraw`

生成後、MCP ツールまたは Excalidraw の「Open」からファイルをインポートしてください。

### スキャン対象

| ディレクトリ | サイズ | カテゴリプレフィックス |
|---|---|---|
| `Architecture-Service-Icons/*/64/` | 64px | `[Service]` |
| `Resource-Icons/*/` | 48px | `[Resource]` |
| `Architecture-Group-Icons/` | 32px | `[Group]` |
| `Category-Icons/Arch-Category_64/` | 64px | `[Category]` |

## MCP ツールの使い方（GitHub Copilot）

VS Code の Copilot チャット（エージェントモード）で以下のような操作が可能です。

```
# キャンバスにAWSアーキテクチャ図を描く
EC2とRDSとS3を使ったWebアプリのアーキテクチャ図を描いてください

# サービスカタログをインポート
service-catalog.excalidraw をキャンバスにインポートしてください
```

## ネットワーク構成

```
VS Code (MCP クライアント)
  ↓ stdio
ghcr.io/yctimlin/mcp_excalidraw  [--network mcp-net]
  ↓ HTTP (http://mcp-excalidraw-canvas:3000)
mcp-excalidraw-canvas [mcp-net]  ← ブラウザ: http://localhost:3000
```
# aws-excalidraw-template
