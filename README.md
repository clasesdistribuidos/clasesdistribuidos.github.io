# clasesdistribuidos.github.io

Apuntes de **TA050 — Sistemas Distribuidos I**, FIUBA.

Sitio Jekyll con el theme [Just the Docs](https://just-the-docs.com).

## Estructura

La navegación tiene **dos niveles**: clase → sección. Una sección es una
página. Las subsecciones dentro de una sección son `##` en el cuerpo y salen
en el índice interno de la página y en el buscador, pero nunca en el sidebar.

```
_clases/clase-NN/
  index.md      portada de la clase   (has_children: true)
  NN-slug.md    una página por sección (parent: <título de la clase>)
assets/clase-NN/
                las figuras de esa clase, recortadas de la pizarra y
                de los scans de las notas
```

La jerarquía sale del front matter (`parent` / `nav_order`), no de los
headings, así que el tercer nivel no puede colarse solo.

Estos archivos se editan a mano y son lo único que define el contenido: no hay
ningún formato intermedio del que se generen.

## Desarrollo local

```sh
bundle install
bundle exec jekyll serve --livereload    # http://127.0.0.1:4000
```

## Deploy

`.github/workflows/pages.yml` buildea y publica en cada push a `main`.
Requiere que en *Settings → Pages* la fuente esté puesta en **GitHub Actions**.

## Convenciones

El front matter que espera cada tipo de página, el marcado de las notas y las
figuras, el proceso para recortar las figuras de la pizarra y el estilo de la
prosa están en [CLAUDE.md](CLAUDE.md).
