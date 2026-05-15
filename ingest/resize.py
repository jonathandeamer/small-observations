"""Resize a JPEG to a web-friendly size, preserving aspect ratio.

Never upscales — if the source is already smaller than max_dim, it's copied
through unchanged (still re-encoded at the target quality).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def to_web(src: Path, dst: Path, *, max_dim: int, quality: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB")
        long_edge = max(img.size)
        if long_edge > max_dim:
            scale = max_dim / long_edge
            new_size = (round(img.size[0] * scale), round(img.size[1] * scale))
            img = img.resize(new_size, Image.LANCZOS)
        img.save(dst, format="JPEG", quality=quality, optimize=True, progressive=True)
