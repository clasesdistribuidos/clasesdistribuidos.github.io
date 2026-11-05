#!/usr/bin/env bash
# Arma los apuntes como libro en PDF, con la clase tufte-book.
#
#   scripts/libro/build.sh [RUTA_AL_REPO]   ->  scripts/libro/build/apuntes-tufte.pdf
#
# Sin argumento usa el repo en el que está. Conviene correrlo sobre un checkout
# limpio de main (git worktree add --detach ... origin/main), no sobre una branch
# con cambios a medias. Necesita pandoc >= 3, rsvg-convert (librsvg), python3
# con PyYAML y TeX Live con latexmk y tufte-latex; la lista completa de
# paquetes está en el CLAUDE.md.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "${1:-$HERE/../..}" && pwd)
OUT="$HERE/build"
mkdir -p "$OUT"

# pdflatex no lee SVG: cada assets/**/*.svg pasa a PDF en build/svg/, con la
# misma ruta, y prep.py cambia la extensión en el markdown.
find "$REPO/assets" -name "*.svg" | while read -r svg; do
  pdf="$OUT/svg/${svg#"$REPO"/}"; pdf="${pdf%.svg}.pdf"
  mkdir -p "$(dirname "$pdf")"
  rsvg-convert -f pdf -o "$pdf" "$svg"
done

python3 "$HERE/prep.py" "$REPO" > "$OUT/libro.md"

pandoc "$OUT/libro.md" \
  --from markdown \
  --to latex \
  --standalone \
  --template "$HERE/tufte-book.latex" \
  --lua-filter "$HERE/tufte.lua" \
  --top-level-division=chapter \
  -V repo="$REPO" \
  -V svgdir="$OUT/svg" \
  -o "$OUT/apuntes-tufte.tex"

cd "$OUT"
latexmk -pdf -interaction=nonstopmode -halt-on-error apuntes-tufte.tex >/dev/null \
  || { tail -40 apuntes-tufte.log; exit 1; }
echo "$OUT/apuntes-tufte.pdf"
