#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

MAGICK_CMD = "magick {source}[0] -auto-orient -colorspace sRGB -resize x2160> -strip -quality 75 {dest}"


def normalize_name(path: Path) -> str:
    return re.sub(r"([^0-9_]+|_\d+$)", "", path.stem.casefold()).strip("_")


def get_sources(folder: str) -> Iterable[Path]:
    for path in Path(folder).iterdir():
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            yield path


def patch_index(root: Path, image_root: Path) -> None:
    images = [str(path.stem) for path in image_root.iterdir() if path.suffix == ".webp"]
    index = root / "index.html"
    source = index.read_text(encoding="utf-8")
    patched = re.sub(r"(?<=const images = )\[.*?\](?=;)", json.dumps(sorted(images)), source)
    index.write_text(patched, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2 or len(set(sys.argv) & {"-h", "--help"}) != 0:
        print("Usage: Run `setup-images.py path/to/images` in a directory with index.html and images/")
    else:
        root = Path(os.getcwd())
        image_root = root / "images"
        sources: dict[str, tuple[Path, Path]] = {}
        for folder in sys.argv[1:]:
            for source in get_sources(folder):
                key = normalize_name(source)
                dest = image_root / (key + ".webp")
                if dest.exists():
                    continue
                if key in sources:
                    print("Multiple sources found for", key)
                sources[key] = (source, dest)
        for idx, (source, dest) in enumerate(sources.values(), 1):
            print(f"Processing {idx:>3}/{len(sources)} {source}")
            subprocess.run(MAGICK_CMD.format(source=source, dest=dest).split(), check=True)
        patch_index(root, image_root)


if __name__ == "__main__":
    main()
