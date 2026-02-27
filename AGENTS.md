# AGENTS.md

このファイルは、Codex/AI エージェントが `aws-excalidraw-template` を安全かつ一貫して扱うための実行ガイドです。

## 1) プロジェクト概要

- 目的: AWS アーキテクチャ図を Excalidraw 形式 (`.excalidraw`) で生成・編集する
- 主な手段は 2 つ:
  - Python スクリプト生成（主系）
  - Go 製 CLI `aet`（テンプレートコピー・サービス追加）
- 主要アセット: `Asset-Package/`（公式 AWS SVG）

## 2) 前提条件

- 必須（主系）: Python 3.10+
- CLI 利用時: Go 1.21+
- MCP ライブキャンバス利用時（任意）:
  - Docker / Docker Compose
  - VS Code + GitHub Copilot

## 3) 重要ディレクトリ

- `etc/`
  - `generate_aws_frames.py`: AWS フレームテンプレート生成
  - `generate_catalog_scene.py`: サービスカタログ生成
  - `excalidraw_helpers.py`: 共通ヘルパー
  - `resources/service-catalog.csv`: サービス定義データ
- `templates/`
  - `aws-frames/<variant>/`: 生成済み AWS フレーム
  - `paper-frames/`: 用紙フレーム
  - `service-catalog.excalidraw`
- `pkg/`, `cmd/`: `aet` CLI 実装
- `doc/COMMAND_SPEC.md`: CLI 仕様（一次参照）

## 4) エージェントの基本方針

- 変更は **最小差分** で実施する
- 仕様変更時は関連ドキュメント（最低 `README.md` と `doc/COMMAND_SPEC.md`）を更新する
- 生成物を直接手編集しない（可能な限りスクリプト/CLIで再生成）
- 既存の命名規則・色・階層を壊さない

## 5) 標準ワークフロー

### 5.1 Python でテンプレート再生成

```bash
python3 etc/generate_aws_frames.py
python3 etc/generate_catalog_scene.py
```

### 5.2 CLI ビルドと主要コマンド

```bash
go build -o .bin/aet ./cmd

# フレーム生成
.bin/aet generate frames --size A4 --output output/samples/web3tier/

# バリアント一覧
.bin/aet generate frames --list-variants

# サービス一覧
.bin/aet list services --query ec2

# サービス追加
.bin/aet add service --name "Amazon EC2" --file output/samples/web3tier/A4-portrait.excalidraw
```

## 6) CLI 仕様の要点（抜粋）

- デフォルト variant:
  - `1cloud-1account-1region-2az-3subnet`
- variant 命名規則:
  - `<N>cloud-<N>account-<N>region-<N>az-<N>subnet[-staggered]`
- subnet は `2|3|4`
- `-staggered` は AZ 重なり表示（AZ >= 2 想定）

詳細は必ず `doc/COMMAND_SPEC.md` を優先参照すること。

## 7) レイアウト/デザイン不変条件

- フレーム階層:
  - Cloud → Account → Region → VPC → AZ → Subnets
- Security Group 色:
  - 枠線 `#9B0000`（crimson系）
- スタッガード AZ 塗り:
  - AZ[0] `#ffffff`
  - AZ[1] `#c8e8e8`
  - AZ[2+] `#92cecd`

## 8) 変更時の確認チェックリスト

1. Python 構文確認:

```bash
python3 -m py_compile etc/generate_aws_frames.py
```

2. Go ビルド確認:

```bash
go build -o .bin/aet ./cmd
```

3. 代表コマンド動作確認:

```bash
.bin/aet generate frames --size A4 --output output/samples/web3tier/
.bin/aet list services --query route
```

4. ドキュメント整合確認:
- `README.md`
- `doc/COMMAND_SPEC.md`

## 9) ドキュメント更新ルール

- コマンド引数やデフォルト値を変更したら:
  - `pkg/controller/*.go`
  - `doc/COMMAND_SPEC.md`
  - `README.md`
  を同一 PR / 同一変更で揃える
- 仕様の正本は `doc/COMMAND_SPEC.md`
- README は「導入 + クイックスタート」に集中し、詳細は COMMAND_SPEC へリンクする

## 10) NG パターン

- `templates/*.excalidraw` を手編集だけで直す（再現性がない）
- variant 命名規則を README / COMMAND_SPEC / 実装で不一致にする
- 検証なしで `aet` のフラグ仕様を変更する

---

必要に応じてこの AGENTS.md を拡張するが、冗長化を避け、実行可能な手順を優先すること。
