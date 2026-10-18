---
name: redibujar-figuras
description: >-
  Redibuja en TikZ una figura de la pizarra ya recortada en `assets/clase-NN/`,
  para que el sitio se vea más de libro, y la compila a SVG con
  `scripts/render_figuras.py`. Usar cuando el usuario pide pasar una figura (o
  varias) a TikZ, corregir una ya redibujada, o proponer alternativas a una
  figura que no explica bien el texto. No reemplaza el recorte de la skill
  `recortar-figuras`, y una página pasa a usar el SVG solo cuando el usuario
  elige el redibujo.
---

# Redibujar figuras en TikZ

La figura recortada de la pizarra es la referencia de *qué* hay que dibujar;
el redibujo cambia *cómo* se ve. No se inventa contenido: si algo no está en
la pizarra ni en el pie de la figura, no va, y si se agrega un rótulo para que
se entienda, se le avisa al usuario.

La excepción es cuando el usuario dice que una figura no explica bien el texto
y pide ideas. Ahí se puede agregar contenido, siempre a partir de lo que dice el
texto alrededor:

1. Listar qué ideas del texto se apoyan en la figura y cuáles muestra el
   dibujo.
2. Dibujar las alternativas, cada una con el foco en una idea, y armarle una
   página para elegir: el recorte actual arriba y, por opción, el dibujo, qué
   muestra, al lado de qué párrafo iría y qué agrega que no está en la
   pizarra.
3. El usuario elige. Una puede reemplazar a la figura y otras sumarse como
   figuras nuevas en otros párrafos.

Así salieron las tres de la sección 1 de la clase 1: `sistema-interfaz-entorno`
reemplaza al recorte, y `subsistema-ampliado` y `componentes-y-maquinas` son
nuevas.

## Antes de dibujar

1. **Confirmar cuál es la figura, por nombre de archivo.** "La imagen 1 de la
   clase 1" no es necesariamente la primera que aparece en el `.md`: una vez
   resultó ser la de la pizarra pág. 1, que en la página venía segunda. Si hay
   duda, preguntar con el nombre (`sistema-interfaz-entorno.png`).
2. Mirar el recorte (`assets/clase-NN/<nombre>.png`) y leer su pie en
   `_clases/clase-NN/*.md`: el pie dice qué tiene que mostrar.
3. Si son muchas, estimar el costo antes de arrancar: en la prueba fueron
   entre 3k y 10k tokens por figura, según cuántas vueltas hicieron falta.

## Dibujar

Un archivo por figura, `figuras/clase-NN/<mismo nombre que el recorte>.tex`:

```latex
\input{estilo}
\begin{document}
\begin{figura}\begin{tikzpicture}
  ...
\end{tikzpicture}\end{figura}
\end{document}
```

Lo compartido está en dos archivos y no se redefine por figura:

- `figuras/estilo.tex` es **cómo se ve**: tipografía, colores, trazo, flechas,
  y el entorno `figura`, que recorta la página al dibujo. Los colores son
  `tinta`, el trazo normal; `suave`, para las anotaciones secundarias, que van
  en gris y con llave cuando agrupan; `acento`, el rojo de la pizarra
  (watermark, rechazos, los rótulos que el profesor escribió en rojo); y
  `segundo`, el verde de la pizarra, para una segunda serie o lo aceptado.
- `figuras/formas.tex` es **el vocabulario**: las piezas que se repiten entre
  figuras. Nodos (`nodo`, `lider`, `\tachar`, `componente`, `capas`, `grupo`,
  `paso`), tiempo (`evento`, `onda`, `vida`), flechas (`msg`, `respuesta`,
  `control`, `datos`, `implica`), marcas (`rechazo`, `ok`, `particion`,
  `base`, `marca`, `llave`, `\flecha`) y el anillo (`\anillo`,
  `\nodoanillo`, `\claveanillo`).

**Antes de dibujar, mirar el catálogo**, que tiene cada forma dibujada con su
nombre:

```sh
python3 scripts/render_figuras.py --catalogo   # figuras/salida/catalogo.png
```

