import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
DIST = HERE / "dist"
ICON_FILE = HERE / "icon.ico"


def generate_icon():
    from PIL import Image, ImageDraw, ImageFont

    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            (2, 2, s - 2, s - 2), radius=max(4, s // 6), fill=(99, 102, 241, 255)
        )
        draw.rounded_rectangle(
            (s // 6, s // 6, s - s // 6, s - s // 6),
            radius=max(2, s // 10),
            fill=(255, 255, 255, 30),
        )
        try:
            font_size = max(10, s // 2)
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "M", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (s - tw) / 2 - bbox[0]
        y = (s - th) / 2 - bbox[1] - 1
        draw.text((x, y), "M", fill="white", font=font)
        images.append(img)

    images[0].save(
        ICON_FILE,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"[build] Icon saved: {ICON_FILE}")


def build():
    print("[build] Generating icon...")
    generate_icon()

    if DIST.exists():
        shutil.rmtree(DIST)
        print("[build] Cleaned dist/")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "Muktadha",
        f"--icon={ICON_FILE}",
        "--add-data", f"config.json{';' if sys.platform == 'win32' else ':'}.",
        str(HERE / "muktadha.py"),
    ]
    print(f"[build] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    out_dir = DIST
    print(f"[build] Output: {out_dir}")
    print(f"[build] Files: {[p.name for p in sorted(out_dir.iterdir())]}")
    print(f"[build] Config auto-created in %APPDATA%\\Muktadha on first run")


if __name__ == "__main__":
    build()
