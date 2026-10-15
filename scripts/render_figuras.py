#!/usr/bin/env python3
"""Compila las figuras redibujadas en TikZ de una clase y las deja en SVG.

Las fuentes viven en figuras/clase-NN/*.tex y comparten figuras/estilo.tex.
Cada una pasa por lualatex -> PDF -> pdftocairo -svg, y el SVG se agranda
(por defecto 1,5x) cambiando solo width/height, para que no se vea chico al
lado de los PNG de 1400 px que hay hoy en assets/.

    python3 scripts/render_figuras.py --clase 14
    python3 scripts/render_figuras.py --clase 14 --png   # además, PNG para revisar
    python3 scripts/render_figuras.py --clase 14 --salida assets/clase-14
    python3 scripts/render_figuras.py --clase 14 --revision  # PDF para corregir a mano

--revision arma un solo PDF con una página por figura, en el orden en que
aparecen en el apunte: el recorte de la pizarra a la izquierda, el redibujo con
una grilla en cm (figuras/grilla.tex) a la derecha y margen para anotar. Queda
en figuras/salida/clase-NN/revision-clase-NN.pdf.

Necesita lualatex (alcanza con TeX Live basic) y pdftocairo/pdftoppm (poppler).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FIGURAS = RAIZ / "figuras"

PAGINAS_REVISION = r"""\documentclass{article}
\usepackage[a4paper,landscape,margin=2.2cm,top=1.6cm]{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{fontspec}
\setmainfont{Helvetica Neue}
\pagestyle{empty}
\setlength\parindent{0pt}
\newcommand\lado[1]{\begin{minipage}[c]{0.44\linewidth}\centering
  \includegraphics[width=\linewidth,height=12cm,keepaspectratio]{#1}\end{minipage}}
\newcommand\pagina[3]{%
  {\large\bfseries #1}\hfill{\small\color{gray}pizarra \quad|\quad TikZ, grilla en cm}\par\vspace{1.2cm}
  #2\hfill\lado{#3}\clearpage}
\begin{document}
"""


def escalar(svg: str, factor: float) -> str:
    def cambiar(m):
        return f'width="{float(m[1]) * factor:.1f}pt" height="{float(m[2]) * factor:.1f}pt"'
    return re.sub(r'width="([\d.]+)pt" height="([\d.]+)pt"', cambiar, svg, count=1)


def lualatex(tex: Path, tmp: str, texinputs: str) -> Path | None:
    env = dict(os.environ, TEXINPUTS=f"{texinputs}{os.pathsep}")
    r = subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
         f"-output-directory={tmp}", str(tex)],
        cwd=tmp, env=env, capture_output=True, text=True)
    pdf = Path(tmp) / f"{tex.stem}.pdf"
    if r.returncode != 0 or not pdf.exists():
        errores = [l for l in r.stdout.splitlines() if l.startswith("!")]
        print(f"  FALLA {tex.name}: {errores[0] if errores else 'ver el log'}", file=sys.stderr)
        return None
    # Helvetica Neue no tiene, por ejemplo, → ni ∥: lualatex no falla, deja el hueco
    log = (Path(tmp) / f"{tex.stem}.log").read_text(errors="replace")
    for faltante in sorted(set(re.findall(r"Missing character: There is no (\S+)", log))):
        print(f"  AVISO {tex.name}: la fuente no tiene {faltante}", file=sys.stderr)
    return pdf


def compilar(tex: Path, salida: Path, factor: float, png: bool) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        pdf = lualatex(tex, tmp, str(FIGURAS))
        if not pdf:
            return False
        svg = Path(tmp) / f"{tex.stem}.svg"
        subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg)], check=True)
        (salida / svg.name).write_text(escalar(svg.read_text(), factor))
        if png:
            subprocess.run(["pdftoppm", "-png", "-r", "130", "-singlefile",
                            str(pdf), str(salida / tex.stem)], check=True)
    print(f"  {tex.stem}.svg")
    return True


def orden_del_apunte(clase: int, texs: list[Path]) -> list[Path]:
    """Las figuras en el orden en que aparecen en las páginas de la clase."""
    nombres = []
    for md in sorted((RAIZ / "_clases" / f"clase-{clase:02d}").glob("*.md")):
        for nombre in re.findall(rf"assets/clase-{clase:02d}/([\w-]+)\.(?:png|jpg)", md.read_text()):
            if nombre not in nombres:
                nombres.append(nombre)
    posicion = {n: i for i, n in enumerate(nombres)}
    return sorted(texs, key=lambda t: (posicion.get(t.stem, len(nombres)), t.stem))


def revision(clase: int, texs: list[Path], salida: Path) -> bool:
    assets = RAIZ / "assets" / f"clase-{clase:02d}"
    with tempfile.TemporaryDirectory() as tmp:
        # un estilo.tex que tapa al real y le suma la grilla, sin tocar las figuras
        envoltorio = Path(tmp) / "envoltorio"
        envoltorio.mkdir()
        (envoltorio / "estilo.tex").write_text(
            f"\\input{{{FIGURAS / 'estilo.tex'}}}\n\\input{{{FIGURAS / 'grilla.tex'}}}\n")
        paginas = []
        for tex in orden_del_apunte(clase, texs):
            pdf = lualatex(tex, tmp, f"{envoltorio}{os.pathsep}{FIGURAS}")
            if not pdf:
                return False
            recortes = [assets / f"{tex.stem}{ext}" for ext in (".png", ".jpg")]
            recorte = next((r for r in recortes if r.exists()), None)
            if recorte:
                izquierda = f"\\lado{{{recorte}}}"
            else:  # pasa en una branch que no tiene las figuras de esa clase
                print(f"  AVISO {tex.stem}: no está el recorte en {assets}", file=sys.stderr)
                izquierda = ("\\begin{minipage}[c]{0.44\\linewidth}\\centering"
                             "\\color{gray}(no está el recorte en esta branch)\\end{minipage}")
            paginas.append(f"\\pagina{{{tex.stem}}}{{{izquierda}}}{{{pdf}}}\n")
        doc = Path(tmp) / f"revision-clase-{clase:02d}.tex"
        doc.write_text(PAGINAS_REVISION + "".join(paginas) + "\\end{document}\n")
        pdf = lualatex(doc, tmp, "")
        if not pdf:
            return False
        shutil.copy(pdf, salida / pdf.name)
    print(f"  {pdf.name}: {len(paginas)} páginas")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clase", type=int, required=True)
    ap.add_argument("--salida", type=Path,
                    help="carpeta destino (por defecto figuras/salida/clase-NN, ignorada por git)")
    ap.add_argument("--escala", type=float, default=1.5)
    ap.add_argument("--png", action="store_true", help="también un PNG por figura, para mirarla")
    ap.add_argument("--revision", action="store_true",
                    help="solo el PDF de revisión: recorte y redibujo lado a lado, con grilla")
    args = ap.parse_args()

    for herramienta in ("lualatex", "pdftocairo"):
        if not shutil.which(herramienta):
            sys.exit(f"falta {herramienta} en el PATH")

    fuentes = FIGURAS / f"clase-{args.clase:02d}"
    texs = sorted(fuentes.glob("*.tex"))
    if not texs:
        sys.exit(f"no hay .tex en {fuentes}")
    salida = args.salida or FIGURAS / "salida" / f"clase-{args.clase:02d}"
    salida.mkdir(parents=True, exist_ok=True)

    print(f"clase {args.clase} -> {salida}")
    if args.revision:
        sys.exit(0 if revision(args.clase, texs, salida) else 1)
    ok = sum(compilar(t, salida, args.escala, args.png) for t in texs)
    print(f"{ok}/{len(texs)} figuras")
    sys.exit(0 if ok == len(texs) else 1)


if __name__ == "__main__":
    main()
