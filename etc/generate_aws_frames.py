#!/usr/bin/env python3
"""
Generate aws-frames Excalidraw templates.

Colors follow the official AWS Architecture Icons Deck for Light BG
(extracted from awslabs/diagram-as-code make-definition-from-pptx-reimp.go):

  AWS Cloud outer   border #000000 solid 2px
  Region            border #00A4A6 dashed 2px
  AZ                border #00A4A6 dashed 1px
  VPC               border #693BC5 solid 2px
  Public Subnet     border #7AA116 solid 1px
  Private Subnet    border #00A4A6 solid 1px
  Security Group    border #7D8998 dashed 1px  (Generic group)
  AWS Account       border #E7157B solid 2px
  Auto Scaling Grp  border #ED7100 dashed 2px

Layout rule: icon + label are placed INSIDE the top-left of each frame.

Variants generated (all combinations × all paper sizes):
  n_clouds:   1, 2
  n_accounts: 1, 2, 3
  n_regions:  1, 2
  n_azs:      1, 2, 3
  Total: 2×3×2×3 = 36 layout variants × 16 paper orientations = 576 files

Directory structure:
  templates/aws-frames/
    base/                            ← original 16 files (moved here)
    1cloud-1account-1region-1az/
    1cloud-1account-1region-2az/     ← equivalent to base
    ...
    2cloud-3account-2region-3az/
"""
import csv as _csv
import json
import os
import shutil
import base64
import hashlib
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "resources", "Asset-Package", "Architecture-Group-Icons")
OUT_DIR  = os.path.join(BASE_DIR, "..", "templates", "aws-frames")

# ── service-catalog.csv 生成用定数 ────────────────────────────────────────────
CSV_OUT   = os.path.join(BASE_DIR, "resources", "service-catalog.csv")
ASSET_DIR = os.path.join(BASE_DIR, "resources", "Asset-Package")

# Paper sizes: portrait (w, h) @ 96 dpi
PAPER_SIZES = {
    "A5":      (559,  794),
    "A4":      (794,  1122),
    "A3":      (1122, 1587),
    "A2":      (1587, 2245),
    "A1":      (2245, 3179),
    "Letter":  (816,  1056),
    "Legal":   (816,  1344),
    "Tabloid": (1056, 1632),
}

# ── Official color / style spec (border colors matched to actual SVG icon colors)
# AWS-Cloud-logo_32.svg / AWS-Cloud_32.svg : #242F3E
# Region_32.svg                            : #00A4A6
# Virtual-private-cloud-VPC_32.svg         : #8C4FFF
# Public-subnet_32.svg                     : #7AA116
# Private-subnet_32.svg                    : #00A4A6
STYLE = {
    "cloud":   dict(stroke="#242F3E", stroke_style="solid",  stroke_width=2, fill="transparent"),
    "region":  dict(stroke="#00A4A6", stroke_style="dashed", stroke_width=2, fill="transparent", label_color="#00A4A6"),
    "az":      dict(stroke="#00A4A6", stroke_style="dashed", stroke_width=1, fill="transparent", label_color="#00A4A6"),
    "vpc":     dict(stroke="#8C4FFF", stroke_style="solid",  stroke_width=2, fill="transparent", label_color="#8C4FFF"),
    "pub_sub": dict(stroke="#7AA116", stroke_style="solid",  stroke_width=1, fill="transparent", label_color="#7AA116"),
    "priv_sub":dict(stroke="#00A4A6", stroke_style="solid",  stroke_width=1, fill="transparent", label_color="#00A4A6"),
    "sg":      dict(stroke="#9B0000", stroke_style="dashed", stroke_width=1, fill="transparent", label_color="#9B0000"),
    "asg":     dict(stroke="#ED7100", stroke_style="dashed", stroke_width=2, fill="transparent", label_color="#ED7100"),
    "account": dict(stroke="#E7157B", stroke_style="solid",  stroke_width=2, fill="transparent", label_color="#E7157B"),
}

SEED_BASE = 4000


# ── service-catalog.csv 生成 ──────────────────────────────────────────────────

