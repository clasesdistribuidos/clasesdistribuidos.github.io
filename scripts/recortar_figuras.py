#!/usr/bin/env python3
"""Recorta las figuras de una clase desde la pizarra y los scans manuscritos.

Las figuras del apunte salen de dos fuentes que viven en el repo de trabajo
(`clases-apuntes`, que por default se busca al lado de este y si no se pasa
con `--apuntes`): la pizarra virtual que el profesor dibujó
en vivo (`raw/claseN/pizarra.pdf`) y los scans de las notas que preparó antes
(`raw/claseN/notas/pagina-NN.jpg`). Cada página trae varias figuras, así que
hay que recortarlas de a una.

Esa N no es necesariamente la de la clase en el sitio: la numeración del repo
de apuntes cuenta las grabaciones y la del sitio cuenta las clases publicadas,
y ya se separaron. `FUENTE_POR_CLASE` guarda las que no coinciden, para que
`--clase N` a secas siga dando lo mismo; `--fuente` lo pisa para probar.

Las cajas de recorte se escriben a mano, mirando las páginas. Están en el
espacio de coordenadas de la pizarra renderizada a 150 dpi (1241x1754), que es
un tamaño cómodo para leer coordenadas de un render con grilla; el render de
trabajo es a 300 dpi y el script escala las cajas solo. Las cajas de los scans
están en las coordenadas nativas del jpg.

La caja no tiene que ser precisa: después de recortar, el script ciñe el
resultado al contenido real y le deja un margen parejo. Lo que sí importa es
que no se cuele texto vecino, y para eso está `borrar`.

    python3 scripts/recortar_figuras.py --clase 2

Regenera todo `assets/clase-NN/`. Es idempotente: se puede correr de nuevo
después de tocar una caja.

    python3 scripts/recortar_figuras.py --clase 2 --grilla

Escribe en un directorio temporal cada página de la pizarra y de las notas con
una grilla de coordenadas encima, rotulada en el mismo espacio en el que se
escriben las cajas. Es el paso previo: se miran esas páginas, se leen las
coordenadas de cada figura y recién ahí se llena la tabla de acá abajo.

Hace falta `pdftoppm` (poppler) además de Pillow y numpy.
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# El material crudo no vive en este repo y su ubicación es de cada máquina: se
# pasa con --apuntes. Este default vale cuando `clases-apuntes` está clonado al
# lado de este repo, que es lo habitual, pero no se da por sentado.
APUNTES_DEFAULT = os.path.join(os.path.dirname(REPO), "clases-apuntes")

# Clase del sitio -> clase del repo de apuntes, para las que no coinciden. La
# clase 3 del sitio se grabó como la 4: `raw/clase3/` es otra cosa y ni siquiera
# tiene `notas/`. Desde ahí el desfasaje se arrastra: la 4 del sitio es la 5 del
# repo. Lo que falta acá se asume igual a sí mismo.
FUENTE_POR_CLASE = {3: 4, 4: 5}

# Recortes que son fotos aunque salgan de la pizarra, y por lo tanto van en
# jpeg. El peso no alcanza para distinguirlos: la foto de Lamport pesa 234 KB en
# png y el diagrama de capas de la clase 1, que es todo trazo y tiene que
# quedarse en png, pesa 238 KB.
FOTOS = {(2, "leslie-lamport")}

# La otra mitad del mismo problema: recortes que son puro trazo y se pasan del
# umbral de peso, así que el criterio automático los mandaría a jpeg y se
# ensuciarían. Los tres casos de falla de la cadena son una figura alta —tres
# bloques uno debajo del otro— y por eso pesa: 301 KB en png contra 132 en jpeg.
TRAZOS = {(3, "fallas-de-la-cadena")}

ANCHO_MAX = 1400  # el ancho de la columna del theme es bastante menor
DPI = 300         # el doble de las coordenadas de las cajas

# nombre, (fuente, página), caja, ceñir, [rectángulos a borrar]
#
# Los rectángulos a borrar tapan texto que quedó dentro de la caja pero no es
# parte de la figura: títulos de la pizarra que el apunte ya dice con palabras.
FIGURAS_POR_CLASE = {
    1: [
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
    ],

    2: [
        # Es una foto, no un trazo: se corta a medida y no se ciñe, porque el
        # fondo claro del follaje confundiría al ceñido.
        ("leslie-lamport",              ("pizarra", 1),  (82, 159, 244, 364),     False),
        ("recursos-no-compartidos",     ("pizarra", 1),  (380, 150, 1241, 400),   True),
        ("maquina-de-estados-orden",    ("pizarra", 1),  (330, 555, 1000, 880),   True),
        ("capas-y-middleware",          ("pizarra", 2),  (285, 40, 950, 300),     True),
        ("tweet-jeff-dean",             ("pizarra", 3),  (60, 100, 1180, 440),    True),
        # La pizarra pág. 6 dibuja el flujo pero no llegó a escribir los
        # resultados (a,2) (b,2) (c,1); las notas sí los tienen.
        ("flujo-map-reduce",            ("notas", 3),    (225, 820, 1265, 1450),  False),
        ("nodos-y-jobs-logicos",        ("pizarra", 6),  (200, 570, 1241, 950),   True),
        ("shuffle-mappers-reducers",    ("pizarra", 7),  (285, 45, 740, 500),     True),
        ("particion-de-claves",         ("pizarra", 7),  (35, 440, 1150, 930),    True,
         [(360, 435, 580, 505)]),                                  # "SHUFFLE" de la figura de arriba
        ("mapper-por-dentro",           ("pizarra", 8),  (20, 15, 950, 600),      True),
        ("reducer-por-dentro",          ("pizarra", 8),  (40, 670, 1241, 1250),   True,
         [(700, 730, 1241, 805),                                   # "M x R archivos intermedios"
          (700, 1045, 1241, 1255)]),                               # el ejemplo del sort
        ("figure-1-anotada",            ("pizarra", 10), (140, 120, 1225, 820),   True),
        # El nodo con el coordinador decidiendo no está en la pizarra: la pág. 9
        # dibuja el nodo pero sin el coordinador.
        ("colocacion-worker-chunkserver", ("notas", 5),  (1150, 1848, 1665, 2105), False),
        ("chunk-local-y-shuffle",       ("pizarra", 9),  (60, 5, 750, 650),       True),
        ("tolerancia-a-fallas",         ("pizarra", 9),  (35, 730, 1150, 1090),   True),
    ],

    # Las 21 figuras salen de la pizarra: no hubo que ir a las notas ni una vez.
    # Es la primera clase en la que pasa. La pizarra de esta clase está bien
    # separada en bloques y casi no hay dibujos apretados contra otros; lo que
    # sí abunda son los títulos de sección, y de ahí que haya tantos `borrar`.
    3: [
        ("web-servers-y-base-de-datos",   ("pizarra", 1), (340, 995, 830, 1490),  True),
        ("dataset-shardeado",             ("pizarra", 2), (60, 335, 500, 790),    True,
         [(40, 335, 245, 405)]),                                   # "SHARDING"
        ("mapeo-dato-ubicacion",          ("pizarra", 2), (690, 505, 1200, 775),  True),
        ("replicas-desincronizadas",      ("pizarra", 3), (385, 60, 830, 215),    True),
        ("tipos-de-falla",                ("pizarra", 3), (50, 240, 850, 440),    True),
        ("state-transfer",                ("pizarra", 3), (180, 822, 600, 1145),  True,
         [(170, 805, 330, 826)]),                                  # "STATE TRANSFER"
        # El borde de abajo lo fija el subíndice de S₀, que baja hasta 1362;
        # justo debajo arranca la llave de "¿cómo conseguimos eso?".
        ("maquina-de-estados-replicada",  ("pizarra", 3), (155, 1168, 1241, 1370), True,
         [(145, 1352, 480, 1420)]),                                # la llave de abajo
        ("clientes-sin-orden",            ("pizarra", 4), (200, 0, 490, 400),     True),
        ("el-log",                        ("pizarra", 4), (330, 685, 880, 980),   True),
        ("wal-de-postgres",               ("pizarra", 4), (300, 1080, 1040, 1480), True),
        ("raft-y-su-log",                 ("pizarra", 5), (200, 15, 960, 560),    True,
         [(185, 15, 280, 82)]),                                    # "Eg2 RAFT"
        ("log-como-versionado",           ("pizarra", 5), (70, 600, 1140, 840),   True),
        ("log-externo-kafka",             ("pizarra", 6), (90, 20, 860, 500),     True),
        ("primary-backup",                ("pizarra", 6), (150, 610, 1190, 890),  True),
        ("change-data-capture",           ("pizarra", 7), (140, 15, 1220, 545),   True,
         [(130, 8, 470, 80)]),                                     # "COMBINACIÓN INTERESANTE"
        ("chain-replication",             ("pizarra", 8), (320, 80, 878, 415),    True),
        ("fallas-de-la-cadena",           ("pizarra", 8), (180, 412, 1200, 1355), True),
        ("agregar-un-nodo",               ("pizarra", 9), (210, 0, 700, 375),     True),
        ("split-brain",                   ("pizarra", 9), (250, 505, 930, 910),   True),
        ("servicio-de-configuracion",     ("pizarra", 9), (280, 950, 830, 1295),  True),
        ("raft-como-servicio-de-configuracion", ("pizarra", 9), (280, 1300, 760, 1700), True),
    ],

    # Es la primera clase en la que el material de las dos fuentes no se
    # superpone: la pizarra tiene los dibujos y las notas tienen escritos los
    # protocolos paso por paso, así que hay dos figuras que solo están ahí.
    4: [
        # La pizarra (pág. 2) dibuja el archivo partido en chunks, pero no anota
        # que cada uno se replica en varios chunkservers, que es la mitad de lo
        # que la figura tiene que decir. Las notas sí lo escriben.
        ("archivo-en-chunks",           ("notas", 1),   (30, 1420, 715, 2025),   False),
        ("arquitectura-gfs",            ("pizarra", 3), (148, 145, 1000, 520),   True,
         [(996, 296, 1006, 326)]),                                 # la punta de la llave de "metadata"
        # Los dos pasos del read, en la pizarra, son los rótulos de la figura 1
        # del paper —o sea la figura anterior—, así que recortarlos sería
        # repetirla. En las notas están escritos aparte, paso por paso.
        ("flujo-de-lectura",            ("notas", 2),   (200, 610, 1445, 960),   False),
        ("anti-patron-de-escritura",    ("pizarra", 3), (340, 575, 750, 905),    True),
        ("coordinador-y-replica-group", ("pizarra", 3), (340, 1026, 1215, 1752), True,
         [(335, 1400, 715, 1700)]),                                # las tres funciones del coordinador
        ("flujo-de-escritura",          ("pizarra", 4), (340, 345, 866, 845),    True,
         [(828, 345, 872, 640)]),                                  # "si todas responden OK / si alguna, error"
        # El "} región inconsistente" del final se sale de la hoja y queda
        # cortado en la fuente, así que el recorte termina en el padding.
        ("region-inconsistente",        ("pizarra", 4), (0, 1135, 1080, 1615),   True),
        ("colocacion-worker-chunkserver", ("pizarra", 6), (190, 100, 600, 605),  True),
        ("chunk-por-mapper",            ("pizarra", 6), (660, 100, 1241, 570),   True),
        ("coordinador-por-dentro",      ("pizarra", 7), (50, 220, 305, 500),     True),
        ("promocion-de-primary",        ("pizarra", 7), (350, 955, 830, 1345),   True),
        ("split-brain",                 ("pizarra", 7), (130, 1350, 955, 1710),  True,
         [(840, 1610, 960, 1715)]),                                # "} SPLIT BRAIN"
        ("coordinador-y-backup",        ("pizarra", 8), (280, 300, 690, 560),    True),
    ],
}

# No todas las figuras salen de la pizarra o de las notas. `dean-y-ghemawat.jpg`
# de la clase 2 es la foto que publicó ACM al darles el premio ACM-Infosys
# (https://x.com/TheOfficialACM/status/714464706195378176); está versionada en
# `assets/clase-02/` y este script no la toca. Va acá para que no quede como un
# archivo suelto sin explicación al leer la tabla.


def renderizar_pizarra(tmp, apuntes):
    pdf = os.path.join(apuntes, "pizarra.pdf")
    if not os.path.exists(pdf):
        sys.exit(f"no está la pizarra en {pdf}")
    subprocess.run(
        ["pdftoppm", "-r", str(DPI), "-png", pdf, os.path.join(tmp, "p")], check=True
    )


def paginas_pizarra(tmp):
    """Número de página -> archivo, para lo que dejó pdftoppm.

    pdftoppm rellena con ceros a la izquierda según cuántas páginas tenga el
    PDF: con 18 páginas escribe `p-01.png` y con 9 escribe `p-1.png`. Así que
    el ancho no se puede dar por sentado —dárlo por sentado hacía que las
    clases de menos de diez páginas se saltearan enteras— y se descubre.
    """
    return {int(re.search(r"p-(\d+)\.png$", f).group(1)): f
            for f in glob.glob(os.path.join(tmp, "p-*.png"))}


def abrir(tmp, apuntes, tipo, n):
    """Devuelve la página y la escala entre sus píxeles y los de la caja."""
    if tipo == "pizarra":
        paginas = paginas_pizarra(tmp)
        if n not in paginas:
            raise FileNotFoundError(f"la pizarra no tiene página {n}")
        return Image.open(paginas[n]).convert("RGB"), DPI // 150
    return Image.open(f"{apuntes}/notas/pagina-{n:02d}.jpg").convert("RGB"), 1


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


def exportar_grillas(tmp, apuntes, destino):
    """Vuelca las páginas con grilla, para leer de ahí las cajas de recorte."""
    os.makedirs(destino, exist_ok=True)
    # Cuántas páginas hay es cosa de cada clase, así que se descubren.
    paginas = [("pizarra", n) for n in sorted(paginas_pizarra(tmp))]
    paginas += [("notas", int(re.search(r"(\d+)", os.path.basename(f)).group(1)))
                for f in sorted(glob.glob(f"{apuntes}/notas/pagina-*.jpg"))]
    for tipo, n in paginas:
        pagina, escala = abrir(tmp, apuntes, tipo, n)
        paso = 100 if tipo == "pizarra" else 200
        im = dibujar_grilla(pagina, paso, escala)
        im.thumbnail((900, 1300))  # legible en un vistazo, sin ser enorme
        salida = os.path.join(destino, f"{tipo}-{n:02d}.png")
        im.save(salida)
        print(salida)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clase", type=int, required=True, help="número de clase")
    ap.add_argument("--apuntes", default=APUNTES_DEFAULT,
                    help="dónde está clonado el repo clases-apuntes "
                         f"(default: {APUNTES_DEFAULT})")
    ap.add_argument("--fuente", type=int,
                    help="clase del repo de apuntes de la que salen las páginas, "
                         "cuando no es la misma que --clase (default: FUENTE_POR_CLASE)")
    ap.add_argument("--grilla", action="store_true",
                    help="volcar las páginas con grilla en vez de recortar")
    args = ap.parse_args()

    fuente = args.fuente or FUENTE_POR_CLASE.get(args.clase, args.clase)
    apuntes = os.path.join(args.apuntes, "raw", f"clase{fuente}")
    if not os.path.isdir(apuntes):
        sys.exit(f"no está el material de la clase {args.clase} en {apuntes}\n"
                 f"pasá la ubicación de clases-apuntes con --apuntes")
    if args.clase not in FIGURAS_POR_CLASE:
        sys.exit(f"no hay tabla de figuras para la clase {args.clase}")
    figuras = FIGURAS_POR_CLASE[args.clase]
    destino = os.path.join(REPO, "assets", f"clase-{args.clase:02d}")

    if not args.grilla:
        os.makedirs(destino, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        renderizar_pizarra(tmp, apuntes)
        if args.grilla:
            salida = tempfile.mkdtemp(prefix=f"figuras-grilla-clase{args.clase}-")
            exportar_grillas(tmp, apuntes, salida)
            print(f"\npáginas con grilla en {salida}")
            return
        for figura in figuras:
            nombre, fuente, caja, ceñir = figura[:4]
            borrar = figura[4] if len(figura) > 4 else []

            pagina, escala = abrir(tmp, apuntes, *fuente)
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
            es_foto = fuente[0] == "notas" or (args.clase, nombre) in FOTOS
            es_trazo = (args.clase, nombre) in TRAZOS
            png = os.path.join(destino, nombre + ".png")
            im.save(png, optimize=True)
            if not es_trazo and (os.path.getsize(png) > 250_000 or es_foto):
                os.remove(png)
                archivo = os.path.join(destino, nombre + ".jpg")
                im.save(archivo, quality=88, optimize=True, progressive=True)
            else:
                archivo = png
            peso = os.path.getsize(archivo) // 1024
            print(f"{os.path.basename(archivo):40s} {im.width}x{im.height}  {peso} KB")


if __name__ == "__main__":
    main()
