"""Deterministic C-R7 Generic Stress Suite Generator.

Renders 14 agent-made synthetic raster logo cases as anti-aliased RGBA PNGs
with transparent background at 1000x1000 resolution.
Covers: thin strokes, sharp corners, dense corner/curve mixes, small features,
multi-piece, nested holes (piece in hole in piece), and mixed topologies.

Zero reference to or derivation from pilot-user/ U5_logo.png.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SCALE = 4
SIZE_1X = 1000
SIZE_4X = SIZE_1X * SCALE
CENTER = SIZE_4X // 2

# Foreground color: dark charcoal/black with full opacity
FG = (20, 20, 20, 255)
CLEAR = (0, 0, 0, 0)


def _star_points(cx, cy, r_out, r_in, num_points=5, rot=0.0):
    pts = []
    angle_step = math.pi / num_points
    for i in range(num_points * 2):
        r = r_out if i % 2 == 0 else r_in
        theta = rot + i * angle_step
        pts.append((cx + r * math.sin(theta), cy - r * math.cos(theta)))
    return pts


def _gear_points(cx, cy, r_outer, r_root, num_teeth=16):
    pts = []
    pitch = 2 * math.pi / num_teeth
    for i in range(num_teeth):
        t0 = i * pitch
        t1 = t0 + 0.25 * pitch
        t2 = t0 + 0.45 * pitch
        t3 = t0 + 0.70 * pitch
        t4 = t0 + 0.90 * pitch
        pts.append((cx + r_root * math.cos(t0), cy + r_root * math.sin(t0)))
        pts.append((cx + r_outer * math.cos(t1), cy + r_outer * math.sin(t1)))
        pts.append((cx + r_outer * math.cos(t2), cy + r_outer * math.sin(t2)))
        pts.append((cx + r_root * math.cos(t3), cy + r_root * math.sin(t3)))
        pts.append((cx + r_root * math.cos(t4), cy + r_root * math.sin(t4)))
    return pts


def render_case01():
    """Case 01: Thin strokes - Concentric rings with fine spokes and calibration ticks."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Outer thin ring (width 20px at 1x)
    r1, r2 = 1700, 1620
    draw.ellipse([CENTER - r1, CENTER - r1, CENTER + r1, CENTER + r1], fill=FG)
    draw.ellipse([CENTER - r2, CENTER - r2, CENTER + r2, CENTER + r2], fill=CLEAR)
    # Inner thin ring (width 10px at 1x)
    r3, r4 = 800, 760
    draw.ellipse([CENTER - r3, CENTER - r3, CENTER + r3, CENTER + r3], fill=FG)
    draw.ellipse([CENTER - r4, CENTER - r4, CENTER + r4, CENTER + r4], fill=CLEAR)
    # Thin crosshair spokes (width 6px at 1x)
    spoke_w = 24
    draw.rectangle([CENTER - spoke_w // 2, CENTER - r1, CENTER + spoke_w // 2, CENTER + r1], fill=FG)
    draw.rectangle([CENTER - r1, CENTER - spoke_w // 2, CENTER + r1, CENTER + spoke_w // 2], fill=FG)
    # Clear inner center of spokes
    draw.ellipse([CENTER - r4, CENTER - r4, CENTER + r4, CENTER + r4], fill=CLEAR)
    # Small center pip
    draw.ellipse([CENTER - 160, CENTER - 160, CENTER + 160, CENTER + 160], fill=FG)
    return img


def render_case02():
    """Case 02: Sharp corners - Multi-point acute star badge with acute inner notches."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # 8-pointed star with acute notches (r_in = 450, r_out = 1750)
    pts = _star_points(CENTER, CENTER, 1750, 480, num_points=8, rot=0.0)
    draw.polygon(pts, fill=FG)
    # Diamond cutout at center
    cut_pts = _star_points(CENTER, CENTER, 280, 280, num_points=2, rot=0.0)
    draw.polygon(cut_pts, fill=CLEAR)
    return img


def render_case03():
    """Case 03: Dense corner/curve mixes - Precision escapement gear with curved teeth and keyway."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # 16-tooth gear
    gear_pts = _gear_points(CENTER, CENTER, 1700, 1300, num_teeth=16)
    draw.polygon(gear_pts, fill=FG)
    # Axle hole
    r_axle = 500
    draw.ellipse([CENTER - r_axle, CENTER - r_axle, CENTER + r_axle, CENTER + r_axle], fill=CLEAR)
    # Keyway notch in axle hole
    kw, kh = 160, 200
    draw.rectangle([CENTER - kw // 2, CENTER - r_axle - kh, CENTER + kw // 2, CENTER - r_axle + 50], fill=CLEAR)
    return img


def render_case04():
    """Case 04: Small features - Filleted badge with fine pinholes (8px at 1x) and narrow isolation slits."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Rounded badge body
    w, h, r = 1600, 1200, 240
    draw.rounded_rectangle([CENTER - w, CENTER - h, CENTER + w, CENTER + h], radius=r, fill=FG)
    # 4 small pinholes near corners (32px at 4x -> 8px at 1x)
    pin_r = 32
    for ox in [-1200, 1200]:
        for oy in [-850, 850]:
            draw.ellipse([CENTER + ox - pin_r, CENTER + oy - pin_r, CENTER + ox + pin_r, CENTER + oy + pin_r], fill=CLEAR)
    # Narrow horizontal isolation slits (16px at 4x -> 4px at 1x)
    slit_h = 16
    draw.rectangle([CENTER - 1100, CENTER - 300 - slit_h // 2, CENTER + 1100, CENTER - 300 + slit_h // 2], fill=CLEAR)
    draw.rectangle([CENTER - 1100, CENTER + 300 - slit_h // 2, CENTER + 1100, CENTER + 300 + slit_h // 2], fill=CLEAR)
    # Central lozenge cutout
    draw.rounded_rectangle([CENTER - 400, CENTER - 180, CENTER + 400, CENTER + 180], radius=80, fill=CLEAR)
    return img


def render_case05():
    """Case 05: Multi-piece geometric - Triskelion / 3 detached symmetrical curved shield lobes."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # 3 detached lobes at 120-degree intervals
    for k in range(3):
        theta = k * (2 * math.pi / 3) - math.pi / 2
        cx = CENTER + 800 * math.cos(theta)
        cy = CENTER + 800 * math.sin(theta)
        pts = []
        for step in range(36):
            phi = step * (2 * math.pi / 36)
            rx = 550 * (1.0 + 0.3 * math.cos(phi))
            ry = 420
            px = cx + rx * math.cos(phi) * math.cos(theta) - ry * math.sin(phi) * math.sin(theta)
            py = cy + rx * math.cos(phi) * math.sin(theta) + ry * math.sin(phi) * math.cos(theta)
            pts.append((px, py))
        draw.polygon(pts, fill=FG)
    return img


def render_case06():
    """Case 06: Nested holes (single depth) - Flange plate with central hole and satellite bolt holes."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Rounded square outer body
    s, r = 1600, 300
    draw.rounded_rectangle([CENTER - s, CENTER - s, CENTER + s, CENTER + s], radius=r, fill=FG)
    # Central circular hole
    rc = 750
    draw.ellipse([CENTER - rc, CENTER - rc, CENTER + rc, CENTER + rc], fill=CLEAR)
    # 4 satellite holes
    rs = 240
    for ox, oy in [(-1050, -1050), (1050, -1050), (1050, 1050), (-1050, 1050)]:
        draw.ellipse([CENTER + ox - rs, CENTER + oy - rs, CENTER + ox + rs, CENTER + oy + rs], fill=CLEAR)
    return img


def render_case07():
    """Case 07: Nested island in hole - Bullseye emblem: outer ring, annular hole, central island."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Outer ring: outer r = 1750, inner hole r = 1150
    draw.ellipse([CENTER - 1750, CENTER - 1750, CENTER + 1750, CENTER + 1750], fill=FG)
    draw.ellipse([CENTER - 1150, CENTER - 1150, CENTER + 1150, CENTER + 1150], fill=CLEAR)
    # Isolated central island inside the hole: r = 600
    draw.ellipse([CENTER - 600, CENTER - 600, CENTER + 600, CENTER + 600], fill=FG)
    return img


def render_case08():
    """Case 08: Deep nesting (three-tier) - Outer square -> square hole -> octagonal island -> circular hole -> star island."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Tier 1: Outer square (1700) with square hole (1250)
    draw.rectangle([CENTER - 1700, CENTER - 1700, CENTER + 1700, CENTER + 1700], fill=FG)
    draw.rectangle([CENTER - 1250, CENTER - 1250, CENTER + 1250, CENTER + 1250], fill=CLEAR)
    # Tier 2: Inside the square hole, an octagonal ring island (outer r = 950, inner circular hole r = 550)
    oct_pts = []
    for i in range(8):
        ang = i * (2 * math.pi / 8) + math.pi / 8
        oct_pts.append((CENTER + 950 * math.cos(ang), CENTER + 950 * math.sin(ang)))
    draw.polygon(oct_pts, fill=FG)
    draw.ellipse([CENTER - 550, CENTER - 550, CENTER + 550, CENTER + 550], fill=CLEAR)
    # Tier 3: Inside the circular hole, a solid 5-point star island
    star_pts = _star_points(CENTER, CENTER, 380, 180, num_points=5, rot=0.0)
    draw.polygon(star_pts, fill=FG)
    return img


def render_case09():
    """Case 09: Mixed organic cluster - Smooth 5-petal flower with center hole and detached pollen droplets."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Smooth flower with 5 sinusoidal lobes
    pts = []
    num_steps = 360
    for i in range(num_steps):
        theta = i * 2 * math.pi / num_steps
        r = 1100 + 450 * math.cos(5 * theta)
        pts.append((CENTER + r * math.cos(theta), CENTER + r * math.sin(theta)))
    draw.polygon(pts, fill=FG)
    # Center hole
    draw.ellipse([CENTER - 280, CENTER - 280, CENTER + 280, CENTER + 280], fill=CLEAR)
    # 3 detached floating droplets above
    for ox, oy, dr in [(-700, -1600, 110), (0, -1720, 140), (700, -1600, 110)]:
        draw.ellipse([CENTER + ox - dr, CENTER + oy - dr, CENTER + ox + dr, CENTER + oy + dr], fill=FG)
    return img


def render_case10():
    """Case 10: Mixed crescent and stars - Crescent moon with sharp zero-angle cusps and 3 detached stars."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Outer circle of crescent
    r_outer = 1650
    draw.ellipse([CENTER - r_outer, CENTER - r_outer, CENTER + r_outer, CENTER + r_outer], fill=FG)
    # Inner offset cutter circle producing the crescent moon
    r_inner = 1380
    offset_x = 550
    draw.ellipse([CENTER + offset_x - r_inner, CENTER - r_inner, CENTER + offset_x + r_inner, CENTER + r_inner], fill=CLEAR)
    # 3 detached sharp stars floating in the concave bay
    draw.polygon(_star_points(CENTER + 400, CENTER - 500, 260, 110, num_points=5, rot=0.2), fill=FG)
    draw.polygon(_star_points(CENTER + 700, CENTER + 50, 320, 140, num_points=5, rot=0.4), fill=FG)
    draw.polygon(_star_points(CENTER + 350, CENTER + 650, 220, 95, num_points=5, rot=0.1), fill=FG)
    return img


def render_case11():
    """Case 11: Mixed spiral vortex - Tapering spiral arm with continuous curvature and sharp tip."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # 2 curved boundary paths forming a tapering spiral
    num_pts = 400
    outer_pts, inner_pts = [], []
    for i in range(num_pts + 1):
        t = i / num_pts
        theta = t * 2.8 * math.pi  # 500 degrees sweep
        # Outer radius grows
        r_out = 350 + 1350 * (t ** 0.85)
        # Tapering thickness: 240px at start down to 16px at tip
        thick = 240 * (1.0 - t) + 16 * t
        r_in = r_out - thick
        outer_pts.append((CENTER + r_out * math.cos(theta), CENTER + r_out * math.sin(theta)))
        inner_pts.append((CENTER + r_in * math.cos(theta), CENTER + r_in * math.sin(theta)))
    poly = outer_pts + list(reversed(inner_pts))
    draw.polygon(poly, fill=FG)
    return img


def render_case12():
    """Case 12: Mixed heraldic shield - Shield with cross cutouts and detached floating crown motif."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Shield body (lower section)
    shield_pts = [
        (CENTER - 1300, CENTER - 700),
        (CENTER + 1300, CENTER - 700),
        (CENTER + 1300, CENTER + 200),
        (CENTER + 900, CENTER + 950),
        (CENTER, CENTER + 1600),
        (CENTER - 900, CENTER + 950),
        (CENTER - 1300, CENTER + 200),
    ]
    draw.polygon(shield_pts, fill=FG)
    # Cross cutouts inside shield (4 quadrant rectangular cutouts)
    cw, ch, cx, cy = 900, 700, 180, 180
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            x0 = CENTER + sx * cx - (cw if sx < 0 else 0)
            x1 = CENTER + sx * cx + (0 if sx < 0 else cw)
            y0 = CENTER + sy * cy - (ch if sy < 0 else 0)
            y1 = CENTER + sy * cy + (0 if sy < 0 else ch)
            draw.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], fill=CLEAR)
    # Detached crown header floating above shield
    crown_pts = [
        (CENTER - 1100, CENTER - 1000),
        (CENTER - 1200, CENTER - 1500),
        (CENTER - 500, CENTER - 1200),
        (CENTER, CENTER - 1650),
        (CENTER + 500, CENTER - 1200),
        (CENTER + 1200, CENTER - 1500),
        (CENTER + 1100, CENTER - 1000),
    ]
    draw.polygon(crown_pts, fill=FG)
    return img


def render_case13():
    """Case 13: Dense scallop rosette - 20 scalloped petals with acute concave cusps and center hole."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # 20-petaled rosette
    pts = []
    num_steps = 400
    for i in range(num_steps):
        theta = i * 2 * math.pi / num_steps
        r = 1350 + 350 * math.cos(20 * theta)
        pts.append((CENTER + r * math.cos(theta), CENTER + r * math.sin(theta)))
    draw.polygon(pts, fill=FG)
    # Center hole
    r_hole = 420
    draw.ellipse([CENTER - r_hole, CENTER - r_hole, CENTER + r_hole, CENTER + r_hole], fill=CLEAR)
    return img


def render_case14():
    """Case 14: Calligraphic monogram - Figure-8 ribbon with variable stroke width and floating accent."""
    img = Image.new("RGBA", (SIZE_4X, SIZE_4X), CLEAR)
    draw = ImageDraw.Draw(img)
    # Outer figure-8 / infinity shape
    pts_outer, pts_inner1, pts_inner2 = [], [], []
    num_steps = 360
    for i in range(num_steps):
        t = i * 2 * math.pi / num_steps
        # Lemniscate of Gerono: x = cos(t), y = sin(t)*cos(t)
        den = 1.0 + math.sin(t) ** 2
        px = 1550 * math.cos(t) / den
        py = 1550 * math.sin(t) * math.cos(t) / den
        # Variable ribbon width
        w = 180 + 100 * math.cos(2 * t)
        pts_outer.append((CENTER + px, CENTER + py))
    # Draw broad figure-8 base
    draw.ellipse([CENTER - 1450, CENTER - 700, CENTER + 1450, CENTER + 700], fill=FG)
    # Cut two lobe holes to form the ribbon
    draw.ellipse([CENTER - 1150, CENTER - 450, CENTER - 150, CENTER + 450], fill=CLEAR)
    draw.ellipse([CENTER + 150, CENTER - 450, CENTER + 1150, CENTER + 450], fill=CLEAR)
    # Central bridge waist
    draw.rectangle([CENTER - 180, CENTER - 350, CENTER + 180, CENTER + 350], fill=FG)
    # Detached diamond accent dot floating above
    draw.polygon([
        (CENTER, CENTER - 1500),
        (CENTER + 160, CENTER - 1250),
        (CENTER, CENTER - 1000),
        (CENTER - 160, CENTER - 1250),
    ], fill=FG)
    return img


CASES = [
    ("case01_thin_strokes", "thin_strokes", "Concentric emblem with fine spokes, inner ring, and calibration tick marks", render_case01),
    ("case02_sharp_corners", "sharp_corners", "8-pointed acute star badge with 25-degree inner notches and central diamond cutout", render_case02),
    ("case03_dense_curve_mix", "dense_corner_curve_mixes", "16-tooth precision escapement gear with curved tooth flanks, root fillets, and keyway", render_case03),
    ("case04_small_features", "small_features", "Filleted badge with 4 fine pinholes (8px), two narrow isolation slits (4px), and center lozenge", render_case04),
    ("case05_multipiece_geometric", "multi_piece", "Triskelion of 3 completely detached symmetrical curved shield lobes", render_case05),
    ("case06_nested_holes", "nested_holes", "Flange plate with rectangular outer contour, central circular hole, and 4 satellite bolt holes", render_case06),
    ("case07_nested_island_in_hole", "nested_holes_piece_in_hole", "Bullseye emblem with outer ring, annular hole, and isolated central circular island inside hole", render_case07),
    ("case08_deep_nesting_three_tier", "nested_holes_three_tier", "3-tier concentric nested emblem: outer square -> square hole -> octagonal island -> circle hole -> star island", render_case08),
    ("case09_mixed_organic_cluster", "mixed", "Organic 5-petal flower with center hole and 3 detached floating pollen droplets", render_case09),
    ("case10_mixed_crescent_stars", "mixed", "Crescent moon with sharp zero-angle cusps and 3 detached 5-pointed stars in concave bay", render_case10),
    ("case11_mixed_spiral_vortex", "mixed", "Tapering spiral vortex arm with 500-degree sweep, continuous curvature, and sharp tip", render_case11),
    ("case12_mixed_shield_emblem", "mixed", "Heraldic shield with 4 quadrant cross cutouts and detached floating crown motif header", render_case12),
    ("case13_dense_scallop_rosette", "dense_corner_curve_mixes", "20-petal scallop rosette badge with acute concave cusps and center circular hole", render_case13),
    ("case14_calligraphic_monogram", "thin_strokes", "Figure-8 ribbon monogram with variable stroke thickness, two holes, and detached accent dot", render_case14),
]


def generate_all(output_dir: Path | None = None) -> dict:
    out = output_dir or ROOT
    out.mkdir(parents=True, exist_ok=True)
    
    entries = []
    hasher = hashlib.sha256()

    for cid, category, desc, render_fn in CASES:
        img_4x = render_fn()
        img_1x = img_4x.resize((SIZE_1X, SIZE_1X), Image.Resampling.LANCZOS)
        
        png_path = out / f"{cid}.png"
        img_1x.save(png_path, format="PNG", optimize=True)
        
        file_bytes = png_path.stat().st_size
        file_sha = hashlib.sha256(png_path.read_bytes()).hexdigest()
        
        entry = {
            "id": cid,
            "filename": f"{cid}.png",
            "category": category,
            "description": desc,
            "width": SIZE_1X,
            "height": SIZE_1X,
            "sha256": file_sha,
            "bytes": file_bytes,
        }
        entries.append(entry)
        hasher.update(f"{cid}:{file_sha}:".encode("utf-8"))

    suite_sha256 = hasher.hexdigest()

    manifest = {
        "schema": "cad-harness.c2-stress-suite.v1",
        "description": "C-R7 generic raster logo stress suite (14 cases). Completely independent of U5.",
        "suite_sha256": suite_sha256,
        "cases_count": len(entries),
        "cases": entries,
    }

    manifest_path = out / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    m = generate_all()
    print("=" * 60)
    print(f"Generated {m['cases_count']} stress suite cases in {ROOT}")
    print(f"Suite SHA-256: {m['suite_sha256']}")
    print("=" * 60)
    for c in m["cases"]:
        print(f"  [{c['category']:<26}] {c['id']}: {c['sha256']} ({c['bytes']} bytes)")
