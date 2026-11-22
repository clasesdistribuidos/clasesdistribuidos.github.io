#!/usr/bin/env python3
"""PDF para elegir entre las tres opciones de cada figura de una clase.

Cada figura se redibuja dos veces: la versión fiel a la pizarra, en
figuras/clase-NN/v1/, y la mejorada a partir del texto de la página y del
transcript, en figuras/clase-NN/. Este script arma un A4 vertical por figura,
en el orden del apunte: arriba el recorte de la pizarra y la versión fiel,
abajo la mejorada con la grilla en cm (la que se corrige a mano) y al pie qué
cambió, sacado de figuras/clase-NN/cambios.json
({"nombre-de-figura": "texto LaTeX"}). El usuario elige una de las tres.

    python3 scripts/comparar_figuras.py --clase 14
    # -> figuras/salida/clase-14/revision-clase-14-mejoradas.pdf

render_figuras.py ignora v1/ (solo mira los .tex de la carpeta de la clase).
Usa sus funciones, así que necesita lo mismo: lualatex y poppler.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_figuras as rf  # noqa: E402

PREAMBULO = r"""\documentclass{article}
\usepackage[a4paper,margin=1.4cm,top=1.2cm]{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{fontspec}
\setmainfont{Helvetica Neue}
\newcommand\var[1]{\textit{#1}}
\pagestyle{empty}
\setlength\parindent{0pt}
\newcommand\col[3]{\begin{minipage}[t]{#1\linewidth}\centering
  {\small\color{gray}#2}\par\vspace{4pt}
  \includegraphics[width=\linewidth,height=#3,keepaspectratio]{\archivo}\end{minipage}}
\newcommand\pagina[5]{%
  {\large\bfseries #1}\par\vspace{0.4cm}
  \def\archivo{#2}\col{0.48}{1. pizarra}{5.2cm}\hfill\def\archivo{#3}\col{0.48}{2. versión fiel}{5.2cm}\par\vspace{0.7cm}
  \def\archivo{#4}\col{1}{3. versión mejorada, grilla en cm}{10.5cm}\par\vspace{0.6cm}
  {\small #5}\clearpage}
\begin{document}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clase", type=int, required=True)
    args = ap.parse_args()

    figuras = rf.FIGURAS
    fuentes = figuras / f"clase-{args.clase:02d}"
    v1 = fuentes / "v1"
    assets = rf.RAIZ / "assets" / f"clase-{args.clase:02d}"
    cambios_json = fuentes / "cambios.json"
    cambios = json.loads(cambios_json.read_text()) if cambios_json.exists() else {}
    salida = figuras / "salida" / f"clase-{args.clase:02d}"
    salida.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        envoltorio = Path(tmp) / "envoltorio"
        envoltorio.mkdir()
        (envoltorio / "estilo.tex").write_text(
            f"\\input{{{figuras / 'estilo.tex'}}}\n\\input{{{figuras / 'grilla.tex'}}}\n")
        d1, d2 = Path(tmp) / "v1", Path(tmp) / "v2"
        d1.mkdir()
        d2.mkdir()
        paginas = []
        for tex in rf.orden_del_apunte(args.clase, sorted(fuentes.glob("*.tex"))):
            nueva = rf.lualatex(tex, str(d2), f"{envoltorio}{os.pathsep}{figuras}")
            if not nueva:
                sys.exit(1)
            vieja = v1 / tex.name
            anterior = rf.lualatex(vieja, str(d1), str(figuras)) if vieja.exists() else None
            recortes = [assets / f"{tex.stem}{ext}" for ext in (".png", ".jpg")]
            recorte = next((r for r in recortes if r.exists()), None)
            if not (anterior and recorte):
                print(f"  AVISO {tex.stem}: falta la versión fiel o el recorte; queda fuera",
                      file=sys.stderr)
                continue
            nota = cambios.get(tex.stem, "")
            paginas.append(f"\\pagina{{{tex.stem}}}{{{recorte}}}{{{anterior}}}{{{nueva}}}{{{nota}}}\n")
        doc = Path(tmp) / f"revision-clase-{args.clase:02d}-mejoradas.tex"
        doc.write_text(PREAMBULO + "".join(paginas) + "\\end{document}\n")
        pdf = rf.lualatex(doc, tmp, "")
        if not pdf:
            sys.exit(1)
        shutil.copy(pdf, salida / pdf.name)
    print(f"  {pdf.name}: {len(paginas)} páginas")


if __name__ == "__main__":
    main()
