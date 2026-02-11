from pathlib import Path

try:
    from PIL import Image
except Exception:
    print("Pillow not installed. To generate favicon: pip install pillow")
    raise SystemExit(0)

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "src" / "agent" / "static" / "logo.png"
out = ROOT / "src" / "agent" / "static" / "favicon.ico"

out.parent.mkdir(parents=True, exist_ok=True)

img = Image.open(src).convert("RGBA")
sizes = [(16,16), (32,32), (48,48), (64,64)]
img.save(out, format="ICO", sizes=sizes)

print("OK:", out)
