#!/usr/bin/env python3
"""Recorta las figuras de una clase desde la pizarra y los scans manuscritos.

Las figuras del apunte salen de dos fuentes que viven en el repo de trabajo
(`clases-apuntes`, al lado de este): la pizarra virtual que el profesor dibujó
en vivo (`raw/claseN/pizarra.pdf`) y los scans de las notas que preparó antes
(`raw/claseN/notas/pagina-NN.jpg`). Cada página trae varias figuras, así que
hay que recortarlas de a una.

Las cajas de recorte se escriben a mano, mirando las páginas. Están en el
espacio de coordenadas de la pizarra renderizada a 150 dpi (1241x1754), que es
un tamaño cómodo para leer coordenadas de un render con grilla; el render de
trabajo es a 300 dpi y el script escala las cajas solo. Las cajas de los scans
están en las coordenadas nativas del jpg.

La caja no tiene que ser precisa: después de recortar, el script ciñe el
resultado al contenido real y le deja un margen parejo. Lo que sí importa es
que no se cuele texto vecino, y para eso está `borrar`.

    python3 scripts/recortar_figuras.py

Regenera todo `assets/clase-01/`. Es idempotente: se puede correr de nuevo
después de tocar una caja.

    python3 scripts/recortar_figuras.py --grilla

Escribe en un directorio temporal cada página de la pizarra y de las notas con
una grilla de coordenadas encima, rotulada en el mismo espacio en el que se
escriben las cajas. Es el paso previo: se miran esas páginas, se leen las
coordenadas de cada figura y recién ahí se llena la tabla de acá abajo.

Hace falta `pdftoppm` (poppler) además de Pillow y numpy.
"""

import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APUNTES = os.path.join(os.path.dirname(REPO), "clases-apuntes", "raw", "clase1")
DESTINO = os.path.join(REPO, "assets", "clase-01")

ANCHO_MAX = 1400  # el ancho de la columna del theme es bastante menor
DPI = 300         # el doble de las coordenadas de las cajas

# nombre, (fuente, página), caja, ceñir, [rectángulos a borrar]
#
# Los rectángulos a borrar tapan texto que quedó dentro de la caja pero no es
# parte de la figura: títulos de la pizarra que el apunte ya dice con palabras.
FIGURAS = [
    ("sistema-interfaz-entorno",       ("pizarra", 1),  (309, 245, 1088, 730),   True),
    ("memoria-dispositivos",           ("pizarra", 2),  (417, 452, 1241, 905),   True),
    ("interprete-estructura",          ("pizarra", 3),  (355, 950, 1015, 1320),  True),
    ("enlace-dos-nodos",               ("pizarra", 4),  (800, 40, 1100, 265),    True),
    ("capas-osi-tcpip-materia",        ("pizarra", 4),  (30, 395, 1235, 950),    True),
    ("multiprocesador-vs-distribuido", ("pizarra", 5),  (60, 70, 1040, 580),     True),
    ("clusters",                       ("pizarra", 6),  (150, 190, 1105, 1490),  True),
    ("titanic-inundacion",             ("pizarra", 7),  (145, 40, 1075, 845),    True),
    ("aws-s3-comunicado",              ("pizarra", 9),  (50, 215, 1180, 555),    True),
    # La pizarra pág. 8 quedó sin dibujo: el monigote está solo en las notas.
    ("transparencia-usuario",          ("notas", 3),    (420, 1550, 870, 1770),  False),
    ("nfs-arquitectura",               ("pizarra", 10), (150, 90, 1210, 690),    True),
    ("cliente-servicio-p2p",           ("pizarra", 11), (55, 20, 1215, 450),     True),
    # En la pizarra (pág. 13) el diagrama quedó apretado contra la figura del
    # libro; el de las notas es el mismo dibujo pero legible.
    ("servidor-de-tiempo",             ("notas", 4),    (620, 1520, 1250, 2010), False),
    ("http-cliente-servidor",          ("pizarra", 14), (240, 30, 730, 355),     True),
    ("load-balancer",                  ("pizarra", 14), (60, 370, 900, 875),     True,
     [(0, 370, 300, 465),                                      # "en la realidad"
      (700, 800, 900, 900)]),                                  # separador de secciones
    ("replicacion-lecturas",           ("pizarra", 14), (55, 935, 1010, 1500),   True),
    ("rpc-middleware-capas",           ("pizarra", 15), (25, 95, 895, 535),      True),
    ("rpc-stubs",                      ("pizarra", 16), (215, 90, 840, 415),     True),
    ("fallas-rpc-no-response",         ("pizarra", 17), (235, 160, 1065, 435),   True,
     [(0, 160, 640, 240)]),                                    # "2. nuevas formas de fallas"
    ("at-least-once",                  ("pizarra", 17), (350, 585, 750, 805),    True),
    ("at-most-once",                   ("pizarra", 17), (225, 1135, 645, 1465),  True),
    ("idempotencia",                   ("pizarra", 18), (110, 10, 930, 470),     True),
]


