"""
make_icons.py
-------------
Generates platform-native icon files from assets/img/converter.png:

  assets/img/converter.icns  – macOS (.app dock icon)
  assets/img/converter.ico   – Windows (.exe / installer icon)

Requirements:
  pip install pillow

Usage:
  python make_icons.py
"""

import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install pillow")

ROOT = Path(__file__).parent
SRC  = ROOT / "assets" / "img" / "app.png"
ICNS = ROOT / "assets" / "img" / "app.icns"
ICO  = ROOT / "assets" / "img" / "app.ico"

ICO_SIZES  = [16, 32, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]

# Maps pixel size → ICNS OSType tag
_ICNS_TAG = {
    16:   b"icp4",
    32:   b"icp5",
    64:   b"icp6",
    128:  b"ic07",
    256:  b"ic08",
    512:  b"ic09",
    1024: b"ic10",
}


# ---------------------------------------------------------------------------
# .ico
# ---------------------------------------------------------------------------

def make_ico(src: Path, dst: Path) -> None:
    img = Image.open(src).convert("RGBA")
    resized = [img.resize((s, s), Image.LANCZOS) for s in ICO_SIZES]
    resized[0].save(
        dst, format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=resized[1:],
    )
    print(f"  created  {dst.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# .icns  (pure-Python fallback when iconutil is unavailable, e.g. on Windows)
# ---------------------------------------------------------------------------

def _png_bytes(img: Image.Image, size: int) -> bytes:
    """Return raw PNG bytes for *img* resized to *size*×*size*."""
    import io
    buf = io.BytesIO()
    img.resize((size, size), Image.LANCZOS).save(buf, format="PNG")
    return buf.getvalue()


def _make_icns_pure(src: Path, dst: Path) -> None:
    """Write an ICNS file without relying on macOS iconutil."""
    img = Image.open(src).convert("RGBA")
    chunks: list[bytes] = []
    for size in ICNS_SIZES:
        tag  = _ICNS_TAG[size]
        data = _png_bytes(img, size)
        # Each chunk: 4-byte OSType + 4-byte length (includes 8-byte header)
        chunks.append(tag + struct.pack(">I", len(data) + 8) + data)

    body   = b"".join(chunks)
    header = b"icns" + struct.pack(">I", len(body) + 8)
    dst.write_bytes(header + body)
    print(f"  created  {dst.relative_to(ROOT)}  (pure-Python)")


def make_icns(src: Path, dst: Path) -> None:
    """Use macOS iconutil when available, otherwise fall back to pure Python."""
    if shutil.which("iconutil"):
        tmp = Path(tempfile.mkdtemp()) / "converter.iconset"
        tmp.mkdir()
        img = Image.open(src).convert("RGBA")

        spec = [
            (16,   "icon_16x16.png"),
            (32,   "icon_16x16@2x.png"),
            (32,   "icon_32x32.png"),
            (64,   "icon_32x32@2x.png"),
            (128,  "icon_128x128.png"),
            (256,  "icon_128x128@2x.png"),
            (256,  "icon_256x256.png"),
            (512,  "icon_256x256@2x.png"),
            (512,  "icon_512x512.png"),
            (1024, "icon_512x512@2x.png"),
        ]
        for size, name in spec:
            img.resize((size, size), Image.LANCZOS).save(tmp / name, format="PNG")

        subprocess.run(
            ["iconutil", "-c", "icns", str(tmp), "-o", str(dst)],
            check=True,
        )
        shutil.rmtree(tmp.parent)
        print(f"  created  {dst.relative_to(ROOT)}  (iconutil)")
    else:
        _make_icns_pure(src, dst)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not SRC.exists():
        sys.exit(f"Source image not found: {SRC}")

    print("Generating icons from", SRC.relative_to(ROOT))
    make_ico(SRC, ICO)
    make_icns(SRC, ICNS)
    print("Done.")


if __name__ == "__main__":
    main()
