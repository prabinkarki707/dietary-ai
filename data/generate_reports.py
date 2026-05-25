"""
generate_reports.py — §3.3: Render each profile into a synthetic medical report PNG.
Uses Pillow to generate templated report images for OCR testing.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

PROFILES_PATH = ROOT / "data" / "profiles.json"
OUTPUT_DIR = ROOT / "data" / "synthetic_reports"
OUTPUT_DIR.mkdir(exist_ok=True)

BG_COLOR = (255, 255, 255)
HEADER_COLOR = (28, 28, 30)
ACCENT_COLOR = (0, 122, 255)
TEXT_COLOR = (44, 44, 46)
LINE_COLOR = (198, 198, 200)
VALUE_COLOR = (99, 99, 102)

W, H = 900, 1100
MARGIN = 60


def _try_font(size: int) -> ImageFont.ImageFont:
    for name in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_profile(profile: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_h1 = _try_font(22)
    font_h2 = _try_font(16)
    font_body = _try_font(14)
    font_small = _try_font(12)
    font_label = _try_font(13)

    y = MARGIN

    # Header
    draw.rectangle([0, 0, W, 80], fill=(0, 122, 255))
    draw.text((MARGIN, 24), "SYNTHETIC MEDICAL REPORT", font=_try_font(18), fill=(255, 255, 255))
    draw.text((W - MARGIN - 180, 28), "For Research Use Only", font=font_small, fill=(200, 220, 255))
    y = 100

    # Patient info
    draw.text((MARGIN, y), f"Patient ID: {profile['id']}", font=font_h2, fill=HEADER_COLOR)
    y += 28
    draw.text((MARGIN, y), f"Name: {profile['name']}", font=font_body, fill=TEXT_COLOR)
    y += 22
    draw.text((MARGIN, y), f"Date: 2026-05-24 (SYNTHETIC — NO REAL DATA)", font=font_small, fill=VALUE_COLOR)
    y += 30

    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=LINE_COLOR, width=1)
    y += 20

    # Section: Lab Results
    draw.text((MARGIN, y), "LABORATORY RESULTS", font=_try_font(15), fill=ACCENT_COLOR)
    y += 28

    lab_rows = [
        ("HbA1c", f"{profile.get('hba1c', '—')} mmol/mol", "Ref: 20–42 mmol/mol"),
        ("Fasting Glucose", f"{profile.get('glucose_fasting', '—')} mmol/L", "Ref: 3.9–5.5 mmol/L"),
        ("eGFR", f"{profile.get('egfr', '—')} mL/min/1.73m²", "Ref: ≥60 mL/min/1.73m²"),
        ("Potassium (K+)", f"{profile.get('potassium', '—')} mmol/L", "Ref: 3.5–5.0 mmol/L"),
    ]

    for label, value, ref in lab_rows:
        draw.text((MARGIN, y), label, font=font_label, fill=TEXT_COLOR)
        draw.text((MARGIN + 220, y), value, font=font_body, fill=HEADER_COLOR)
        draw.text((MARGIN + 420, y), ref, font=font_small, fill=VALUE_COLOR)
        y += 24
        draw.line([(MARGIN, y), (W - MARGIN, y)], fill=(242, 242, 247), width=1)
        y += 6

    y += 14
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=LINE_COLOR, width=1)
    y += 20

    # Section: Vital Signs
    draw.text((MARGIN, y), "VITAL SIGNS", font=_try_font(15), fill=ACCENT_COLOR)
    y += 28

    bp_sys = profile.get("bp_systolic", "—")
    bp_dia = profile.get("bp_diastolic", "—")
    draw.text((MARGIN, y), "Blood Pressure (BP)", font=font_label, fill=TEXT_COLOR)
    draw.text((MARGIN + 220, y), f"{bp_sys}/{bp_dia} mmHg", font=font_body, fill=HEADER_COLOR)
    draw.text((MARGIN + 420, y), "Ref: <140/90 mmHg", font=font_small, fill=VALUE_COLOR)
    y += 32

    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=LINE_COLOR, width=1)
    y += 20

    # Section: Active Conditions
    draw.text((MARGIN, y), "ACTIVE CONDITIONS", font=_try_font(15), fill=ACCENT_COLOR)
    y += 28

    conditions = profile.get("conditions", [])
    if conditions:
        for c in conditions:
            draw.text((MARGIN, y), f"• {c.title()}", font=font_body, fill=TEXT_COLOR)
            y += 24
    else:
        draw.text((MARGIN, y), "No active conditions recorded.", font=font_body, fill=VALUE_COLOR)
        y += 24

    y += 10
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=LINE_COLOR, width=1)
    y += 20

    # Section: Allergens
    draw.text((MARGIN, y), "KNOWN ALLERGENS", font=_try_font(15), fill=ACCENT_COLOR)
    y += 28
    allergens = profile.get("allergens", [])
    if allergens:
        for a in allergens:
            draw.text((MARGIN, y), f"⚠ {a.upper()}", font=font_body, fill=(204, 31, 23))
            y += 24
    else:
        draw.text((MARGIN, y), "None reported.", font=font_body, fill=VALUE_COLOR)
        y += 24

    # Footer
    draw.rectangle([0, H - 50, W, H], fill=(242, 242, 247))
    draw.text((MARGIN, H - 35), "⚕ SYNTHETIC DATA ONLY — FOR ACADEMIC RESEARCH · COM6016M Dissertation · Prabin Karki", font=font_small, fill=VALUE_COLOR)

    return img


def generate_all():
    with open(PROFILES_PATH) as f:
        profiles = json.load(f)

    for p in profiles:
        img = render_profile(p)
        out = OUTPUT_DIR / f"{p['id']}_report.png"
        img.save(out, "PNG")
        print(f"Saved: {out}")

    print(f"\nGenerated {len(profiles)} synthetic report images in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all()
