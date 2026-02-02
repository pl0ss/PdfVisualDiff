#!/usr/bin/env python3

import argparse
import os

import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFilter


CONTENT_ONLY = True  # True = nur Inhalt vergleichen, False = kompletter Diff

# ----------------------------
# Argumente (CLI)
# ----------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Visueller Vergleich von PDF-Dateien auf Pixelebene"
    )

    parser.add_argument("pdf1", help="erste PDF-Datei")
    parser.add_argument("pdf2", help="zweite PDF-Datei")

    parser.add_argument(
        "--out",
        default="diff_out",
        help="Output-Verzeichnis (Standard: diff_out)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Render-Auflösung (Standard: 300)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=200,
        help="Schwellwert für Binarisierung (Standard: 200)",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--content-only",
        action="store_true",
        help="nur schwarzen Inhalt vergleichen (Hintergrund bleibt weiß)",
    )
    mode.add_argument(
        "--full",
        action="store_true",
        help="kompletter Bildvergleich (inkl. Hintergrund)",
    )

    return parser.parse_args()

# ----------------------------
# Vorverarbeitung
# ----------------------------
def preprocess(img, threshold):
    img = img.convert("L")  # Graustufen
    img = img.filter(ImageFilter.MedianFilter(size=3))  # leichtes Entrauschen
    img = img.point(lambda x: 0 if x < threshold else 255)  # binär
    return img

# ----------------------------
# Diff-Logik
# ----------------------------
def diff_image(img1, img2, content_only=True):
    a = np.array(img1)
    b = np.array(img2)

    if a.shape != b.shape:
        raise ValueError("Seitengrößen stimmen nicht überein")

    h, w = a.shape
    out = np.ones((h, w, 3), dtype=np.uint8) * 255  # weißer Hintergrund

    same_black = (a == 0) & (b == 0)
    only1 = (a == 0) & (b == 255)
    only2 = (a == 255) & (b == 0)

    if content_only:
        out[same_black] = [0, 0, 0]       # identischer Inhalt
        out[only1] = [255, 0, 0]          # nur PDF 1
        out[only2] = [0, 255, 0]          # nur PDF 2
    else:
        same = (a == b)
        out[same] = [0, 0, 0]
        out[only1] = [255, 0, 0]
        out[only2] = [0, 255, 0]

    return Image.fromarray(out)

# ----------------------------
# Main
# ----------------------------
def main():
    args = parse_args()

    content_only = True
    if args.full:
        content_only = False
    if args.content_only:
        content_only = True

    os.makedirs(args.out, exist_ok=True)

    imgs1 = convert_from_path(args.pdf1, dpi=args.dpi)
    imgs2 = convert_from_path(args.pdf2, dpi=args.dpi)

    if len(imgs1) != len(imgs2):
        raise ValueError("PDFs haben unterschiedliche Seitenanzahl")

    total_pages = len(imgs1)

    for i, (p1, p2) in enumerate(zip(imgs1, imgs2), start=1):
        print(f"Seite {i} von {total_pages}")

        i1 = preprocess(p1, args.threshold)
        i2 = preprocess(p2, args.threshold)

        diff = diff_image(i1, i2, content_only)
        diff.save(os.path.join(args.out, f"diff_page_{i}.png"))

    print(f"Fertig; Diff-Bilder liegen in: {args.out}")


if __name__ == "__main__":
    main()