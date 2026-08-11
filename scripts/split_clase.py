#!/usr/bin/env python3
"""Parte un borrador de clase monolítico en una página por sección.

Uso:
    scripts/split_clase.py ~/borradores/clase-02.md
    scripts/split_clase.py ~/borradores/clase-02.md --force
    scripts/split_clase.py ~/borradores/clase-02.md --dry-run

Andamio de arranque, no parte del sitio: sirve para convertir un apunte escrito
de corrido en la estructura de páginas de `_clases/`. El borrador vive fuera del
repo y no se versiona; una vez partida la clase, las páginas generadas son la
única fuente y se editan a mano. Por eso `--force` es peligroso sobre una clase
ya existente: pisa esas ediciones. `--dry-run` muestra qué haría.

El borrador se corta en cada heading `## N. Título`; los `###` de adentro son
las subsecciones. Cada sección resultante se escribe en
`_clases/clase-NN/NN-slug.md` con el front matter que Just the Docs necesita
para armar el sidebar en dos niveles (clase -> sección).

Además traduce tres marcadores de taquigrafía, cómodos al transcribir:

    [FIGURA: descripción — notas pág. N]   -> recuadro punteado con la descripción
    [CÓDIGO PENDIENTE: descripción]        -> recuadro punteado, etiquetado como código
    *[Nota: texto]*                        -> callout azul "Nota"

El número de clase sale del nombre del archivo (`clase-02.md` -> 2). El título
sale del front matter del borrador (`titulo:`) o de --titulo.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_CLASES = RAIZ / "_clases"

RE_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
RE_SECCION = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
RE_HEADING = re.compile(r"^(#{3,6})\s+(.*)$")
# "3.2 El reparto" o "3.2. El reparto". Pide al menos un punto para no comerse
# un título que arranque con un año o una cifra suelta.
RE_NUMERACION = re.compile(r"^\d+(?:\.\d+)+\.?\s+")

# [FIGURA: descripción — notas pág. 4 / pizarra pág. 11]
RE_FIGURA = re.compile(r"^\[FIGURA:\s*(.+?)\]\s*$")
# La descripción trae guiones largos propios, así que la referencia se corta
# por el último "—" cuya cola arranque en notas/pizarra, no por el primero.
RE_REFERENCIA = re.compile(r"^(.*)\s+—\s+((?:notas|pizarra)\b.*)$", re.DOTALL)

# [CÓDIGO PENDIENTE: ...], con o sin backticks alrededor.
RE_CODIGO = re.compile(r"^`?\[CÓDIGO PENDIENTE:\s*(.+?)\]`?\s*$")

# *[Nota: ...]* — a veces seguida de prosa en la misma línea, y a veces
# abarcando varios párrafos hasta el `]*` de cierre.
RE_NOTA = re.compile(r"^\*\[Nota:\s*(.+?)\]\*\s*(.*)$", re.DOTALL)
RE_ABRE_NOTA = re.compile(r"^\*\[Nota:")


def slugify(texto: str, limite: int = 50) -> str:
    """Slug ASCII, sin acentos, cortado en borde de palabra."""
    normalizado = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    limpio = re.sub(r"[^a-zA-Z0-9]+", "-", sin_acentos).strip("-").lower()
    if len(limpio) <= limite:
        return limpio
    recortado = limpio[:limite]
    if "-" in recortado:
        recortado = recortado.rsplit("-", 1)[0]
    return recortado.strip("-")


def yaml_str(texto: str) -> str:
    """Escapa un string para YAML entre comillas dobles."""
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"') + '"'


def separar_front_matter(texto: str) -> tuple[dict[str, str], str]:
    """Devuelve (campos, cuerpo). Parser mínimo: sólo `clave: valor` planos."""
    match = RE_FRONT_MATTER.match(texto)
    if not match:
        return {}, texto
    campos: dict[str, str] = {}
    for linea in match.group(1).splitlines():
        if ":" not in linea or linea.lstrip().startswith("#"):
            continue
        clave, _, valor = linea.partition(":")
        campos[clave.strip()] = valor.strip().strip("\"'")
    return campos, texto[match.end():]


def promover_headings(texto: str) -> str:
    """Sube un nivel los headings del cuerpo y les saca la numeración.

    El `## N. Título` de la sección pasa a ser el `#` de su propia página, así
    que sus `###` tienen que volverse `##` para no saltear un nivel. Además el
    índice interno y la búsqueda de Just the Docs trabajan sobre h2.

    Algunos borradores numeran las subsecciones (`### 3.2 El reparto`). Adentro
    de una página que ya se titula "3. Del modelo al clúster" ese número sobra,
    así que se lo saca.
    """
    salida = []
    en_bloque_codigo = False
    for linea in texto.splitlines():
        if linea.lstrip().startswith("```"):
            en_bloque_codigo = not en_bloque_codigo
            salida.append(linea)
            continue
        match = RE_HEADING.match(linea) if not en_bloque_codigo else None
        if match:
            almohadillas, titulo = match.groups()
            titulo = RE_NUMERACION.sub("", titulo)
            salida.append("#" * (len(almohadillas) - 1) + " " + titulo)
        else:
            salida.append(linea)
    return "\n".join(salida)


def caja_figura(descripcion: str, clase_css: str, etiqueta: str) -> str:
    """HTML crudo para un placeholder de figura o de código.

    Se emite HTML y no un `{% include %}` porque las descripciones traen
    comillas y guiones largos que romperían los parámetros de Liquid. Cuando
    exista la imagen real alcanza con agregar un <img> adentro del <figure>.
    """
    referencia = ""
    match = RE_REFERENCIA.match(descripcion)
    if match:
        descripcion, referencia = match.group(1), match.group(2)

    partes = [
        f'<figure class="{clase_css}">',
        "  <figcaption>",
        f'    <span class="figura-label">{etiqueta}</span>',
        f"    {html.escape(descripcion.strip())}",
    ]
    if referencia:
        partes.append(f'    <span class="figura-ref">{html.escape(referencia.strip())}</span>')
    partes += ["  </figcaption>", "</figure>"]
    return "\n".join(partes)


def capitalizar(texto: str) -> str:
    """Arranca la nota en mayúscula, como el resto de las notas del sitio.

    En el borrador las notas siguen a la palabra "Nota:" y por eso vienen en
    minúscula. Solo se toca cuando la nota empieza con una palabra, saltando
    las itálicas de apertura; si arranca con otra cosa —una cita entrecomillada,
    un `§3.3`, código— se deja como está, porque ahí la mayúscula caería
    adentro de algo que no es el comienzo de la oración.
    """
    i = 0
    while i < len(texto) and texto[i] in "*_":
        i += 1
    if i < len(texto) and texto[i].islower():
        return texto[:i] + texto[i].upper() + texto[i + 1:]
    return texto


def bloque_nota(contenido: str) -> str:
    """Callout `nota` de Just the Docs, preservando el markdown de adentro."""
    contenido = capitalizar(contenido.strip())
    lineas = [f"> {l}" if l.strip() else ">" for l in contenido.splitlines()]
    return "{: .nota }\n" + "\n".join(lineas)


def transformar_marcadores(texto: str) -> str:
    salida: list[str] = []
    en_bloque_codigo = False
    lineas = texto.splitlines()
    i = 0

    while i < len(lineas):
        linea = lineas[i]

        if linea.lstrip().startswith("```"):
            en_bloque_codigo = not en_bloque_codigo
            salida.append(linea)
            i += 1
            continue
        if en_bloque_codigo:
            salida.append(linea)
            i += 1
            continue

        if m := RE_FIGURA.match(linea):
            salida.append(caja_figura(m.group(1), "figura", "Figura"))
            i += 1
            continue

        if m := RE_CODIGO.match(linea):
            salida.append(caja_figura(m.group(1), "figura figura-codigo", "Código pendiente"))
            i += 1
            continue

        if RE_ABRE_NOTA.match(linea):
            # Una nota puede abarcar varios párrafos: se juntan las líneas
            # hasta el `]*` que la cierra. Si no cierra nunca, la línea queda
            # como está y el marcador crudo se ve en la página, que es la
            # señal de que el borrador está mal formado.
            fin = i
            bloque = linea
            while "]*" not in bloque and fin + 1 < len(lineas):
                fin += 1
                bloque += "\n" + lineas[fin]

            if m := RE_NOTA.match(bloque):
                salida.append(bloque_nota(m.group(1)))
                resto = m.group(2).strip()
                if resto:
                    # La nota venía inline con prosa detrás: la prosa pasa a
                    # ser su propio párrafo, después del callout.
                    salida.append("")
                    salida.append(resto)
                i = fin + 1
                continue

        salida.append(linea)
        i += 1

    return "\n".join(salida)


def contar_subsecciones(texto: str) -> int:
    return len(re.findall(r"^##\s+", texto, re.MULTILINE))


@dataclass
class Seccion:
    numero: int
    titulo: str
    cuerpo: str

    @property
    def slug(self) -> str:
        return f"{self.numero:02d}-{slugify(self.titulo)}"


def partir(cuerpo: str) -> tuple[str, list[Seccion]]:
    matches = list(RE_SECCION.finditer(cuerpo))
    if not matches:
        raise SystemExit("No se encontró ningún heading '## N. Título' en el fuente.")

    preambulo = cuerpo[: matches[0].start()].strip()
    secciones = []
    for i, m in enumerate(matches):
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(cuerpo)
        secciones.append(
            Seccion(
                numero=int(m.group(1)),
                titulo=m.group(2).strip(),
                cuerpo=cuerpo[m.end():fin].strip(),
            )
        )
    return preambulo, secciones


INDICE = """<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>
"""


def render_seccion(seccion: Seccion, titulo_clase: str) -> str:
    cuerpo = transformar_marcadores(promover_headings(seccion.cuerpo))
    encabezado = [
        "---",
        f"title: {yaml_str(f'{seccion.numero}. {seccion.titulo}')}",
        f"parent: {yaml_str(titulo_clase)}",
        f"nav_order: {seccion.numero}",
        "---",
        "",
        f"# {seccion.numero}. {seccion.titulo}",
    ]
    # El índice interno sólo aporta si hay varias subsecciones; con una sola
    # (o ninguna) es ruido.
    if contar_subsecciones(cuerpo) >= 2:
        encabezado += ["{: .no_toc }", "", INDICE]
    encabezado += ["", cuerpo, ""]
    return "\n".join(encabezado)


def render_indice(titulo_clase: str, numero: int) -> str:
    """Portada de la clase: solo el título.

    Lo que el borrador trae antes de la primera sección es su propio título y
    su tabla de contenidos, que acá duplicarían el sidebar. Se descarta; main()
    avisa qué se tiró para que no se pierda nada en silencio.
    """
    return "\n".join([
        "---",
        f"title: {yaml_str(titulo_clase)}",
        f"nav_order: {numero}",
        "has_children: true",
        # Sin esto la portada de la clase caería en /clase-NN/index/, porque
        # el `:path` de la collection incluye el nombre del archivo.
        f"permalink: /clase-{numero:02d}/",
        "---",
        "",
        f"# {titulo_clase}",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fuente", type=Path)
    parser.add_argument("--titulo", help="Título de la clase (si no está en el front matter)")
    parser.add_argument("--force", action="store_true", help="Sobrescribe una clase ya generada")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    texto = args.fuente.read_text(encoding="utf-8")
    campos, cuerpo = separar_front_matter(texto)

    match_numero = re.search(r"(\d+)", args.fuente.stem)
    if not match_numero:
        raise SystemExit(f"No pude sacar el número de clase de '{args.fuente.name}'.")
    numero = int(match_numero.group(1))

    titulo_clase = args.titulo or campos.get("titulo")
    if not titulo_clase:
        raise SystemExit("Falta el título de la clase: usá --titulo o `titulo:` en el front matter.")

    preambulo, secciones = partir(cuerpo)
    destino = DIR_CLASES / f"clase-{numero:02d}"

    if destino.exists() and not args.force and not args.dry_run:
        raise SystemExit(f"{destino.relative_to(RAIZ)} ya existe. Usá --force para sobrescribir.")

    archivos = {destino / "index.md": render_indice(titulo_clase, numero)}
    for seccion in secciones:
        archivos[destino / f"{seccion.slug}.md"] = render_seccion(seccion, titulo_clase)

    print(f"Clase {numero}: {titulo_clase}")
    print(f"  {len(secciones)} secciones -> {destino.relative_to(RAIZ)}/")
    if preambulo:
        print(f"  se descartaron {len(preambulo.splitlines())} líneas previas a la "
              "primera sección (título y tabla de contenidos del borrador):")
        for linea in preambulo.splitlines()[:4]:
            print(f"      | {linea[:70]}")
        print("      | ...")
    for ruta, contenido in archivos.items():
        print(f"    {ruta.name}  ({len(contenido.splitlines())} líneas)")
        if not args.dry_run:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")

    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
