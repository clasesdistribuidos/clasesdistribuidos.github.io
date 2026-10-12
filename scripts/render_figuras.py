#!/usr/bin/env python3
"""Compila las figuras redibujadas en TikZ de una clase y las deja en SVG.

Las fuentes viven en figuras/clase-NN/*.tex y comparten figuras/estilo.tex.
Cada una pasa por lualatex -> PDF -> pdftocairo -svg, y el SVG se agranda
(por defecto 1,5x) cambiando solo width/height, para que no se vea chico al
lado de los PNG de 1400 px que hay hoy en assets/.

    python3 scripts/render_figuras.py --clase 14
    python3 scripts/render_figuras.py --clase 14 --png   # además, PNG para revisar
    python3 scripts/render_figuras.py --clase 14 --salida assets/clase-14

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


def escalar(svg: str, factor: float) -> str:
    def cambiar(m):
        return f'width="{float(m[1]) * factor:.1f}pt" height="{float(m[2]) * factor:.1f}pt"'
    return re.sub(r'width="([\d.]+)pt" height="([\d.]+)pt"', cambiar, svg, count=1)


def compilar(tex: Path, salida: Path, factor: float, png: bool) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, TEXINPUTS=f"{FIGURAS}{os.pathsep}")
        r = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={tmp}", str(tex)],
            cwd=tmp, env=env, capture_output=True, text=True)
        pdf = Path(tmp) / f"{tex.stem}.pdf"
        if r.returncode != 0 or not pdf.exists():
            errores = [l for l in r.stdout.splitlines() if l.startswith("!")]
            print(f"  FALLA {tex.name}: {errores[0] if errores else 'ver el log'}", file=sys.stderr)
            return False
        svg = Path(tmp) / f"{tex.stem}.svg"
        subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg)], check=True)
        (salida / svg.name).write_text(escalar(svg.read_text(), factor))
        if png:
            subprocess.run(["pdftoppm", "-png", "-r", "130", "-singlefile",
                            str(pdf), str(salida / tex.stem)], check=True)
    print(f"  {tex.stem}.svg")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clase", type=int, required=True)
    ap.add_argument("--salida", type=Path,
                    help="carpeta destino (por defecto figuras/salida/clase-NN, ignorada por git)")
    ap.add_argument("--escala", type=float, default=1.5)
    ap.add_argument("--png", action="store_true", help="también un PNG por figura, para mirarla")
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
    ok = sum(compilar(t, salida, args.escala, args.png) for t in texs)
    print(f"{ok}/{len(texs)} figuras")
    sys.exit(0 if ok == len(texs) else 1)


if __name__ == "__main__":
    main()
