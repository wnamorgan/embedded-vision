#!/usr/bin/env python3
"""
YOLO dataset reviewer (one argument).

Expected dataset structure:
  <dataset>/
    images/...
    labels/...
    classes.txt   (optional; one class name per line)

Usage:
  python3 review_yolo.py            # uses current working directory as dataset root
  python3 review_yolo.py /path/to/dataset

Keys:
  y = good (next)
  n = bad  (add to bad list, next)
  q / ESC = quit

After running program, the files can be examined in various environments
 - Linux CL Viewer: feh <filename.jpg>
 - Label Studio: Filter → Data → image → contains → <filename.jpg>

"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def load_classes(dataset_root: Path) -> Optional[List[str]]:
    p = dataset_root / "classes.txt"
    if not p.exists():
        return None
    lines = [ln.strip() for ln in p.read_text().splitlines()]
    lines = [ln for ln in lines if ln]
    return lines if lines else None


def gather_images(images_dir: Path) -> List[Path]:
    imgs = [p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXTS]
    imgs.sort()
    return imgs


def label_path_for_image(img_path: Path, images_dir: Path, labels_dir: Path) -> Path:
    rel = img_path.relative_to(images_dir)
    return labels_dir / rel.with_suffix(".txt")


def parse_yolo_label_file(label_file: Path) -> List[Tuple[int, float, float, float, float]]:
    if not label_file.exists():
        return []
    out: List[Tuple[int, float, float, float, float]] = []
    for ln in label_file.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split()
        if len(parts) < 5:
            continue
        cls = int(float(parts[0]))
        cx, cy, w, h = map(float, parts[1:5])
        out.append((cls, cx, cy, w, h))
    return out


def yolo_to_xyxy(cx: float, cy: float, w: float, h: float, W: int, H: int):
    x1 = int(round((cx - w / 2.0) * W))
    y1 = int(round((cy - h / 2.0) * H))
    x2 = int(round((cx + w / 2.0) * W))
    y2 = int(round((cy + h / 2.0) * H))
    x1 = max(0, min(W - 1, x1))
    y1 = max(0, min(H - 1, y1))
    x2 = max(0, min(W - 1, x2))
    y2 = max(0, min(H - 1, y2))
    return x1, y1, x2, y2


def draw_boxes(img, labels, classes: Optional[List[str]]):
    H, W = img.shape[:2]
    for cls, cx, cy, bw, bh in labels:
        x1, y1, x2, y2 = yolo_to_xyxy(cx, cy, bw, bh, W, H)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        text = str(cls)
        if classes and 0 <= cls < len(classes):
            text = f"{cls}:{classes[cls]}"

        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        y_top = max(0, y1 - th - 8)
        cv2.rectangle(img, (x1, y_top), (x1 + tw + 6, y1), (0, 255, 0), -1)
        cv2.putText(img, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)


def main() -> int:
    dataset_root = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd()

    images_dir = dataset_root / "images"
    labels_dir = dataset_root / "labels"

    if not images_dir.exists():
        print(f"ERROR: missing images/ directory at: {images_dir}", file=sys.stderr)
        return 2
    if not labels_dir.exists():
        print(f"ERROR: missing labels/ directory at: {labels_dir}", file=sys.stderr)
        return 2

    classes = load_classes(dataset_root)
    images = gather_images(images_dir)
    if not images:
        print(f"ERROR: no images found under: {images_dir}", file=sys.stderr)
        return 2

    bad: List[str] = []

    win = "YOLO Review (y=good, n=bad, q=quit)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    i = 0
    while i < len(images):
        img_path = images[i]
        lbl_path = label_path_for_image(img_path, images_dir, labels_dir)

        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            print(f"WARN: could not read image: {img_path}", file=sys.stderr)
            i += 1
            continue

        labels = parse_yolo_label_file(lbl_path)
        vis = img.copy()
        draw_boxes(vis, labels, classes)

        rel = img_path.relative_to(images_dir).as_posix()
        title = f"[{i+1}/{len(images)}] {rel} | labels={len(labels)} | y=good n=bad q=quit"
        cv2.setWindowTitle(win, title)
        cv2.imshow(win, vis)

        key = cv2.waitKey(0) & 0xFF
        if key in (ord("q"), 27):  # q or ESC
            break
        if key == ord("n"):
            bad.append(rel)
            i += 1
            continue
        if key == ord("y"):
            i += 1
            continue
        # any other key: ignore and stay on same image

    cv2.destroyAllWindows()

    print("\n=== BAD LIST (relative to images/) ===")
    for p in bad:
        print(p)
    print(f"=== TOTAL BAD: {len(bad)} / {len(images)} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
