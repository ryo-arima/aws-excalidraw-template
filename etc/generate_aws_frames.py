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
                az_layout="grid", n_subnets=3):
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

    m  = max(14, round(base * 0.022))
    p1 = max(10, round(base * 0.016))
    p2 = max(8,  round(base * 0.013))
    p3 = max(7,  round(base * 0.011))
    p4 = max(5,  round(base * 0.008))

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
        acc_h   = (acc_area_h - acc_gap * (n_accounts - 1)) / n_accounts
        acc_w   = acc_area_w

        for ai in range(n_accounts):
            aidx  = ai + 1
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
            reg_area_x = acc_x + p1
            reg_area_y = acc_y + header_h + p1
            reg_area_w = acc_w - p1 * 2
            reg_area_h = acc_h - header_h - p1 * 2

            reg_gap = p2 if n_regions > 1 else 0
            reg_w   = (reg_area_w - reg_gap * (n_regions - 1)) / n_regions
            reg_h   = reg_area_h

            for ri in range(n_regions):
                ridx  = ri + 1
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
                vpc_x = reg_x + p2
                vpc_y = reg_y + header_h + p2
                vpc_w = reg_w - p2 * 2
                vpc_h = reg_h - header_h - p2 * 2

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
                az_area_x = vpc_x + p3
                az_area_y = vpc_y + header_h + p3
                az_area_w = vpc_w - p3 * 2
                az_area_h = vpc_h - header_h - p3 * 2

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
                    az_w      = (az_area_w - az_gap * (n_azs - 1)) / n_azs
                    az_h      = az_area_h
                    az_render = list(range(n_azs))

                for zi in az_render:
                    zidx = zi + 1

                    if use_stagger:
                        az_x = az_area_x + zi * stagger
                        az_y = az_area_y + zi * stagger
                        # zi=0 が最前面(暗化なし)、zi=n_azs-1 が最背面(最大暗化)
                        dark_factor = (zi / (n_azs - 1)) * _MAX_AZ_DARK
                        depth       = zi
                    else:
                        az_x        = az_area_x + zi * (az_w + az_gap)
                        az_y        = az_area_y
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

                    # subnets inside AZ (3 layers: Public / Private 1 / Private 2)
                    # sub_gap はアイコン1個を配置できる幅を確保
                    sub_gap   = max(ico_sub + p4 * 2, round(base * 0.01))
                    sub_x     = az_x + p3
                    sub_w_val = az_w - p3 * 2
                    sub_h_val = (az_h - az_header - p3 - sub_gap * 2) / 3
                    pub_y     = az_y + az_header
                    priv1_y   = pub_y   + sub_h_val + sub_gap
                    priv2_y   = priv1_y + sub_h_val + sub_gap

                    pub_eid   = f"pub-sub{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                    priv1_eid = f"priv1-sub{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                    priv2_eid = f"priv2-sub{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"

                    st_pub  = STYLE["pub_sub"]
                    st_priv = STYLE["priv_sub"]
                    st_sg   = STYLE["sg"]
                    sg_x    = sub_x + p4
                    sg_w    = sub_w_val - p4 * 2

                    def _add_sg(eid, inner_y, h_parent, base_y):
                        sg_h = h_parent - (inner_y - base_y) - p4
                        elements.append(make_rect(
                            eid, sg_x, inner_y, sg_w, sg_h,
                            sg_stroke, st_sg["stroke_style"], st_sg["fill"],
                            stroke_width=st_sg["stroke_width"], seed=s)); return s + 1

                    def _add_sg_label(eid, inner_y):
                        elements.append(make_text(
                            f"{eid}-label",
                            sg_x + p4, inner_y + p4,
                            round(sg_w * 0.9), fs_sg + 4,
                            "Security Group", fs_sg,
                            sg_label, bold=True, seed=s)); return s + 1

                    # ── Public Subnet ─────────────────────────────────
                    elements.append(make_rect(
                        pub_eid, sub_x, pub_y, sub_w_val, sub_h_val,
                        sub_pub_stroke, st_pub["stroke_style"], st_pub["fill"],
                        stroke_width=st_pub["stroke_width"], seed=s)); s += 1
                    s = add_header(elements, files, icon_files,
                                   pub_eid, "Public-subnet_32.svg",
                                   "Public Subnet", sub_pub_label,
                                   sub_x, pub_y, ico_sub, fs_sub, p4, s)
                    pub_inner_y = pub_y + ico_sub + p4
                    sg_pub_eid  = f"sg-pub{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                    s = _add_sg(sg_pub_eid, pub_inner_y, sub_h_val, pub_y)
                    s = _add_sg_label(sg_pub_eid, pub_inner_y)

                    # ── Private Subnet 1 ──────────────────────────────
                    elements.append(make_rect(
                        priv1_eid, sub_x, priv1_y, sub_w_val, sub_h_val,
                        sub_priv_stroke, st_priv["stroke_style"], st_priv["fill"],
                        stroke_width=st_priv["stroke_width"], seed=s)); s += 1
                    s = add_header(elements, files, icon_files,
                                   priv1_eid, "Private-subnet_32.svg",
                                   "Private Subnet", sub_priv_label,
                                   sub_x, priv1_y, ico_sub, fs_sub, p4, s)
                    priv1_inner_y = priv1_y + ico_sub + p4
                    sg_priv1_eid  = f"sg-priv1-{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                    s = _add_sg(sg_priv1_eid, priv1_inner_y, sub_h_val, priv1_y)
                    s = _add_sg_label(sg_priv1_eid, priv1_inner_y)

                    # ── Private Subnet 2 ──────────────────────────────
                    elements.append(make_rect(
                        priv2_eid, sub_x, priv2_y, sub_w_val, sub_h_val,
                        sub_priv_stroke, st_priv["stroke_style"], st_priv["fill"],
                        stroke_width=st_priv["stroke_width"], seed=s)); s += 1
                    s = add_header(elements, files, icon_files,
                                   priv2_eid, "Private-subnet_32.svg",
                                   "Private Subnet 2", sub_priv_label,
                                   sub_x, priv2_y, ico_sub, fs_sub, p4, s)
                    priv2_inner_y = priv2_y + ico_sub + p4
                    sg_priv2_eid  = f"sg-priv2-{zidx}-c{cidx}a{aidx}r{ridx}-{suffix}"
                    s = _add_sg(sg_priv2_eid, priv2_inner_y, sub_h_val, priv2_y)
                    s = _add_sg_label(sg_priv2_eid, priv2_inner_y)

    return elements, files


def build_excalidraw(W, H, suffix, icon_files,
                     n_clouds=1, n_accounts=1, n_regions=1, n_azs=2,
                     az_layout="grid", n_subnets=3):
    elements, files = build_scene(W, H, suffix, icon_files,
                                  n_clouds, n_accounts, n_regions, n_azs,
                                  az_layout=az_layout, n_subnets=n_subnets)
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": files,
    }


