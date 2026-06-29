# Build poster assets: render paper figures (PDF->PNG @300dpi) and generate QR codes.
# Run: uv run --with pymupdf --with segno python build_assets.py
import os
import shutil

import fitz
import segno

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "latex", "figures")
DST = os.path.join(HERE, "assets")
os.makedirs(DST, exist_ok=True)

for name in ["teaser-overview", "speedup_comparison", "demand_supply_multiline", "cross_benchmark_correlation"]:
    doc = fitz.open(os.path.join(SRC, f"{name}.pdf"))
    doc[0].get_pixmap(dpi=300).save(os.path.join(DST, f"{name}.png"))
    doc.close()
    print(f"rendered {name}.png")

shutil.copy(os.path.join(SRC, "leaderboard.png"), os.path.join(DST, "leaderboard.png"))
print("copied leaderboard.png")

qrs = {
    "qr-github": "https://github.com/allenai/vla-evaluation-harness",
    "qr-arxiv": "https://arxiv.org/abs/2603.13966",
    "qr-leaderboard": "https://allenai.github.io/vla-evaluation-harness/leaderboard",
}
for fn, url in qrs.items():
    segno.make(url, error="m").save(os.path.join(DST, f"{fn}.svg"), scale=12, border=1, dark="#13315c")
    print(f"generated {fn}.svg")

print("done")