def _normalize_service_name(filename: str) -> str:
    """SVG ファイル名から表示用サービス名を生成する。"""
    name = filename
    for prefix in ("Arch_", "Res_", "Arch-Category_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    for suffix in ("_64.svg", "_48.svg", "_32.svg", "_16.svg"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    else:
        name = name.removesuffix(".svg")
    return name.replace("-", " ").replace("_", " ")


def generate_service_catalog_csv() -> None:
    """Asset-Package 以下の全 SVG をスキャンして service-catalog.csv を生成する。

    出力列: id, category, service, svg_file, rel_path, base64
    """
    asset_root     = Path(ASSET_DIR).resolve()
    workspace_root = asset_root.parent  # Asset-Package の親 = ワークスペースルート
    rows: list[dict] = []

    def _add(category: str, svg: Path) -> None:
        rel = svg.relative_to(workspace_root).as_posix()
        rows.append(dict(
            category=category,
            service=_normalize_service_name(svg.name),
            svg_file=svg.name,
            rel_path=rel,
            abs_path=svg,
        ))

    # 1. Architecture-Service-Icons/*/64/*.svg
    arch_svc = asset_root / "Architecture-Service-Icons"
    if arch_svc.is_dir():
        for cat_dir in sorted(arch_svc.iterdir()):
            if not cat_dir.is_dir():
                continue
            size64 = cat_dir / "64"
            if not size64.is_dir():
                continue
            cat_name = cat_dir.name.replace("Arch_", "").replace("-", " ")
            for svg in sorted(size64.glob("*.svg")):
                _add(cat_name, svg)

    # 2. Resource-Icons/*  (*_48.svg 直下 or 48/ サブディレクトリ)
    res_dir = asset_root / "Resource-Icons"
    if res_dir.is_dir():
        for cat_dir in sorted(res_dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            cat_name = "Resource " + cat_dir.name.replace("Res_", "").replace("-", " ")
            svgs = sorted(cat_dir.glob("*_48.svg"))
            if not svgs:
                sub48 = cat_dir / "48"
                if sub48.is_dir():
                    svgs = sorted(sub48.glob("*.svg"))
            for svg in svgs:
                _add(cat_name, svg)

    # 3. Architecture-Group-Icons/*.svg
    grp_dir = asset_root / "Architecture-Group-Icons"
    if grp_dir.is_dir():
        for svg in sorted(grp_dir.glob("*.svg")):
            _add("Architecture Groups", svg)

    # 4. Category-Icons/Arch-Category_64/*.svg
    cat_icon_dir = asset_root / "Category-Icons" / "Arch-Category_64"
    if cat_icon_dir.is_dir():
        for svg in sorted(cat_icon_dir.glob("*.svg")):
            _add("AWS Categories", svg)

    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = _csv.writer(f)
        writer.writerow(["id", "category", "service", "svg_file", "rel_path", "base64"])
        for i, row in enumerate(rows, start=1):
            with open(row["abs_path"], "rb") as svgf:
                b64 = "data:image/svg+xml;base64," + base64.b64encode(svgf.read()).decode("ascii")
            writer.writerow([i, row["category"], row["service"],
                             row["svg_file"], row["rel_path"], b64])

    print(f"service-catalog.csv 生成完了: {len(rows)} エントリ -> {CSV_OUT}")


def svg_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/svg+xml;base64,{data}"


def file_id(name: str) -> str:
    return hashlib.md5(name.encode()).hexdigest()[:16]


def _base(eid, x, y, w, h, seed):
    return dict(
        id=eid, x=round(x), y=round(y),
        width=round(w), height=round(h),
        angle=0, opacity=100,
        groupIds=[], frameId=None, roundness=None,
        seed=seed, version=1, versionNonce=seed,
        isDeleted=False, boundElements=[],
        updated=1709000000000, link=None, locked=False,
    )


def make_rect(eid, x, y, w, h, stroke, stroke_style, fill,
              stroke_width=2, seed=SEED_BASE):
    el = _base(eid, x, y, w, h, seed)
    el.update(
        type="rectangle",
        strokeColor=stroke,
        backgroundColor=fill,
        fillStyle="solid",
        strokeWidth=stroke_width,
        strokeStyle=stroke_style,
        roughness=0,
        roundness=None,
    )
    return el


def make_text(eid, x, y, w, h, text, font_size=12,
              color="#000000", bold=False, seed=SEED_BASE):
    el = _base(eid, x, y, w, h, seed)
    el.update(
        type="text",
        strokeColor=color,
        backgroundColor="transparent",
        fillStyle="solid",
        strokeWidth=1,
        strokeStyle="solid",
        roughness=0,
        text=text,
        fontSize=font_size,
        fontFamily=2,        # Helvetica (clean sans-serif, closest to AWS decks)
        textAlign="left",
        verticalAlign="top",
        containerId=None,
        originalText=text,
        autoResize=True,
        lineHeight=1.25,
    )
    return el


def make_image(eid, x, y, w, h, img_file_id, seed=SEED_BASE):
    el = _base(eid, x, y, w, h, seed)
    el.update(
        type="image",
        strokeColor="transparent",
        backgroundColor="transparent",
        fillStyle="solid",
        strokeWidth=1,
        strokeStyle="solid",
        roughness=0,
        status="saved",
        fileId=img_file_id,
        scale=[1, 1],
    )
    return el


def make_frame(eid, x, y, w, h, name, seed=SEED_BASE):
    el = _base(eid, x, y, w, h, seed)
    el.update(
        type="frame",
        strokeColor="#868e96",
        backgroundColor="transparent",
        fillStyle="solid",
        strokeWidth=2,
        strokeStyle="solid",
        roughness=0,
        name=name,
    )
    return el


# ── Helper: register SVG and return file-id ───────────────────────────────────
def ensure_icon(svg_name, icon_files, files_dict):
    if svg_name not in icon_files:
        return None
    fid = file_id(svg_name)
    if fid not in files_dict:
        files_dict[fid] = {
            "mimeType": "image/svg+xml",
            "id": fid,
            "dataURL": icon_files[svg_name],
            "created": 1709000000000,
            "lastRetrieved": 1709000000000,
        }
    return fid


# ── Helper: draw icon+label – icon corner aligned to frame corner ────────────
def add_header(elements, files_dict, icon_files,
               prefix, svg_name, label_text, label_color,
               rect_x, rect_y, icon_sz, fs, pad, seed_start):
    """Place icon at frame top-left corner, label immediately to its right.

    The top-left corner of the icon aligns exactly with the top-left corner
    of the parent rectangle.  Returns next seed value.
    """
    s = seed_start
    fid = ensure_icon(svg_name, icon_files, files_dict)
    if fid:
        # Icon pinned to the top-left corner of the frame
        elements.append(make_image(
            f"{prefix}-icon", rect_x, rect_y,
            icon_sz, icon_sz, fid, seed=s)); s += 1
        txt_x = rect_x + icon_sz + max(4, round(icon_sz * 0.18))
    else:
        # No icon – indent label by one pad unit
        txt_x = rect_x + pad
    # Vertically center text with the icon
    txt_y = rect_y + (icon_sz - fs) // 2
    txt_w = max(icon_sz * 5, 120)
    elements.append(make_text(
        f"{prefix}-label", txt_x, txt_y, txt_w, fs + 4,
        label_text, fs, label_color, bold=True, seed=s)); s += 1
    return s


# ── AZ stagger helpers ───────────────────────────────────────────────────────
_MAX_AZ_DARK   = 0.40   # 最背面 AZ の最大暗化率 (0=変化なし, 1=黒)
# staggered depth 0 (前面 AZ1)=白, depth 1/2 = 段階的に暗いティール (枠のみ)
_STAGGER_FILL  = ["#ffffff", "#c8e8e8", "#92cecd"]  # depth 0/1/2 の背景色


def darken_hex(color: str, factor: float) -> str:
    """hex カラーを factor(0=変化なし, 1=黒) の割合で暗くして返す。"""
    color = color.lstrip("#")
    r = max(0, int(int(color[0:2], 16) * (1 - factor)))
    g = max(0, int(int(color[2:4], 16) * (1 - factor)))
    b = max(0, int(int(color[4:6], 16) * (1 - factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Main scene builder ────────────────────────────────────────────────────────
def build_scene(W, H, suffix, icon_files,
                n_clouds=1, n_accounts=1, n_regions=1, n_azs=2,
                az_layout="grid", n_subnets=3, spacing_mode="both",
                start_mode="top"):
    """Build a scene with the given structural dimensions.

    Layout strategy:
      clouds   – side-by-side horizontally
      accounts – stacked vertically inside each cloud
      regions  – side-by-side horizontally inside each account
      AZs      – side-by-side (grid) or staggered-overlap (staggered)
      subnets  – stacked vertically inside each AZ (2/3/4 layers)

    n_subnets: 1層目 = Public Subnet, 2層目以降 = Private Subnet N
    az_layout: "grid"      – 通常の横並び配置
               "staggered" – 右下方向にずらして重ねる奥行き表現(2AZ/3AZのみ有効)
    spacing_mode: "both"       – 上下左右ともアイコン1個分の余白
                  "vertical"   – 上下のみアイコン1個分、左右は従来値
                  "horizontal" – 左右のみアイコン1個分、上下は従来値
    start_mode:   "top"  – Account を上から下へ配置（従来）
                  "left" – Account を左から右へ配置
    """
    elements = []
    files = {}
    s = SEED_BASE

    base   = min(W, H)
    fs_aws = 12
    fs_reg = 12
    fs_vpc = 12
    fs_az  = 12
    fs_sub = 12
    fs_sg  = 12

    logo_sz = 32
    ico_reg = 32
    ico_az  = 32
    ico_sub = 32
    layer_gap = ico_reg  # Account/Region/VPC/AZ 間の余白（アイコン1個分）

    if spacing_mode not in ("both", "vertical", "horizontal"):
        raise ValueError(f"Unknown spacing_mode: {spacing_mode}")
    if start_mode not in ("top", "left"):
        raise ValueError(f"Unknown start_mode: {start_mode}")

    m  = max(14, round(base * 0.022))
    p1 = max(10, round(base * 0.016))
    p2 = max(8,  round(base * 0.013))
    p3 = max(7,  round(base * 0.011))
    p4 = max(5,  round(base * 0.008))

    # 子要素を「余裕を持って」収めるための最小サイズ
    min_child_w = ico_reg + p2 * 4
    min_child_h = ico_reg + p2 * 4

    header_h = logo_sz + p3

    # ── Paper frame ───────────────────────────────────────────────────────
    elements.append(make_frame(
        f"paper-{suffix}", 0, 0, W, H,
        f"Paper Frame ({suffix})", seed=s)); s += 1

    # ── Clouds (side-by-side horizontally) ────────────────────────────────
    cloud_gap  = p1 if n_clouds > 1 else 0
    cloud_w    = (W - m * 2 - cloud_gap * (n_clouds - 1)) / n_clouds
    cloud_h    = H - m * 2

    for ci in range(n_clouds):
        cidx    = ci + 1
        cloud_x = m + ci * (cloud_w + cloud_gap)
        cloud_y = m

        st = STYLE["cloud"]
        elements.append(make_rect(
            f"cloud{cidx}-{suffix}", cloud_x, cloud_y, cloud_w, cloud_h,
            st["stroke"], st["stroke_style"], st["fill"],
            stroke_width=st["stroke_width"], seed=s)); s += 1
        cloud_label = "Amazon Web Services" if n_clouds == 1 else f"Amazon Web Services {cidx}"
        s = add_header(elements, files, icon_files,
                       f"cloud{cidx}-{suffix}", "AWS-Cloud-logo_32.svg",
                       cloud_label, "#232F3E",
                       cloud_x, cloud_y, logo_sz, fs_aws, p1, s)

        # ── Accounts (stacked vertically inside cloud) ────────────────
        acc_area_x = cloud_x + p1
        acc_area_y = cloud_y + header_h + p1
        acc_area_w = cloud_w - p1 * 2
        acc_area_h = cloud_h - header_h - p1 * 2

        acc_gap = p1 if n_accounts > 1 else 0
        if start_mode == "left":
            acc_w = (acc_area_w - acc_gap * (n_accounts - 1)) / n_accounts
            acc_h = acc_area_h
        else:
            acc_h = (acc_area_h - acc_gap * (n_accounts - 1)) / n_accounts
            acc_w = acc_area_w

        for ai in range(n_accounts):
            aidx  = ai + 1
            if start_mode == "left":
                acc_x = acc_area_x + ai * (acc_w + acc_gap)
                acc_y = acc_area_y
            else:
                acc_x = acc_area_x
                acc_y = acc_area_y + ai * (acc_h + acc_gap)

            st = STYLE["account"]
            elements.append(make_rect(
                f"account-c{cidx}a{aidx}-{suffix}", acc_x, acc_y, acc_w, acc_h,
                st["stroke"], st["stroke_style"], st["fill"],
                stroke_width=st["stroke_width"], seed=s)); s += 1
            acc_label = "AWS Account" if n_accounts == 1 else f"AWS Account {aidx}"
            s = add_header(elements, files, icon_files,
                           f"account-c{cidx}a{aidx}-{suffix}", "AWS-Account_32.svg",
                           acc_label, st["label_color"],
                           acc_x, acc_y, logo_sz, fs_aws, p1, s)

            # ── Regions (side-by-side horizontally inside account) ────
            reg_gap_x = layer_gap if spacing_mode in ("both", "horizontal") else p1
            reg_gap_y = layer_gap if spacing_mode in ("both", "vertical") else p1
            reg_area_x = acc_x + reg_gap_x
            reg_area_y = acc_y + header_h + reg_gap_y
            reg_area_w = acc_w - reg_gap_x * 2
            reg_area_h = acc_h - header_h - reg_gap_y * 2

            if reg_area_w < min_child_w or reg_area_h < min_child_h:
                continue

            reg_gap = p2 if n_regions > 1 else 0
            if start_mode == "left":
                reg_w = reg_area_w
                reg_h = (reg_area_h - reg_gap * (n_regions - 1)) / n_regions
            else:
                reg_w = (reg_area_w - reg_gap * (n_regions - 1)) / n_regions
                reg_h = reg_area_h

            for ri in range(n_regions):
                ridx  = ri + 1
                if start_mode == "left":
                    reg_x = reg_area_x
                    reg_y = reg_area_y + ri * (reg_h + reg_gap)
                else:
                    reg_x = reg_area_x + ri * (reg_w + reg_gap)
                    reg_y = reg_area_y

                st = STYLE["region"]
                elements.append(make_rect(
                    f"region-c{cidx}a{aidx}r{ridx}-{suffix}",
                    reg_x, reg_y, reg_w, reg_h,
                    st["stroke"], st["stroke_style"], st["fill"],
                    stroke_width=st["stroke_width"], seed=s)); s += 1
                reg_label = "Region" if n_regions == 1 else f"Region {ridx}"
                s = add_header(elements, files, icon_files,
                               f"region-c{cidx}a{aidx}r{ridx}-{suffix}",
                               "Region_32.svg", reg_label, st["label_color"],
                               reg_x, reg_y, ico_reg, fs_reg, p2, s)

                # ── VPC inside region ─────────────────────────────────
                vpc_gap_x = layer_gap if spacing_mode in ("both", "horizontal") else p2
                vpc_gap_y = layer_gap if spacing_mode in ("both", "vertical") else p2
                vpc_x = reg_x + vpc_gap_x
                vpc_y = reg_y + header_h + vpc_gap_y
                vpc_w = reg_w - vpc_gap_x * 2
                vpc_h = reg_h - header_h - vpc_gap_y * 2

                if vpc_w < min_child_w or vpc_h < min_child_h:
                    continue

                st = STYLE["vpc"]
                elements.append(make_rect(
                    f"vpc-c{cidx}a{aidx}r{ridx}-{suffix}",
                    vpc_x, vpc_y, vpc_w, vpc_h,
                    st["stroke"], st["stroke_style"], st["fill"],
                    stroke_width=st["stroke_width"], seed=s)); s += 1
                s = add_header(elements, files, icon_files,
                               f"vpc-c{cidx}a{aidx}r{ridx}-{suffix}",
                               "Virtual-private-cloud-VPC_32.svg", "VPC",
                               st["label_color"],
                               vpc_x, vpc_y, ico_reg, fs_vpc, p2, s)

                # ── AZs ──────────────────────────────────────────────
                az_gap_x = layer_gap if spacing_mode in ("both", "horizontal") else p3
                az_gap_y = layer_gap if spacing_mode in ("both", "vertical") else p3
                az_area_x = vpc_x + az_gap_x
                az_area_y = vpc_y + header_h + az_gap_y
                az_area_w = vpc_w - az_gap_x * 2
                az_area_h = vpc_h - header_h - az_gap_y * 2

                if az_area_w < min_child_w or az_area_h < min_child_h:
                    continue

                use_stagger = (az_layout == "staggered" and n_azs >= 2)
                if use_stagger:
                    # 各 AZ を右下方向にずらして重ねる奥行き表現
                    stagger   = max(10, round(base * 0.015))
                    az_w      = az_area_w - stagger * (n_azs - 1)
                    az_h      = az_area_h - stagger * (n_azs - 1)
                    az_gap    = 0
                    az_render = list(range(n_azs - 1, -1, -1))  # 背面→前面の順で描画
                else:
                    stagger   = 0
                    az_gap    = max(6, round(base * 0.009)) if n_azs > 1 else 0
                    if start_mode == "left":
                        az_w = az_area_w
                        az_h = (az_area_h - az_gap * (n_azs - 1)) / n_azs
                    else:
                        az_w = (az_area_w - az_gap * (n_azs - 1)) / n_azs
                        az_h = az_area_h
                    az_render = list(range(n_azs))

                if az_w < min_child_w or az_h < min_child_h:
                    continue

                for zi in az_render:
                    zidx = zi + 1

                    if use_stagger:
                        az_x = az_area_x + zi * stagger
                        az_y = az_area_y + zi * stagger
                        # zi=0 が最前面(暗化なし)、zi=n_azs-1 が最背面(最大暗化)
                        dark_factor = (zi / (n_azs - 1)) * _MAX_AZ_DARK
                        depth       = zi
                    else:
                        if start_mode == "left":
                            az_x = az_area_x
                            az_y = az_area_y + zi * (az_h + az_gap)
                        else:
                            az_x = az_area_x + zi * (az_w + az_gap)
                            az_y = az_area_y
                        dark_factor = 0.0
                        depth       = 0

                    # 深度に応じてカラーを暗化
                    az_stroke       = darken_hex(STYLE["az"]["stroke"],       dark_factor)
                    az_label_color  = darken_hex(STYLE["az"]["label_color"],  dark_factor)
                    # staggered のみ STAGGER_FILL を使用; grid は通常スタイルの fill
                    if use_stagger:
                        az_fill = _STAGGER_FILL[min(depth, len(_STAGGER_FILL) - 1)]
                    else:
                        az_fill = STYLE["az"]["fill"]
                    sub_pub_stroke  = darken_hex(STYLE["pub_sub"]["stroke"],  dark_factor)
                    sub_pub_label   = darken_hex(STYLE["pub_sub"]["label_color"], dark_factor)
                    sub_priv_stroke = darken_hex(STYLE["priv_sub"]["stroke"], dark_factor)
                    sub_priv_label  = darken_hex(STYLE["priv_sub"]["label_color"], dark_factor)
                    sg_stroke       = darken_hex(STYLE["sg"]["stroke"],       dark_factor)
                    sg_label        = darken_hex(STYLE["sg"]["label_color"],  dark_factor)
                    asg_stroke      = darken_hex(STYLE["asg"]["stroke"],      dark_factor)
                    asg_label       = darken_hex(STYLE["asg"]["label_color"], dark_factor)

                    # staggered モードの背面 AZ (zi > 0) は枠とラベルのみ
                    is_stagger_bg = use_stagger and zi > 0

                    st = STYLE["az"]
                    az_eid = f"az{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                    elements.append(make_rect(
                        az_eid, az_x, az_y, az_w, az_h,
                        az_stroke, st["stroke_style"], az_fill,
                        stroke_width=st["stroke_width"], seed=s)); s += 1
                    elements.append(make_text(
                        f"{az_eid}-label",
                        az_x + p3, az_y + p3,
                        round(az_w * 0.9), fs_az + 4,
                        f"Availability Zone {zidx}", fs_az,
                        az_label_color, bold=True, seed=s)); s += 1

                    # 背面 AZ は枠のみ — 内部コンポーネントをスキップ
                    if is_stagger_bg:
                        continue

                    az_header = p3 + fs_az + p3

                    # subnets inside AZ
                    # top始点: 縦積み（従来） / left始点: 左から横並び（Public→Private）
                    sub_gap = max(ico_sub + p4 * 2, round(base * 0.01))
                    if start_mode == "left":
                        sub_left_x = az_x + p3
                        sub_top_y  = az_y + az_header
                        sub_h_val  = az_h - az_header - p3
                        sub_w_val  = (az_w - p3 * 2 - sub_gap * (n_subnets - 1)) / n_subnets
                    else:
                        sub_x     = az_x + p3
                        sub_w_val = az_w - p3 * 2
                        sub_h_val = (az_h - az_header - p3 - sub_gap * (n_subnets - 1)) / n_subnets
                        sub_top_y = az_y + az_header

                    if start_mode == "left":
                        if sub_w_val < (ico_sub + p4 * 2) or sub_h_val < (ico_sub + p4 * 2):
                            continue
                    else:
                        if sub_w_val < (ico_sub + p4 * 2) or sub_h_val < (ico_sub + p4 * 2):
                            continue

                    st_pub  = STYLE["pub_sub"]
                    st_priv = STYLE["priv_sub"]
                    st_sg   = STYLE["sg"]
                    def _add_sg_vertical(eid, sub_x, sub_y, inner_y, h_parent, base_y):
                        sg_x = sub_x + p4
                        sg_w = sub_w_val - p4 * 2
                        sg_h = h_parent - (inner_y - base_y) - p4
                        elements.append(make_rect(
                            eid, sg_x, inner_y, sg_w, sg_h,
                            sg_stroke, st_sg["stroke_style"], st_sg["fill"],
                            stroke_width=st_sg["stroke_width"], seed=s))
                        return s + 1, sg_x, sg_w

                    def _add_sg_horizontal(eid, sub_x, sub_y):
                        sg_x = sub_x + p4
                        sg_y = sub_y + ico_sub + p4
                        sg_w = sub_w_val - p4 * 2
                        sg_h = sub_h_val - (ico_sub + p4) - p4
                        elements.append(make_rect(
                            eid, sg_x, sg_y, sg_w, sg_h,
                            sg_stroke, st_sg["stroke_style"], st_sg["fill"],
                            stroke_width=st_sg["stroke_width"], seed=s))
                        return s + 1, sg_x, sg_y, sg_w

                    for si in range(n_subnets):
                        if start_mode == "left":
                            sub_x = sub_left_x + si * (sub_w_val + sub_gap)
                            sub_y = sub_top_y
                        else:
                            sub_x = az_x + p3
                            sub_y = sub_top_y + si * (sub_h_val + sub_gap)

                        if si == 0:
                            subnet_label = "Public Subnet"
                            subnet_style = st_pub
                            subnet_stroke = sub_pub_stroke
                            subnet_label_color = sub_pub_label
                            subnet_icon = "Public-subnet_32.svg"
                            subnet_prefix = "pub"
                        else:
                            subnet_label = "Private Subnet" if si == 1 else f"Private Subnet {si}"
                            subnet_style = st_priv
                            subnet_stroke = sub_priv_stroke
                            subnet_label_color = sub_priv_label
                            subnet_icon = "Private-subnet_32.svg"
                            subnet_prefix = f"priv{si}"

                        sub_eid = f"{subnet_prefix}-sub{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                        elements.append(make_rect(
                            sub_eid, sub_x, sub_y, sub_w_val, sub_h_val,
                            subnet_stroke, subnet_style["stroke_style"], subnet_style["fill"],
                            stroke_width=subnet_style["stroke_width"], seed=s)); s += 1
                        s = add_header(elements, files, icon_files,
                                       sub_eid, subnet_icon,
                                       subnet_label, subnet_label_color,
                                       sub_x, sub_y, ico_sub, fs_sub, p4, s)

                        sg_eid = f"sg-{subnet_prefix}-{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                        if start_mode == "left":
                            s, sg_x, sg_y, sg_w = _add_sg_horizontal(sg_eid, sub_x, sub_y)
                            elements.append(make_text(
                                f"{sg_eid}-label",
                                sg_x + p4, sg_y + p4,
                                round(sg_w * 0.9), fs_sg + 4,
                                "Security Group", fs_sg,
                                sg_label, bold=True, seed=s)); s += 1
                        else:
                            sub_inner_y = sub_y + ico_sub + p4
                            s, sg_x, sg_w = _add_sg_vertical(sg_eid, sub_x, sub_y, sub_inner_y, sub_h_val, sub_y)
                            elements.append(make_text(
                                f"{sg_eid}-label",
                                sg_x + p4, sub_inner_y + p4,
                                round(sg_w * 0.9), fs_sg + 4,
                                "Security Group", fs_sg,
                                sg_label, bold=True, seed=s)); s += 1

    return elements, files


def build_excalidraw(W, H, suffix, icon_files,
                     n_clouds=1, n_accounts=1, n_regions=1, n_azs=2,
                     az_layout="grid", n_subnets=3, spacing_mode="both",
                     start_mode="top"):
    elements, files = build_scene(W, H, suffix, icon_files,
                                  n_clouds, n_accounts, n_regions, n_azs,
                                  az_layout=az_layout, n_subnets=n_subnets,
                                  spacing_mode=spacing_mode,
                                  start_mode=start_mode)
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": files,
    }


