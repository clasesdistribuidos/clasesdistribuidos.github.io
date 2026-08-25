#!/usr/bin/env python3
"""Arma una hoja de contactos con los recortes de una clase.

    python3 scripts/hoja_de_contactos.py --clase 3

Escribe una sola imagen con todos los recortes de `assets/clase-NN/` en
miniatura y rotulados, y la deja en un archivo temporal. Existe porque
revisando recorte por recorte los errores se pasan por alto: lo que salta
mirando la grilla entera de una es el recorte que se llevó la etiqueta de la
figura de al lado, el que cortó un subíndice, o el que quedó vacío.

Andamio, no parte del sitio: `scripts/` está excluido del build.
"""

import argparse
import glob
import os
import tempfile

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COLUMNAS = 4
CELDA = 330  # lado de la miniatura, en px
PIE = 26     # alto de la banda del rótulo


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clase", type=int, required=True)
    ap.add_argument("--salida", help="dónde escribirla (default: un temporal)")
    args = ap.parse_args()

    origen = os.path.join(REPO, "assets", f"clase-{args.clase:02d}")
    rutas = sorted(glob.glob(os.path.join(origen, "*.png"))
                   + glob.glob(os.path.join(origen, "*.jpg")))
    if not rutas:
        raise SystemExit(f"no hay recortes en {origen}")

    filas = (len(rutas) + COLUMNAS - 1) // COLUMNAS
    hoja = Image.new("RGB", (COLUMNAS * CELDA, filas * (CELDA + PIE)), "white")
    pincel = ImageDraw.Draw(hoja)

    for i, ruta in enumerate(rutas):
        im = Image.open(ruta).convert("RGB")
        im.thumbnail((CELDA - 12, CELDA - 12))
        cx = (i % COLUMNAS) * CELDA
        cy = (i // COLUMNAS) * (CELDA + PIE)
        hoja.paste(im, (cx + (CELDA - im.width) // 2, cy + (CELDA - im.height) // 2))
        # El marco ayuda a ver cuánto aire le quedó al recorte adentro de la celda.
        pincel.rectangle([cx + 2, cy + 2, cx + CELDA - 3, cy + CELDA - 3],
                         outline=(210, 210, 210))
        pincel.text((cx + 8, cy + CELDA + 4),
                    f"{i + 1:2d}. {os.path.splitext(os.path.basename(ruta))[0]}",
                    fill=(0, 0, 0))

    salida = args.salida or os.path.join(
        tempfile.mkdtemp(prefix=f"contactos-clase{args.clase}-"), "contactos.png")
    hoja.save(salida)
    print(f"{salida}  ({len(rutas)} recortes, {hoja.width}x{hoja.height})")


if __name__ == "__main__":
    main()