Una figura usa las formas de la biblioteca tal como vienen. Si una pieza hace
falta en una sola figura, se define en el `tikzpicture` de esa figura. Cuando
aparece en una segunda, se sube a `formas.tex`, se agrega a `catalogo.tex` y
se cambia la primera para que la use. Las familias que todavía no existen
—tira de celdas para logs, historia de ejecución, tabla, árbol— están
anotadas al final de `formas.tex` y se diseñan con la primera clase que las
necesite.

La letra es la de las figuras de *The Feynman Lectures on Physics*: Computer
Modern Bright, sin serifa, en su versión OpenType (CMU Bright, del paquete
cm-unicode). Las cuatro OTF y su licencia (OFL) están en `figuras/fuentes/`,
y el script las pone en `OPENTYPEFONTS`: no hay que instalar nada. Como en
el libro, **los rótulos van en mayúsculas**, y no se escriben así en el
`.tex`: los pone la fuente (`Letters=Uppercase`), con tildes y ñ. Lo que se
lee como fórmula queda en su caja, como en el libro ("SPIN IN +*x* DIR.",
"16 MeV"):

- las variables van con `\var{W}`, en oblicua y en minúscula. `\textit`
  también se pasa a mayúsculas: nunca usarlo para una variable;
- el código va con `cod`, en Menlo, tal cual (`send(record, id)`);
- una función o una unidad dentro de un rótulo (min, ms) todavía no tiene
  una forma propia: hoy sale en mayúsculas.

En mayúsculas el texto ocupa más: un rótulo que entraba justo puede pisar
una caja, y se achica con `font=\scriptsize` (el libro también tiene
rótulos más chicos).

Dos reglas de forma: un rechazo es la pieza `rechazo`, nunca el carácter ×,
que queda chico. Y las fórmulas se escriben como texto, con `\var{W}` para
las variables y `≥` en unicode: con TeX Live basic no hay `unicode-math`.
CMU Bright no tiene `≥`, `≤` ni `≠`; `estilo.tex` los saca del modo
matemático.

Trampas que ya aparecieron:

- CMU Bright no tiene ∥, ↔, ⇒, ∞ ni ≈ (la → sí): usar `$\parallel$` y
  compañía, o `\flecha` para una flecha dibujada.
- `\@car` y compañía no andan en un `.tex` común. Para rótulos como p₁,
  iterar con dos variables: `\foreach \l/\i in {p/1, q/2}` y
  `\var{\l}\textsubscript{\i}`.
- La punta de una flecha que llega a un evento pisa el rótulo que está de ese
  lado: ponerlo del lado opuesto (`above right` si la flecha llega desde
  arriba a la izquierda), con un parámetro de lado por evento en el
  `foreach`.
- En el PNG algunas líneas se ven más gruesas: es redondeo de píxeles, no el
  dibujo. Se confirma con `grep -o 'stroke-width="[^"]*"' x.svg | sort | uniq -c`.
- Un `\tikz` metido en un texto (`\flecha`) también es un picture: todo lo
  que se engancha a `every picture` le llega. La grilla de revisión lo inflaba
  hasta un cuadrado de 2 cm; por eso `grilla.tex` cuenta el anidamiento.
- `acentuado` es para trazos: sobre un nodo le dibuja un recuadro rojo. Para
  un texto en rojo, `text=acento`.
- Una grilla, guía o fondo que cae en coordenadas enteras tapa las líneas del
  dibujo si va encima: `on background layer`.

Un punto que tiene que caer sobre una curva, como la interfaz sobre el borde
de un óvalo, se ubica con coordenadas de la curva y no calculado a mano:
`(0,0) ++(20:3.0 and 2.3)` en vez de `(2.82,0.78)`.

## Compilar y mirar

```sh
python3 scripts/render_figuras.py --clase N --png
```

