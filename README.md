# clasesdistribuidos.github.io

Apuntes de **TA050 — Sistemas Distribuidos I**, FIUBA.

Sitio Jekyll con el theme [Just the Docs](https://just-the-docs.com).

## Estructura

La navegación tiene **dos niveles**: clase → sección. Una sección es una
página. Las subsecciones dentro de una sección son `##` en el cuerpo y salen
en el índice interno de la página y en el buscador, pero nunca en el sidebar.

```
_source/clase-NN.md      apunte monolítico, tal como se escribe
_clases/clase-NN/
  index.md               portada de la clase   (has_children: true)
  01-slug.md             una página por sección (parent: <título de la clase>)
```

La jerarquía sale del front matter (`parent` / `nav_order`), no de los
headings, así que el tercer nivel no puede colarse solo.

## Agregar una clase

1. Escribir el apunte en `_source/clase-NN.md` con front matter:

   ```yaml
   ---
   titulo: Clase 2 — MapReduce
   fecha: 2026-03-13
   ---
   ```

   Las secciones se marcan con `## N. Título` y las subsecciones con `###`.

2. Partirlo en páginas:

   ```sh
   python3 scripts/split_clase.py _source/clase-02.md
   ```

   Las páginas generadas quedan versionadas y son editables a mano a partir
   de ahí. Para regenerar sobre algo ya existente hace falta `--force`, que
   pisa las ediciones manuales. `--dry-run` muestra qué haría.

3. Revisar local y commitear.

El script traduce tres marcadores del fuente:

| En el fuente | Se convierte en |
|---|---|
| `[FIGURA: descripción — notas pág. N]` | recuadro punteado con la descripción |
| `[CÓDIGO PENDIENTE: descripción]` | recuadro punteado, etiquetado como código |
| `*[Nota: texto]*` | callout azul "Nota" |

Y sube un nivel los headings del cuerpo (`###` → `##`), porque el `## N.` de la
sección pasa a ser el `#` de su propia página.

Para reemplazar una figura pendiente por la imagen real, poner el `<img>`
adentro del `<figure>` y agregarle la clase `figura-con-imagen`.

## Desarrollo local

```sh
bundle install
bundle exec jekyll serve --livereload    # http://127.0.0.1:4000
```

## Deploy

`.github/workflows/pages.yml` buildea y publica en cada push a `main`.
Requiere que en *Settings → Pages* la fuente esté puesta en **GitHub Actions**.