# ── Variant definitions ───────────────────────────────────────────────────────
# All (n_clouds, n_accounts, n_regions, n_azs, az_layout, n_subnets, spacing_mode, start_mode) combinations
# staggered バリアントは 2AZ / 3AZ のみ生成
def all_variants():
    spacing_modes = ("vertical", "horizontal")
    start_modes = ("top", "left")
    for nc in (1, 2):
        for na in (1, 2, 3):
            for nr in (1, 2):
                for nz in (1, 2, 3):
                    for ns in (2, 3, 4):
                        for sm in spacing_modes:
                            for st in start_modes:
                                yield nc, na, nr, nz, "grid", ns, sm, st
                                if nz >= 2:
                                    yield nc, na, nr, nz, "staggered", ns, sm, st


def variant_dir_name(nc, na, nr, nz, az_layout="grid", ns=3, spacing_mode="both", start_mode="top"):
    name = f"{nc}cloud-{na}account-{nr}region-{nz}az-{ns}subnet"
    if az_layout == "staggered":
        name += "-staggered"
    if spacing_mode == "vertical":
        name += "-vspace"
    elif spacing_mode == "horizontal":
        name += "-hspace"
    if start_mode == "left":
        name += "-leftstart"
    return name


def main():
    aws_frames_root = os.path.join(OUT_DIR, "..")   # templates/aws-frames/../ = templates/
    aws_frames_dir  = OUT_DIR                        # templates/aws-frames/
    base_dir        = os.path.join(aws_frames_dir, "base")

    # ── Move existing top-level *.excalidraw files to base/ ──────────────
    existing = [f for f in os.listdir(aws_frames_dir)
                if f.endswith(".excalidraw")] if os.path.isdir(aws_frames_dir) else []
    if existing:
        os.makedirs(base_dir, exist_ok=True)
        for fname in existing:
            src = os.path.join(aws_frames_dir, fname)
            dst = os.path.join(base_dir, fname)
            shutil.move(src, dst)
        print(f"Moved {len(existing)} existing files → {base_dir}")

    # ── service-catalog.csv を再生成 ─────────────────────────────────────
    print("=== service-catalog.csv を生成中 ===")
    generate_service_catalog_csv()
    print()

    # ── Load SVG icons ────────────────────────────────────────────────────
    icon_files = {}
    for fname in os.listdir(ICON_DIR):
        if fname.endswith(".svg") and "Dark" not in fname:
            icon_files[fname] = svg_to_data_url(os.path.join(ICON_DIR, fname))
    print(f"Loaded {len(icon_files)} icons from {ICON_DIR}\n")

    # ── Generate all variants ─────────────────────────────────────────────
    total_files = 0
    variants = list(all_variants())
    grid_count     = sum(1 for v in variants if v[4] == "grid")
    stagger_count  = sum(1 for v in variants if v[4] == "staggered")
    vspace_count   = sum(1 for v in variants if v[6] == "vertical")
    hspace_count   = sum(1 for v in variants if v[6] == "horizontal")
    top_count      = sum(1 for v in variants if v[7] == "top")
    left_count     = sum(1 for v in variants if v[7] == "left")
    per_variant    = len(PAPER_SIZES) * 2
    print(f"Generating {len(variants)} variants "
          f"({grid_count} grid + {stagger_count} staggered, "
          f"{vspace_count} vspace + {hspace_count} hspace, "
          f"{top_count} top + {left_count} left-start) "
          f"× {per_variant} paper sizes = {len(variants) * per_variant} files …\n")

    for nc, na, nr, nz, az_layout, ns, spacing_mode, start_mode in variants:
        vname   = variant_dir_name(nc, na, nr, nz, az_layout, ns, spacing_mode, start_mode)
        vdir    = os.path.join(aws_frames_dir, vname)
        os.makedirs(vdir, exist_ok=True)

        for paper, (pw, ph) in PAPER_SIZES.items():
            for orientation, (W, H) in [("portrait", (pw, ph)), ("landscape", (ph, pw))]:
                suffix = f"{paper}-{orientation}"
                scene  = build_excalidraw(W, H, suffix, icon_files,
                                          n_clouds=nc, n_accounts=na,
                                          n_regions=nr, n_azs=nz,
                                          az_layout=az_layout, n_subnets=ns,
                                          spacing_mode=spacing_mode,
                                          start_mode=start_mode)
                out = os.path.join(vdir, f"{suffix}.excalidraw")
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(scene, f, ensure_ascii=False, indent=2)
                total_files += 1

        layout_tag = " [staggered]" if az_layout == "staggered" else ""
        spacing_tag = f" [{spacing_mode}]"
        start_tag = f" [{start_mode}]"
        print(f"  {vname}/{layout_tag}{spacing_tag}{start_tag}  ({per_variant} files, "
              f"e.g. {len(scene['elements'])} elements in A4-portrait)")

    print(f"\nDone: {total_files} files → {aws_frames_dir}")


if __name__ == "__main__":
    main()

