from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def main(out_path: str, title: str, artist: str, size: int = 3000) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (size, size), color=(10, 10, 14))
    draw = ImageDraw.Draw(img)

    # Systemfont fallback (ohne externe Fonts)
    try:
        font_title = ImageFont.truetype("arial.ttf", 120)
        font_artist = ImageFont.truetype("arial.ttf", 70)
    except:
        font_title = ImageFont.load_default()
        font_artist = ImageFont.load_default()

    margin = 180
    draw.text((margin, margin), artist, fill=(220, 220, 230), font=font_artist)
    draw.text((margin, margin + 140), title, fill=(240, 240, 245), font=font_title)

    # Minimaler Akzentbalken
    draw.rectangle([margin, size - 260, size - margin, size - 220], fill=(80, 80, 95))

    img.save(out_path, quality=95)
    print(f"Cover written: {out_path}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--artist", required=True)
    p.add_argument("--size", type=int, default=3000)
    args = p.parse_args()
    main(args.out, args.title, args.artist, args.size)
