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
"""
import json
import os
import base64
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "..", "Asset-Package", "Architecture-Group-Icons")
OUT_DIR  = os.path.join(BASE_DIR, "..", "templates", "aws-frames")

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
    "sg":      dict(stroke="#7D8998", stroke_style="dashed", stroke_width=1, fill="transparent", label_color="#7D8998"),
    "asg":     dict(stroke="#ED7100", stroke_style="dashed", stroke_width=2, fill="transparent", label_color="#ED7100"),
    "account": dict(stroke="#E7157B", stroke_style="solid",  stroke_width=2, fill="transparent", label_color="#E7157B"),
}

SEED_BASE = 4000


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


# ── Main scene builder ────────────────────────────────────────────────────────
def build_scene(W, H, suffix, icon_files):
    elements = []
    files = {}
    s = SEED_BASE

    base   = min(W, H)
    # Fixed font sizes (S=12)
    fs_aws = 12   # AWS Account / Cloud label
    fs_reg = 12   # Region label
    fs_vpc = 12   # VPC label
    fs_az  = 12   # AZ label
    fs_sub = 12   # Subnet / ASG label
    fs_sg  = 12   # SG label

    logo_sz = 32   # icon size (all fixed at 32)
    ico_reg = 32
    ico_az  = 32
    ico_sub = 32

    m  = max(14, round(base * 0.022))   # outer margin (paper edge → account)
    p1 = max(10, round(base * 0.016))   # padding between major containers
    p2 = max(8,  round(base * 0.013))   # padding inside region
    p3 = max(7,  round(base * 0.011))   # padding inside VPC / AZ
    p4 = max(5,  round(base * 0.008))   # padding inside subnet

    header_h = logo_sz + p3            # header row height (icon + small gap below)

    # ── Paper frame ───────────────────────────────────────────────────────
    elements.append(make_frame(
        f"paper-{suffix}", 0, 0, W, H,
        f"Paper Frame ({suffix})", seed=s)); s += 1

    # ── AWS Cloud ─────────────────────────────────────────────────────────
    cloud_x = m;  cloud_y = m
    cloud_w = W - m * 2;  cloud_h = H - m * 2
    st = STYLE["cloud"]
    elements.append(make_rect(
        f"cloud-{suffix}", cloud_x, cloud_y, cloud_w, cloud_h,
        st["stroke"], st["stroke_style"], st["fill"],
        stroke_width=st["stroke_width"], seed=s)); s += 1
    s = add_header(elements, files, icon_files,
                   f"cloud-{suffix}", "AWS-Cloud-logo_32.svg",
                   "Amazon Web Services", "#232F3E",
                   cloud_x, cloud_y, logo_sz, fs_aws, p1, s)

    # ── AWS Account ───────────────────────────────────────────────────────
    acc_x = cloud_x + p1
    acc_y = cloud_y + header_h + p1
    acc_w = cloud_w - p1 * 2
    acc_h = cloud_h - header_h - p1 * 2
    st = STYLE["account"]
    elements.append(make_rect(
        f"account-{suffix}", acc_x, acc_y, acc_w, acc_h,
        st["stroke"], st["stroke_style"], st["fill"],
        stroke_width=st["stroke_width"], seed=s)); s += 1
    s = add_header(elements, files, icon_files,
                   f"account-{suffix}", "AWS-Account_32.svg",
                   "AWS Account", st["label_color"],
                   acc_x, acc_y, logo_sz, fs_aws, p1, s)

    # ── Region ────────────────────────────────────────────────────────────
    reg_x = acc_x + p1
    reg_y = acc_y + header_h + p1
    reg_w = acc_w - p1 * 2
    reg_h = acc_h - header_h - p1 * 2
    st = STYLE["region"]
    elements.append(make_rect(
        f"region-{suffix}", reg_x, reg_y, reg_w, reg_h,
        st["stroke"], st["stroke_style"], st["fill"],
        stroke_width=st["stroke_width"], seed=s)); s += 1
    s = add_header(elements, files, icon_files,
                   f"region-{suffix}", "Region_32.svg", "Region", st["label_color"],
                   reg_x, reg_y, ico_reg, fs_reg, p2, s)

    # ── VPC ───────────────────────────────────────────────────────────────
    vpc_x = reg_x + p2
    vpc_y = reg_y + header_h + p2
    vpc_w = reg_w - p2 * 2
    vpc_h = reg_h - header_h - p2 * 2
    st = STYLE["vpc"]
    elements.append(make_rect(
        f"vpc-{suffix}", vpc_x, vpc_y, vpc_w, vpc_h,
        st["stroke"], st["stroke_style"], st["fill"],
        stroke_width=st["stroke_width"], seed=s)); s += 1
    s = add_header(elements, files, icon_files,
                   f"vpc-{suffix}", "Virtual-private-cloud-VPC_32.svg", "VPC", st["label_color"],
                   vpc_x, vpc_y, ico_reg, fs_vpc, p2, s)

    # ── Two AZs side by side inside VPC ──────────────────────────────────
    az_gap = max(6, round(base * 0.009))
    az_y   = vpc_y + header_h + p3
    az_h   = vpc_h - header_h - p3 * 2
    az_w   = (vpc_w - p3 * 2 - az_gap) / 2

    for i, az_x in enumerate([vpc_x + p3, vpc_x + p3 + az_w + az_gap], start=1):
        az_num = str(i)
        st = STYLE["az"]
        elements.append(make_rect(
            f"az{az_num}-{suffix}", az_x, az_y, az_w, az_h,
            st["stroke"], st["stroke_style"], st["fill"],
            stroke_width=st["stroke_width"], seed=s)); s += 1
        elements.append(make_text(
            f"az{az_num}-label-{suffix}",
            az_x + p3, az_y + p3,
            round(az_w * 0.8), fs_az + 4,
            f"Availability Zone {az_num}", fs_az, st["label_color"], bold=True, seed=s)); s += 1

        az_header = p3 + fs_az + p3

        # subnets inside AZ
        sub_gap   = max(4, round(base * 0.006))
        sub_x     = az_x + p3
        sub_w_val = az_w - p3 * 2
        sub_h_val = (az_h - az_header - p3 - sub_gap) / 2
        pub_y     = az_y + az_header
        priv_y    = pub_y + sub_h_val + sub_gap

        # Public Subnet
        st_pub = STYLE["pub_sub"]
        elements.append(make_rect(
            f"pub-sub{az_num}-{suffix}", sub_x, pub_y, sub_w_val, sub_h_val,
            st_pub["stroke"], st_pub["stroke_style"], st_pub["fill"],
            stroke_width=st_pub["stroke_width"], seed=s)); s += 1
        s = add_header(elements, files, icon_files,
                       f"pub-sub{az_num}-{suffix}", "Public-subnet_32.svg",
                       "Public Subnet", st_pub["label_color"],
                       sub_x, pub_y, ico_sub, fs_sub, p4, s)

        # Security Group inside Public Subnet
        pub_inner_y = pub_y + ico_sub + p4
        sg_x  = sub_x + p4
        sg_y  = pub_inner_y
        sg_w  = sub_w_val - p4 * 2
        sg_h  = sub_h_val - (pub_inner_y - pub_y) - p4
        if sg_h > fs_sg * 3:
            st_sg = STYLE["sg"]
            elements.append(make_rect(
                f"sg{az_num}-{suffix}", sg_x, sg_y, sg_w, sg_h,
                st_sg["stroke"], st_sg["stroke_style"], st_sg["fill"],
                stroke_width=st_sg["stroke_width"], seed=s)); s += 1
            elements.append(make_text(
                f"sg{az_num}-label-{suffix}",
                sg_x + p4, sg_y + p4,
                round(sg_w * 0.9), fs_sg + 4,
                "Security Group", fs_sg, st_sg["label_color"], bold=True, seed=s)); s += 1

        # Private Subnet
        st_priv = STYLE["priv_sub"]
        elements.append(make_rect(
            f"priv-sub{az_num}-{suffix}", sub_x, priv_y, sub_w_val, sub_h_val,
            st_priv["stroke"], st_priv["stroke_style"], st_priv["fill"],
            stroke_width=st_priv["stroke_width"], seed=s)); s += 1
        s = add_header(elements, files, icon_files,
                       f"priv-sub{az_num}-{suffix}", "Private-subnet_32.svg",
                       "Private Subnet", st_priv["label_color"],
                       sub_x, priv_y, ico_sub, fs_sub, p4, s)

        # Auto Scaling Group inside Private Subnet
        priv_inner_y = priv_y + ico_sub + p4
        asg_x = sub_x + p4
        asg_y = priv_inner_y
        asg_w = sub_w_val - p4 * 2
        asg_h = sub_h_val - (priv_inner_y - priv_y) - p4
        if asg_h > fs_sg * 3:
            st_asg = STYLE["asg"]
            elements.append(make_rect(
                f"asg{az_num}-{suffix}", asg_x, asg_y, asg_w, asg_h,
                st_asg["stroke"], st_asg["stroke_style"], st_asg["fill"],
                stroke_width=st_asg["stroke_width"], seed=s)); s += 1
            s = add_header(elements, files, icon_files,
                           f"asg{az_num}-{suffix}", "Auto-Scaling-group_32.svg",
                           "Auto Scaling Group", st_asg["label_color"],
                           asg_x, asg_y, ico_sub, fs_sub, p4, s)

    return elements, files


def build_excalidraw(W, H, suffix, icon_files):
    elements, files = build_scene(W, H, suffix, icon_files)
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": files,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load SVG icons
    icon_files = {}
    for fname in os.listdir(ICON_DIR):
        if fname.endswith(".svg") and "Dark" not in fname:
            icon_files[fname] = svg_to_data_url(os.path.join(ICON_DIR, fname))
    print(f"Loaded {len(icon_files)} icons from {ICON_DIR}")

    count = 0
    for name, (pw, ph) in PAPER_SIZES.items():
        for orientation, (W, H) in [("portrait", (pw, ph)), ("landscape", (ph, pw))]:
            suffix = f"{name}-{orientation}"
            scene  = build_excalidraw(W, H, suffix, icon_files)
            out    = os.path.join(OUT_DIR, f"{suffix}.excalidraw")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(scene, f, ensure_ascii=False, indent=2)
            print(f"  {suffix}.excalidraw  ({W}x{H}px,  {len(scene['elements'])} elements)")
            count += 1

    print(f"\nDone: {count} files -> {OUT_DIR}")


if __name__ == "__main__":
    main()

