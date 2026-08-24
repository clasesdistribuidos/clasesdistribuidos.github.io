# CLAUDE.md

Apuntes de **TA050 — Sistemas Distribuidos I** (FIUBA), como sitio Jekyll con
el theme [Just the Docs](https://just-the-docs.com).

El contenido son los `.md` de `_clases/`. Se editan a mano y son la única
fuente: no hay ningún formato intermedio del que se generen ni ningún paso de
build que los toque. Lo que está en el archivo es lo que se publica.

## Reglas que no hay que romper

**La navegación tiene dos niveles y solo dos: clase → sección.** Una sección es
una página. Las subsecciones dentro de una página son `##` y salen en el índice
interno y en el buscador, pero nunca en el sidebar. La jerarquía sale del front
matter (`parent` / `nav_order`), no de los headings, así que un tercer nivel no
puede colarse solo — pero tampoco hay que agregarlo a mano inventando páginas
con `has_children` adentro de una clase.

**El `parent` de una sección tiene que coincidir carácter por carácter con el
`title` de la portada de su clase.** Así arma el árbol Just the Docs. Si se
renombra una clase, hay que actualizar el `parent` de todas sus secciones.

**No agregar links de anterior/siguiente a mano.** `_includes/footer_custom.html`
los genera solo, ordenando por URL. Funciona porque clases y secciones están
numeradas con cero a la izquierda.

**Los borradores no se versionan.** Ver "Agregar una clase".

## Anatomía

```
_clases/clase-NN/
  index.md            portada de la clase   (has_children: true)
  NN-slug.md          una página por sección (parent: <título de la clase>)
assets/clase-NN/      las figuras recortadas de esa clase
_includes/            navegación secuencial al pie
_sass/custom/         estilos propios (figuras, nav secuencial)
_data/papers.yml      la bibliografía que lista papers.md
scripts/              andamios; excluidos del build
```

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

Arrancan en mayúscula, aunque en el borrador vengan en minúscula detrás de
"Nota:". Se dejan como están cuando lo primero no es una palabra —una cita
entrecomillada, un `§3.3`— porque ahí la mayúscula caería adentro de otra cosa.

**Figura pendiente.** Recuadro punteado con la descripción de lo que va a ir
ahí y la referencia a la página de donde va a salir el dibujo:

```html
<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    dos nodos unidos por un enlace de comunicación
    <span class="figura-ref">notas pág. 2 / pizarra pág. 4</span>
  </figcaption>
</figure>
```

**Figura con imagen.** El `<img>` va adentro del `<figure>`, antes del pie, y
el `<figure>` suma la clase `figura-con-imagen`. La descripción y la referencia
se quedan: la primera es el pie, la segunda dice de dónde salió el dibujo.

```html
<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-01/enlace-dos-nodos.png' | relative_url }}" alt="Dos nodos unidos por un enlace de comunicación">
  <figcaption>
    <span class="figura-label">Figura</span>
    dos nodos unidos por un enlace de comunicación
    <span class="figura-ref">notas pág. 2 / pizarra pág. 4</span>
  </figcaption>
</figure>
```

El `alt` va corto: el pie ya describe la figura en detalle y está ahí al lado.

**Código pendiente.** La misma estructura, con `class="figura figura-codigo"` y
la etiqueta `Código pendiente`.

## Figuras: de la pizarra al sitio

Las figuras no se dibujan de nuevo: se recortan de lo que el profesor usó en
clase. Hay dos fuentes, y las dos viven en el repo de trabajo `clases-apuntes`
(`raw/claseN/`). Dónde está clonado es cosa de cada máquina, así que no se
escribe acá: el script lo busca al lado de este repo y si no está se le pasa
con `--apuntes`.

- **La pizarra virtual** (`pizarra.pdf`), que dibujó en vivo. Es la fuente
  preferida: son trazos vectoriales, se rinden nítidos a cualquier resolución.
  Intercala hojas dibujadas a mano con capturas del libro, fotos y recortes.
- **Los scans de las notas** (`notas/pagina-NN.jpg`), que preparó antes de la
  clase. Papel, más sucios y de menos resolución. Se usan solo cuando la
  pizarra no sirve: porque esa página quedó sin dibujo, o porque el dibujo
  quedó apretado contra otra cosa y es ilegible.

Cuando se elige notas sobre pizarra, dejar un comentario en el script diciendo
por qué. En la clase 1 pasó dos veces y las dos están anotadas.

`scripts/recortar_figuras.py` es el registro del recorte: tiene una tabla por
clase con una caja por figura, y `--clase N` regenera `assets/clase-NN/` entero.
Es idempotente, así que corregir una caja es editar un número y volver a
correrlo — y volver a correr una clase vieja tiene que dar los mismos bytes.
Necesita `pdftoppm` (poppler), Pillow y numpy.

### El proceso

1. **Contar los placeholders primero.** `grep -c '<figure class="figura">'` en
   las páginas de la clase da el número exacto de figuras que la tabla del
   script tiene que tener. El script no lo verifica por su cuenta, y es fácil
   saltearse una: en la clase 1 me faltó una y la cuenta no cerró recién al
   final.
2. **Leer el mapeo, no adivinarlo.** El `<span class="figura-ref">` de cada
   placeholder ya dice de qué página sale esa figura. Está escrito desde que se
   transcribió el apunte.
3. **Sacar las coordenadas de un render con grilla**, no a ojo ni a fuerza de
   iterar:

   ```sh
   python3 scripts/recortar_figuras.py --clase N --grilla
   ```

   Vuelca en un directorio temporal cada página de la pizarra y de las notas
   con una grilla rotulada en el mismo espacio en el que se escriben las cajas.
   Se miran esas imágenes y se leen las cajas directamente de la grilla.
4. **Mirar la página entera antes de cortar.** Una página de pizarra suele
   tener varias figuras (la 14 de la clase 1 tiene tres) y además texto que no
   es parte de ninguna.
5. **Llenar la tabla.** Las cajas de la pizarra van en coordenadas de 150 dpi
   (1241x1754); el script rinde a 300 y las escala solo. Las de los scans van
   en las coordenadas nativas del jpg. La caja no necesita ser precisa: el
   script la ciñe al contenido real y le deja un margen parejo. Lo que sí
   importa es que no entre contenido ajeno.
6. **Tapar el texto vecino con `borrar`.** Títulos que el apunte ya dice con
   palabras, separadores entre secciones de la pizarra, restos de la figura de
   al lado: rectángulos blancos, en las mismas coordenadas que las cajas.
7. **Revisar todo junto antes de darlo por bueno.** Armar una hoja de contactos
   con los recortes en miniatura y mirarla de una: así saltan los que se
   llevaron algo de al lado o cortaron una etiqueta. Recorte por recorte, eso
   se pasa por alto.

### Formatos

El script decide solo, y el criterio es: los trazos de la pizarra se ensucian
en jpeg, así que van en png; las fotos y los scans pesan mucho menos en jpeg y
la diferencia no se ve. Ancho máximo 1400 px, bastante más que la columna del
theme, para que se vean bien en pantallas densas.

## Agregar una clase

El apunte de cada clase se escribe de corrido, fuera de este repo, y llega como
un único `.md` con marcadores `[FIGURA:]`, `[CÓDIGO PENDIENTE:]` y `*[Nota:]*`.
`scripts/split_clase.py` lo parte en una página por sección y traduce esos
marcadores.

**El procedimiento completo está en la skill `nueva-clase`**
(`.claude/skills/nueva-clase/SKILL.md`): branch propia por clase, qué contar
antes y después, qué revisar, y qué no tocar.

Ese borrador es un andamio: vive fuera del repo, no se versiona, y una vez
partido las páginas son lo único que se mantiene. Por eso `--force` sobre una
clase que ya existe es peligroso, pisa las ediciones hechas a mano.

Cada clase se trabaja en una feature branch y se mergea a `main`. El recorte de
las figuras va en una branch aparte, después de mergear el texto.

## La prosa

El apunte está escrito como se da la clase: párrafos largos y corridos, en
primera persona del plural ("vamos a ver", "dijimos"), voseo rioplatense.
Explica los conceptos en el orden en que aparecieron y va enganchando uno con
el siguiente.

Al editar, seguir lo que ya está en la página. En particular, no convertir la
prosa en listas de bullets: las enumeraciones del pizarrón están deliberadamente
escritas como texto seguido. Las negritas son escasas y marcan el término que se
está definiendo; la itálica, énfasis.

## Desarrollo local

```sh
bundle install
bundle exec jekyll serve --livereload    # http://127.0.0.1:4000
```

`.github/workflows/pages.yml` buildea y publica en cada push a `main`.
