#!/usr/bin/env python3
"""
Asset-Package 配下の全 SVG アイコンを自動スキャンして
Excalidraw の image + text 要素をカテゴリ別グリッドで生成し
service-catalog.excalidraw として出力するスクリプト。

スキャン対象:
  Architecture-Service-Icons/*/64/*.svg   (サービスアイコン)
  Resource-Icons/*/48/*.svg もしくは *_48.svg (リソースアイコン)
  Architecture-Group-Icons/*.svg          (グループアイコン)
  Category-Icons/Arch-Category_64/*.svg   (カテゴリアイコン)
"""

import base64
import json
import os
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent
ASSET_DIR = BASE_DIR / "Asset-Package"
OUTPUT_FILE = BASE_DIR / "service-catalog.excalidraw"

ICON_SIZE = 48
LABEL_HEIGHT = 44       # サービス名2行分を確保
CELL_W = 270            # 横余白十分に確保
CELL_H = ICON_SIZE + LABEL_HEIGHT + 32
COLS = 4
CAT_PADDING = 90
CAT_HEADER_H = 44
START_X = 0
START_Y = 0


def svg_to_data_uri(path: Path) -> str:
    with open(path, "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


def normalize_name(filename: str) -> str:
    """SVGファイル名からサービス名を生成する。"""
    name = filename
    # プレフィックス除去
    for prefix in ("Arch_", "Res_", "Arch-Category_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    # サイズサフィックス除去 (_64, _48, _32, _16)
    for suffix in ("_64.svg", "_48.svg", "_32.svg", "_16.svg"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    else:
        name = name.removesuffix(".svg")
    # ハイフン・アンダースコアをスペースに
    name = name.replace("-", " ").replace("_", " ")
    return name


def scan_icons() -> dict[str, list[dict]]:
    """
    カテゴリ名 -> [{name, path}] の辞書を返す。
    """
    groups: dict[str, list[dict]] = {}

    # 1. Architecture-Service-Icons: */64/*.svg
    arch_svc = ASSET_DIR / "Architecture-Service-Icons"
    for cat_dir in sorted(arch_svc.iterdir()):
        if not cat_dir.is_dir():
            continue
        size_dir = cat_dir / "64"
        if not size_dir.is_dir():
            continue
        cat_name = cat_dir.name.replace("Arch_", "").replace("-", " ")
        items = []
        for svg in sorted(size_dir.glob("*.svg")):
            items.append({"name": normalize_name(svg.name), "path": svg})
        if items:
            groups[f"[Service] {cat_name}"] = items

    # 2. Resource-Icons: */  (flat _48.svg files)
    res_dir = ASSET_DIR / "Resource-Icons"
    for cat_dir in sorted(res_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_name = cat_dir.name.replace("Res_", "").replace("-", " ")
        # 直下の _48.svg OR 48/ サブディレクトリ
        svgs = sorted(cat_dir.glob("*_48.svg"))
        if not svgs:
            sub = cat_dir / "48"
            if sub.is_dir():
                svgs = sorted(sub.glob("*.svg"))
        items = [{"name": normalize_name(s.name), "path": s} for s in svgs]
        if items:
            groups[f"[Resource] {cat_name}"] = items

    # 3. Architecture-Group-Icons: flat *.svg
    grp_dir = ASSET_DIR / "Architecture-Group-Icons"
    items = []
    for svg in sorted(grp_dir.glob("*.svg")):
        items.append({"name": normalize_name(svg.name), "path": svg})
    if items:
        groups["[Group] Architecture Groups"] = items

    # 4. Category-Icons: Arch-Category_64/*.svg
    cat_icon_dir = ASSET_DIR / "Category-Icons" / "Arch-Category_64"
    if cat_icon_dir.is_dir():
        items = []
        for svg in sorted(cat_icon_dir.glob("*.svg")):
            items.append({"name": normalize_name(svg.name), "path": svg})
        if items:
            groups["[Category] AWS Categories"] = items

    return groups


def short_id():
    return uuid.uuid4().hex[:16]


# カテゴリ背景色 (fill, stroke)
CATEGORY_COLORS = {
    "Analytics":                   ("#f3e8ff", "#9c36b5"),
    "App Integration":             ("#fff0f6", "#e03131"),
    "Artificial Intelligence":     ("#e0f5f5", "#0c8599"),
    "Blockchain":                  ("#fff9db", "#e8590c"),
    "Business Applications":       ("#e8f5e9", "#2f9e44"),
    "Cloud Financial Management":  ("#e3f2fd", "#1971c2"),
    "Compute":                     ("#fff3e0", "#e8590c"),
    "Containers":                  ("#e3f2fd", "#1971c2"),
    "Customer Enablement":         ("#fce4ec", "#e03131"),
    "Database":                    ("#e3f2fd", "#1971c2"),
    "Developer Tools":             ("#f3e5f5", "#9c36b5"),
    "End User Computing":          ("#e8f5e9", "#2f9e44"),
    "Front-End Web & Mobile":      ("#fff3e0", "#e8590c"),
    "Games":                       ("#fce4ec", "#e03131"),
    "General Icons":               ("#f5f5f5", "#868e96"),
    "Internet of Things":          ("#e0f2f1", "#0c8599"),
    "Management Governance":       ("#f5f5f5", "#868e96"),
    "Media Services":              ("#fff0f6", "#e03131"),
    "Migration Modernization":     ("#e8f5e9", "#2f9e44"),
    "Networking Content Delivery": ("#e8eaf6", "#9c36b5"),
    "Quantum Technologies":        ("#e0f7fa", "#0c8599"),
    "Satellite":                   ("#e8f5e9", "#2f9e44"),
    "Security Identity Compliance":("#fce4ec", "#e03131"),
    "Storage":                     ("#e8f5e9", "#2f9e44"),
}


def cat_colors(cat_name: str):
    for key, val in CATEGORY_COLORS.items():
        if key.lower() in cat_name.lower() or cat_name.lower() in key.lower():
            return val
    return ("#f5f5f5", "#868e96")


def main():
    groups = scan_icons()
    print(f"スキャン完了: {len(groups)} カテゴリ, {sum(len(v) for v in groups.values())} アイコン")

    elements = []
    files = {}

    cur_x = START_X
    cur_y = START_Y

    for cat, services in groups.items():
        fill, stroke = cat_colors(cat)
        n_rows = (len(services) + COLS - 1) // COLS
        box_w = COLS * CELL_W + CAT_PADDING * 2
        box_h = CAT_HEADER_H + n_rows * CELL_H + CAT_PADDING * 2

        # カテゴリ背景ボックス
        elements.append({
            "type": "rectangle",
            "id": short_id(),
            "x": cur_x,
            "y": cur_y,
            "width": box_w,
            "height": box_h,
            "backgroundColor": fill,
            "strokeColor": stroke,
            "strokeWidth": 2,
            "roughness": 0,
            "opacity": 60,
            "fillStyle": "solid",
            "roundness": {"type": 3},
            "version": 1,
            "isDeleted": False,
            "groupIds": [],
            "frameId": None,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False,
        })

        # カテゴリ名テキスト
        elements.append({
            "type": "text",
            "id": short_id(),
            "x": cur_x + CAT_PADDING,
            "y": cur_y + 8,
            "width": box_w - CAT_PADDING * 2,
            "height": CAT_HEADER_H - 8,
            "text": cat,
            "fontSize": 16,
            "fontFamily": 2,
            "textAlign": "left",
            "verticalAlign": "top",
            "strokeColor": stroke,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "version": 1,
            "isDeleted": False,
            "groupIds": [],
            "frameId": None,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False,
            "containerId": None,
            "lineHeight": 1.25,
        })

        # サービスアイコン + ラベル
        for i, svc in enumerate(services):
            col = i % COLS
            row_i = i // COLS
            ix = cur_x + CAT_PADDING + col * CELL_W + (CELL_W - ICON_SIZE) // 2
            iy = cur_y + CAT_HEADER_H + CAT_PADDING + row_i * CELL_H

            data_url = svg_to_data_uri(svc["path"])
            if data_url:
                file_id = short_id()
                files[file_id] = {
                    "mimeType": "image/svg+xml",
                    "id": file_id,
                    "dataURL": data_url,
                    "created": 1,
                }
                elements.append({
                    "type": "image",
                    "id": short_id(),
                    "x": ix,
                    "y": iy,
                    "width": ICON_SIZE,
                    "height": ICON_SIZE,
                    "fileId": file_id,
                    "status": "saved",
                    "scale": [1, 1],
                    "roughness": 0,
                    "opacity": 100,
                    "strokeColor": "transparent",
                    "backgroundColor": "transparent",
                    "fillStyle": "solid",
                    "strokeWidth": 1,
                    "version": 1,
                    "isDeleted": False,
                    "groupIds": [],
                    "frameId": None,
                    "boundElements": [],
                    "updated": 1,
                    "link": None,
                    "locked": False,
                })

            # サービス名ラベル
            elements.append({
                "type": "text",
                "id": short_id(),
                "x": cur_x + CAT_PADDING + col * CELL_W,
                "y": iy + ICON_SIZE + 4,
                "width": CELL_W,
                "height": LABEL_HEIGHT,
                "text": svc["name"],
                "fontSize": 11,
                "fontFamily": 2,
                "textAlign": "center",
                "verticalAlign": "top",
                "strokeColor": "#1e1e1e",
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "roughness": 0,
                "opacity": 100,
                "version": 1,
                "isDeleted": False,
                "groupIds": [],
                "frameId": None,
                "boundElements": [],
                "updated": 1,
                "link": None,
                "locked": False,
                "containerId": None,
                "lineHeight": 1.25,
            })

        cur_y += box_h + 40

    scene = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": files,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(scene, f, ensure_ascii=False)

    print(f"完了: {len(elements)} 要素, {len(files)} 画像ファイル")
    print(f"出力: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