Deja un `.svg` y un `.png` por figura en `figuras/salida/clase-NN/`, que git
ignora. Si la fuente no tiene un carácter, el script avisa (`AVISO … la fuente
no tiene →`): lualatex no falla, deja el hueco. Mirar el PNG **después de cada compilación, también después de cada
arreglo chico**: un subíndice corrido o un rótulo pisado no se ven sin
mirarlos. Cosas que hubo que corregir en la prueba: la curva de un gráfico con
una S rara al arrancar, una flecha despegada del punto al que señalaba, una
cruz que pisaba el rótulo de la flecha, un rótulo flotando sin nada al lado.

Para que el usuario las revise, conviene armarle una página que muestre el
recorte y el redibujo lado a lado, con una línea por figura que diga qué se
aparta de la pizarra.

## Feedback del usuario: el PDF de revisión

Las correcciones de dibujo se marcan a mano encima, no se describen con
palabras. Para eso:

```sh
python3 scripts/render_figuras.py --clase N --revision
```

Arma `figuras/salida/clase-NN/revision-clase-NN.pdf`: una página A4 apaisada
por figura, en el orden en que aparecen en el apunte, con el nombre del archivo
arriba, el recorte de la pizarra a la izquierda y el redibujo a la derecha, y
el tercio de abajo libre para escribir. El redibujo lleva una grilla en cm
(`figuras/grilla.tex`), detrás del dibujo y numerada en los bordes, para que
una corrección pueda decir "subilo a la altura 2". La grilla es en cm de la
figura, no del papel ni de las unidades del `.tex` (hay figuras con
`y=0.95cm`): al leer una corrección, traducirla. Ni la grilla ni el PDF llegan
al sitio; los `.tex` no se tocan.

Todas las figuras pendientes de una clase van en el mismo PDF: una página más
no cuesta casi nada, lo caro es leer las anotadas.

El circuito:

1. Antes de pasarle el PDF, decirle al usuario qué se aparta de la pizarra
   en cada figura (rótulos agregados, lecturas dudosas del dibujo), para que
   lo mire con atención.
2. El usuario lo abre en Xournal++ con *Archivo → Anotar PDF* (Xournal++ no
   abre PNG: solo los inserta como imagen), marca en **azul o magenta** —no
   en rojo, que es el `acento` de las figuras—, y exporta con *Archivo →
   Exportar como PDF*. El texto largo, mejor por el chat.
3. Pedirle qué páginas marcó, y abrir solo esas: una sin marcas no cuesta
   nada. Rendirlas con `pdftoppm -png -r 100 -f N -l N` y leerlas
   (≈2–3k tokens por página; corregir la figura después, ≈5–10k).
4. Listar qué se entendió de cada marca antes de tocar el `.tex`, y si una es
   ambigua, preguntar.
5. Corregir, mirar el PNG de nuevo, y volver a armar el PDF con lo que quede.

## En otra máquina

La letra de las figuras viaja con el repo, en `figuras/fuentes/`. La del
código, **Menlo**, se pide por nombre y viene con macOS: en Linux o Windows
hay que instalarla o cambiarla ahí (DejaVu Sans Mono anda), y avisar que el
resultado cambia.

## Llevarlas al sitio

Se adopta figura por figura, cuando el usuario elige el redibujo:

```sh
python3 scripts/render_figuras.py --clase N --salida assets/clase-NN
```

Compila todos los `.tex` de la clase, así que también deja en `assets/` los SVG
de figuras que la página todavía no usa. Commitear solo los SVG que se usan.

En el `.md`, cambiar `.png` por `.svg` en el `src` del `<img>` y actualizar el
`alt` y el pie si el redibujo agrega algo. La `figura-ref` se queda: sigue
diciendo de qué página de la pizarra salió el dibujo. El recorte tampoco se
borra, porque `--revision` lo usa como referencia y `recortar_figuras.py` lo
volvería a generar.

Una figura nueva, que no está en la pizarra, va como cualquier otra
`figura-con-imagen`, con `<span class="figura-ref">agregada al apunte; no está
en la pizarra</span>`.

El SVG sale agrandado 1,5× (`--escala`) porque el CSS solo pone
`max-width: 100%`, y a tamaño natural queda chico al lado de los PNG de
1400 px.