def renderizar_pizarra(tmp):
    pdf = os.path.join(APUNTES, "pizarra.pdf")
    if not os.path.exists(pdf):
        sys.exit(f"no está la pizarra en {pdf}")
    subprocess.run(
        ["pdftoppm", "-r", str(DPI), "-png", pdf, os.path.join(tmp, "p")], check=True
    )


def abrir(tmp, tipo, n):
    """Devuelve la página y la escala entre sus píxeles y los de la caja."""
    if tipo == "pizarra":
        return Image.open(f"{tmp}/p-{n:02d}.png").convert("RGB"), DPI // 150
    return Image.open(f"{APUNTES}/notas/pagina-{n:02d}.jpg").convert("RGB"), 1


def ceñir_al_contenido(im, margen):
    a = np.array(im.convert("L"))
    tinta = a < 240
    filas, cols = tinta.any(axis=1).nonzero()[0], tinta.any(axis=0).nonzero()[0]
    if len(filas) == 0 or len(cols) == 0:
        return im
    return im.crop((
        max(0, cols.min() - margen),
        max(0, filas.min() - margen),
        min(im.width, cols.max() + 1 + margen),
        min(im.height, filas.max() + 1 + margen),
    ))


def dibujar_grilla(im, paso, escala):
    """Superpone una grilla rotulada en el espacio de coordenadas de las cajas."""
    im = im.copy()
    pincel = ImageDraw.Draw(im)
    for x in range(0, im.width, paso * escala):
        pincel.line([(x, 0), (x, im.height)], fill=(255, 150, 150))
        pincel.text((x + 4, 4), str(x // escala), fill=(200, 0, 0))
    for y in range(0, im.height, paso * escala):
        pincel.line([(0, y), (im.width, y)], fill=(150, 190, 255))
        pincel.text((4, y + 4), str(y // escala), fill=(0, 0, 200))
    return im


def exportar_grillas(tmp, destino):
    """Vuelca las páginas con grilla, para leer de ahí las cajas de recorte."""
    os.makedirs(destino, exist_ok=True)
    paginas = [("pizarra", n) for n in range(1, 19)]
    paginas += [("notas", n) for n in range(1, 8)]
    for tipo, n in paginas:
        try:
            pagina, escala = abrir(tmp, tipo, n)
        except FileNotFoundError:
            continue
        paso = 100 if tipo == "pizarra" else 200
        im = dibujar_grilla(pagina, paso, escala)
        im.thumbnail((900, 1300))  # legible en un vistazo, sin ser enorme
        salida = os.path.join(destino, f"{tipo}-{n:02d}.png")
        im.save(salida)
        print(salida)


def main():
    grilla = "--grilla" in sys.argv
    if not grilla:
        os.makedirs(DESTINO, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        renderizar_pizarra(tmp)
        if grilla:
            destino = tempfile.mkdtemp(prefix="figuras-grilla-")
            exportar_grillas(tmp, destino)
            print(f"\npáginas con grilla en {destino}")
            return
        for figura in FIGURAS:
            nombre, fuente, caja, ceñir = figura[:4]
            borrar = figura[4] if len(figura) > 4 else []

            pagina, escala = abrir(tmp, *fuente)
            if borrar:
                pincel = ImageDraw.Draw(pagina)
                for r in borrar:
                    pincel.rectangle([v * escala for v in r], fill=(255, 255, 255))

            im = pagina.crop(tuple(v * escala for v in caja))
            if ceñir:
                im = ceñir_al_contenido(im, 12 * escala)
            if im.width > ANCHO_MAX:
                alto = round(im.height * ANCHO_MAX / im.width)
                im = im.resize((ANCHO_MAX, alto), Image.LANCZOS)

            # Los trazos de la pizarra se ensucian en jpeg, así que van en png;
            # las fotos y los scans pesan mucho menos en jpeg y no se nota.
            png = os.path.join(DESTINO, nombre + ".png")
            im.save(png, optimize=True)
            if os.path.getsize(png) > 250_000 or fuente[0] == "notas":
                os.remove(png)
                salida = os.path.join(DESTINO, nombre + ".jpg")
                im.save(salida, quality=88, optimize=True, progressive=True)
            else:
                salida = png
            peso = os.path.getsize(salida) // 1024
            print(f"{os.path.basename(salida):40s} {im.width}x{im.height}  {peso} KB")


if __name__ == "__main__":
    main()
