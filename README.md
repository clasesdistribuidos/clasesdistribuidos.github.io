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
```

La jerarquía sale del front matter (`parent` / `nav_order`), no de los
headings, así que el tercer nivel no puede colarse solo.

Estos archivos se editan a mano y son lo único que define el contenido: no hay
ningún formato intermedio del que se generen.

## Front matter

Portada de la clase:

```yaml
---
title: "Clase 2 — MapReduce"
nav_order: 2
has_children: true
permalink: /clase-02/
---
```

El `permalink` explícito hace falta porque el `:path` de la collection incluye
el nombre del archivo; sin él la portada caería en `/clase-02/index/`.

Sección:

```yaml
---
title: "3. La organización cliente-servidor"
parent: "Clase 2 — MapReduce"
nav_order: 3
---
```

El `parent` tiene que coincidir exactamente con el `title` de la portada, que
es como Just the Docs arma el árbol.

## Convenciones del cuerpo

**Índice interno.** Después del `# N. Título` de la página, marcado con
`{: .no_toc }` para que no se duplique:

```markdown
# 3. La organización cliente-servidor
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>
```

Solo aporta si la página tiene dos o más `##`; con una sola es ruido.

**Nota.** Callout azul, definido en `_config.yml`:

```markdown
{: .nota }
> Texto de la nota.
```

**Figura pendiente.** Recuadro punteado con la descripción de lo que va a ir
ahí y, opcionalmente, la referencia a las notas o la pizarra:

```html
<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    dos nodos unidos por un enlace de comunicación
    <span class="figura-ref">notas pág. 2 / pizarra pág. 4</span>
  </figcaption>
</figure>
```

Para reemplazarla por la imagen real, poner el `<img>` adentro del `<figure>`
y agregarle la clase `figura-con-imagen`. Para un bloque de código todavía no
escrito, la misma estructura con `class="figura figura-codigo"` y la etiqueta
`Código pendiente`.

## Agregar una clase

Crear `_clases/clase-NN/` con su `index.md` y una página por sección, copiando
el front matter de una clase existente.

Si el apunte se escribió de corrido en un único archivo —que suele ser lo más
cómodo para transcribir—, `scripts/split_clase.py` lo parte en páginas y
genera el front matter, los slugs y los índices internos. Ese borrador es un
andamio: no se versiona, y una vez partido las páginas son lo único que se
mantiene. Ver el docstring del script para el formato que espera.

## Desarrollo local

```sh
bundle install
bundle exec jekyll serve --livereload    # http://127.0.0.1:4000
```

## Deploy

`.github/workflows/pages.yml` buildea y publica en cada push a `main`.
Requiere que en *Settings → Pages* la fuente esté puesta en **GitHub Actions**.