# ── Variant definitions ───────────────────────────────────────────────────────
# All (n_clouds, n_accounts, n_regions, n_azs, az_layout, n_subnets) combinations
# staggered バリアントは 2AZ / 3AZ のみ生成
def all_variants():
    for nc in (1, 2):
        for na in (1, 2, 3):
            for nr in (1, 2):
                for nz in (1, 2, 3):
                    for ns in (2, 3, 4):
                        yield nc, na, nr, nz, "grid", ns
                        if nz >= 2:
                            yield nc, na, nr, nz, "staggered", ns


def variant_dir_name(nc, na, nr, nz, az_layout="grid", ns=3):
    name = f"{nc}cloud-{na}account-{nr}region-{nz}az-{ns}subnet"
    if az_layout == "staggered":
        name += "-staggered"
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
    per_variant    = len(PAPER_SIZES) * 2
    print(f"Generating {len(variants)} variants ({grid_count} grid + {stagger_count} staggered) "
          f"× {per_variant} paper sizes = {len(variants) * per_variant} files …\n")

    for nc, na, nr, nz, az_layout, ns in variants:
        vname   = variant_dir_name(nc, na, nr, nz, az_layout, ns)
        vdir    = os.path.join(aws_frames_dir, vname)
        os.makedirs(vdir, exist_ok=True)

        for paper, (pw, ph) in PAPER_SIZES.items():
            for orientation, (W, H) in [("portrait", (pw, ph)), ("landscape", (ph, pw))]:
                suffix = f"{paper}-{orientation}"
                scene  = build_excalidraw(W, H, suffix, icon_files,
                                          n_clouds=nc, n_accounts=na,
                                          n_regions=nr, n_azs=nz,
                                          az_layout=az_layout, n_subnets=ns)
                out = os.path.join(vdir, f"{suffix}.excalidraw")
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(scene, f, ensure_ascii=False, indent=2)
                total_files += 1

        layout_tag = " [staggered]" if az_layout == "staggered" else ""
        print(f"  {vname}/{layout_tag}  ({per_variant} files, "
              f"e.g. {len(scene['elements'])} elements in A4-portrait)")

    print(f"\nDone: {total_files} files → {aws_frames_dir}")


if __name__ == "__main__":
    main()

