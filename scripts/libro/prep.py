#!/usr/bin/env python3
"""
Pasada previa: convierte el sitio Jekyll (just-the-docs + kramdown) en UN solo
markdown "pandoc-friendly", sin Liquid, sin HTML y sin IALs de kramdown.

    python3 prep.py RUTA_AL_REPO > libro.md

Mapeo:
  portada de clase (index.md, title)   -> "# Título"        (\\chapter)
  "# N. Sección" de cada página         -> "## N. Sección"   (\\section)
  "## Subsección"                       -> "### Subsección"  (\\subsection)
  <figure> con <img>                    -> ![caption](assets/...)  (figura, caption al margen)
  <figure> sin <img> (pendiente)        -> ::: pendiente
  {: .nota } + > blockquote             -> ::: nota          (\\marginnote)
  {: .fs-2 ... } + párrafo (listings)   -> ::: caption       (\\marginnote)
  {{ '/x/' | relative_url }}            -> URL absoluta del sitio
  TOC de just-the-docs, {: .no_toc }    -> se descartan
"""
import html
import re
import sys
from pathlib import Path

import yaml

SITE = "https://clasesdistribuidos.github.io"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
DETAILS = re.compile(r"<details\b.*?</details>\s*", re.S)
FIGURE = re.compile(r'<figure class="([^"]*)">(.*?)</figure>', re.S)
IMG_SRC = re.compile(r"""<img src="\{\{\s*'(/assets/[^']+)'\s*\|\s*relative_url\s*\}\}\"""")
FIGCAPTION = re.compile(r"<figcaption>(.*?)</figcaption>", re.S)
SPAN = re.compile(r'<span class="figura-(label|ref)">.*?</span>', re.S)
LIQUID_URL = re.compile(r"""\{\{\s*'([^']+)'\s*\|\s*relative_url\s*\}\}""")


def split_front_matter(text):
    m = FRONT_MATTER.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def figure_to_md(m):
    body = m.group(2)
    cap = FIGCAPTION.search(body)
    caption = SPAN.sub("", cap.group(1)) if cap else ""
    caption = " ".join(html.unescape(caption).split())
    caption = caption[:1].upper() + caption[1:]
    src = IMG_SRC.search(body)
    if src:
        path = src.group(1).lstrip('/')
        if path.endswith('.svg'):
            path = path[:-4] + '.pdf'  # build.sh lo convirtió a build/svg/
        return f"\n![{caption}]({path})\n"
    kind = "Código pendiente" if "figura-codigo" in m.group(1) else "Figura pendiente"
    return f"\n::: pendiente\n**{kind}:** {caption}\n:::\n"


def convert_blocks(lines):
    """Pasada línea a línea: headings, notas y captions de listings.
    Respeta los bloques de código (no toca nada adentro de ```)."""
    out, i, in_code = [], 0, False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            in_code = not in_code
            out.append(line)
            i += 1
            continue
        if in_code:
            out.append(line)
            i += 1
            continue

        if re.match(r"^\{:\s*\.no_toc\s*\}\s*$", line):
            i += 1
            continue

        if re.match(r"^#{1,5} ", line):
            out.append("#" + line)  # baja un nivel: la clase es el capítulo
            i += 1
            continue

        # {: .nota } seguido de un blockquote
        if re.match(r"^\{:\s*\.nota\s*\}\s*$", line):
            i += 1
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            out += ["", "::: nota", *quote, ":::", ""]
            continue

        # {: .fs-2 ... } seguido de un párrafo: caption de un listing
        if re.match(r"^\{:\s*\.fs-\d", line):
            i += 1
            para = []
            while i < len(lines) and lines[i].strip():
                para.append(lines[i])
                i += 1
            out += ["", "::: caption", *para, ":::", ""]
            continue

        out.append(line)
        i += 1
    return out


def convert_page(body):
    body = DETAILS.sub("", body)
    body = FIGURE.sub(figure_to_md, body)
    body = LIQUID_URL.sub(lambda m: SITE + m.group(1), body)
    return "\n".join(convert_blocks(body.splitlines())).strip() + "\n"


def collection(root, name):
    chapters = []
    for d in sorted((root / name).iterdir()):
        if not d.is_dir():
            continue
        meta, _ = split_front_matter((d / "index.md").read_text(encoding="utf-8"))
        parts = [f"# {meta['title']}\n"]
        for page in sorted(p for p in d.glob("*.md") if p.name != "index.md"):
            _, body = split_front_matter(page.read_text(encoding="utf-8"))
            parts.append(convert_page(body))
        chapters.append("\n".join(parts))
    return chapters


def main():
    root = Path(sys.argv[1])
    cfg = yaml.safe_load((root / "_config.yml").read_text(encoding="utf-8"))
    doc = [
        "---",
        f"title: {cfg['title']!r}",
        f"subtitle: {cfg['description']!r}",
        "lang: es",
        "---",
        "",
        "```{=latex}\n\\part{Clases}\n```",
        *collection(root, "_clases"),
    ]
    if (root / "_practicas").is_dir():
        doc += ["```{=latex}\n\\part{Prácticas}\n```", *collection(root, "_practicas")]
    sys.stdout.write("\n\n".join(doc))


if __name__ == "__main__":
    main()
