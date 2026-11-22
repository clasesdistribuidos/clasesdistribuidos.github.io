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
el redibujo cambia *cómo* se ve. Cada figura se redibuja dos veces, en la
misma pasada, y el usuario elige entre tres opciones: el recorte, la versión
fiel y la versión mejorada.

La **versión fiel** no inventa contenido: si algo no está en la pizarra ni en
el pie de la figura, no va, y si se agrega un rótulo para que se entienda, se
le avisa al usuario. Va en `figuras/clase-NN/v1/`. La **versión mejorada**
parte del lugar donde va la figura, y no solo de la pizarra: se dibuja para
que muestre lo que dice el texto, con lo que hace falta agregar o sacar para
eso. Va en `figuras/clase-NN/`, que es la carpeta que compila
`render_figuras.py`. Cómo se arma está en "La versión mejorada", más abajo.

Cuando el usuario dice que una figura no explica bien el texto y pide ideas,
se va más allá de la mejorada: se proponen varias, cada una con su foco,
siempre a partir de lo que dice el texto alrededor:

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
nuevas. Las alternativas se dibujan aparte, cada una en su propio `.tex` con
un nombre que diga qué prueba, y no pisan la figura hasta que el usuario elige.

Una figura también puede no redibujarse: si lo que hay en la pizarra es una
enumeración en dos columnas, o una lista de cosas con sus propiedades, queda
mejor como una tabla markdown en la página, con los textos en castellano.
Así terminó `memoria-dispositivos` en la clase 1. La tabla reemplaza al
`<figure>` entero, el recorte se queda en `assets/` y el `.tex`, si existía,
no se adopta.

## Antes de dibujar

1. **Confirmar cuál es la figura, por nombre de archivo.** "La imagen 1 de la
   clase 1" no es necesariamente la primera que aparece en el `.md`: una vez
   resultó ser la de la pizarra pág. 1, que en la página venía segunda. Si hay
   duda, preguntar con el nombre (`sistema-interfaz-entorno.png`).
2. Mirar el recorte (`assets/clase-NN/<nombre>.png`) y leer su pie en
   `_clases/clase-NN/*.md`: el pie dice qué tiene que mostrar.
3. Si son muchas, estimar el costo antes de arrancar: entre 10k y 20k tokens
   por figura, porque se dibujan las dos versiones y la mejorada lee además
   la página y el transcript. Una sola versión costaba entre 3k y 10k, según
   cuántas vueltas hicieran falta.

## Dibujar

Dos archivos por figura, con el mismo nombre que el recorte: la versión fiel
en `figuras/clase-NN/v1/<nombre>.tex` y la mejorada en
`figuras/clase-NN/<nombre>.tex`. Las dos tienen la misma forma:

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
que queda chico, y lo mismo vale para un mensaje perdido o un timeout que
corta una espera. Y las fórmulas se escriben como texto, con `\var{W}` para
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
  El PNG de `pdftoppm` lo exagera: a 130 dpi un trazo de 1,26 px sale de 1 o
  de 2 px según dónde caiga, con cualquier modo de líneas finas. El grosor
  que importa es el del SVG en el navegador, y se mira ahí.
- Las celdas de `\tira` dibujan cada una su borde, así que el borde que
  comparten dos celdas se traza dos veces y, medido en el navegador, sale
  hasta un 15 % más oscuro que el contorno. Si se nota, dibujar las celdas
  con `draw=none` y trazar una sola vez el contorno y los separadores: la
  diferencia baja al 7 %, que ya es antialias. En la clase 13 se resolvió así
  adentro de `fan-out-con-log` y `replicacion-de-particiones`, sin tocar
  `formas.tex`.
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

### Lo que el usuario fue pidiendo

Los rótulos van en castellano, aunque en la pizarra o en el libro estén en
inglés: las figuras del Saltzer de la clase 1 se tradujeron todas. Se quedan
en inglés los términos que la materia usa así, como master, primary, backups,
stub o timeout, que son los mismos que aparecen en el texto. El redibujo
también simplifica: lo que no aporta a lo que explica el párrafo se saca, y
lo secundario que sí conviene dejar va en gris, con `suave` en el trazo o
como relleno, para que lo principal se lea primero.

Las flechas dicen qué son por el trazo: un pedido es `msg`, sólido, y una
respuesta es `respuesta`, punteada. El color no se usa para decorar:
`acento` es solo para fallas y rechazos, y `segundo` para lo aceptado o para
una segunda serie que hay que distinguir de la primera. Todo lo demás va en
`tinta`.

En los diagramas de tiempo, los recuadros agrupan las líneas de vida que
viven en la misma máquina, en `suave`, con el rótulo afuera, arriba del
recuadro, y no adentro, donde compite con los rótulos de las líneas. Como no
todos los lectores saben leer un diagrama de tiempo, la primera vez que
aparece uno en una página va precedido por un párrafo breve que lo explica,
en la prosa del apunte: qué es cada recuadro y cada línea, que el tiempo corre
hacia abajo, qué es una flecha llena y una punteada, qué marca la cruz. Así
quedó el de la sección 5 de la clase 1, antes de `at-least-once`.

Cuando varias figuras comparan variantes de lo mismo —las semánticas de
entrega, los modelos de integración—, todas usan la misma entrada (el mismo
pedido, los mismos mensajes) y la misma geometría, para que la diferencia se
lea en el resultado y no en el dibujo. Esas familias se generan con un script
que escribe los `.tex` a partir de una geometría compartida, en lugar de
copiar a mano y que se desalineen. Si el script arma el TikZ desde Python
con `%` o `.format`, choca con los `%` de los comentarios LaTeX y con las
llaves: escribir la plantilla tal cual, con placeholders como `@Y@`, y
reemplazarlos con `.replace`. El script es un andamio: se commitean los
`.tex` que genera.

## La versión mejorada

La mejorada se dibuja a partir de tres cosas, y no solo del recorte: el
párrafo de la página donde va la figura y los que lo rodean, el pie de la
figura, y el tramo del transcript donde el profesor la explica. El
transcript está en `clases-apuntes`, `raw/claseM/clase.es.txt` (M sale de
`FUENTE_POR_CLASE`), y se lee por tramos con `grep -n`, no entero. Con eso
se decide qué tiene que mostrar el dibujo: qué idea del texto se apoya en
él, qué hay en la pizarra que no aporta a esa idea, qué falta para que se
vea. A eso se suma lo de siempre al mejorar, simetría y alineamiento, y lo
que está en "Lo que el usuario fue pidiendo".

Lo que la mejorada cambia respecto de la fiel, y sobre todo lo que agrega
que no está en la pizarra, se anota en `figuras/clase-NN/cambios.json`
(`{"nombre": "texto LaTeX"}`), y se le avisa al usuario antes de pasarle el
PDF. Si para una figura la fiel ya muestra bien lo que dice el texto, la
mejorada puede ser la misma con retoques, y la nota lo dice.

Para una clase que ya tiene solo la versión fiel, como las que se
redibujaron antes de este flujo, es la misma segunda mitad: se mueven los
`.tex` a `v1/` y se dibujan las mejoradas en su lugar.

## Compilar y mirar

```sh
python3 scripts/render_figuras.py --clase N --png
```

Compila las mejoradas, los `.tex` de `figuras/clase-NN/`; `v1/` lo ignora.
Deja un `.svg` y un `.png` por figura en `figuras/salida/clase-NN/`, que git
ignora. Las fieles no tienen ese paso propio: se miran en el PDF con las
tres opciones, que las compila. Si la fuente no tiene un carácter, el script avisa (`AVISO … la fuente
no tiene →`): lualatex no falla, deja el hueco. Mirar el PNG **después de cada compilación, también después de cada
arreglo chico**: un subíndice corrido o un rótulo pisado no se ven sin
mirarlos. Cosas que hubo que corregir en la prueba: la curva de un gráfico con
una S rara al arrancar, una flecha despegada del punto al que señalaba, una
cruz que pisaba el rótulo de la flecha, un rótulo flotando sin nada al lado.

## Elegir: el PDF con las tres opciones

```sh
python3 scripts/comparar_figuras.py --clase N
```

arma `figuras/salida/clase-NN/revision-clase-NN-mejoradas.pdf`: un A4 por
figura, en el orden del apunte, con la pizarra y la versión fiel arriba, la
mejorada abajo con la grilla en cm, y al pie la nota de `cambios.json`. Las
tres van numeradas (1. pizarra, 2. versión fiel, 3. versión mejorada). Una
figura a la que le falta la fiel o el recorte queda fuera, con un aviso. El
PDF se arma siempre y se le pasa al usuario, pero la elección no se hace
sobre él: es la referencia que tiene abierta mientras se le pregunta figura
por figura (ver "Cómo aprueba el usuario").

## Feedback del usuario: el PDF de revisión

Una vez elegidas, las correcciones de dibujo se marcan a mano encima, no se
describen con palabras. Para eso:

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

## Cómo aprueba el usuario

Con una clase entera, el usuario prefiere que se dibujen todas de una, no de
a una por vez, pero con la estimación de costo antes de arrancar (ver "Antes
de dibujar") para poder elegir. Después se arma el PDF con las tres
opciones de todas las figuras pendientes y se le pasa, como referencia.

La elección no se hace en el PDF: se pregunta directamente de a una por
chat, todas las figuras, con una `AskUserQuestion` por figura. Es el
circuito que en la clase 13 el usuario dijo que funcionó mejor, y pidió
usarlo desde la primera figura, sin una ronda previa sobre el PDF. Las opciones son la mejorada, primera y
recomendada, la versión fiel, el recorte y "necesita cambios". La pregunta
nombra la página del PDF y dice en dos líneas qué muestra la mejorada y qué
se pierde respecto de la pizarra. Si el usuario pide un cambio, se corrige,
se recompila, se le manda solo el PNG de esa figura con `SendUserFile` y se
vuelve a preguntar "¿Queda así?" antes de pasar a la siguiente. Así las
correcciones salen chicas y concretas, y no hace falta mandar otro PDF ni
anotar en Xournal++. El PDF anotado de la sección anterior queda para lo que
cuesta decir con palabras, como mover una pieza a una altura de la grilla.

Si una figura no convence en ninguna de sus versiones, se le dibujan
alternativas aparte, como en el caso de las figuras que no explican bien el
texto, y el usuario elige.

## Si queda a medias

Si el trabajo queda a medias, dejar un `figuras/clase-NN/ESTADO.md` con lo
hecho, lo pendiente y lo que se aparta de la pizarra, para retomarlo desde
otra máquina (la memoria de Claude no viaja con el repo). Se borra, junto con
`v1/` y `cambios.json`, antes de abrir la PR: así se hizo con la clase 14.

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

El pie se escribe en prosa, primero el concepto y después lo que muestra el
dibujo: "at-least-once: se pierden las respuestas y el stub reintenta después
de cada timeout; los tres pedidos llegan, y la aplicación del servidor suma
tres veces". Sin `<code>`, sin rayas, y sin recorrer el dibujo por posición
("a la izquierda…, a la derecha…"): el lector tiene la figura al lado, lo
que le falta es qué significa. Es el estilo de los pies de las clases 1 y 14.

Una figura nueva, que no está en la pizarra, va como cualquier otra
`figura-con-imagen`, con `<span class="figura-ref">agregada al apunte; no está
en la pizarra</span>`.

El SVG sale agrandado 1,5× (`--escala`) porque el CSS solo pone
`max-width: 100%`, y a tamaño natural queda chico al lado de los PNG de
1400 px.

### Mirarlas en el sitio desde un worktree

`preview_start` y `.claude/launch.json` levantan Jekyll sobre la carpeta
principal del repo, no sobre el worktree, así que muestran las páginas de
`main` y no las de la branch. Desde un worktree se levanta a mano, en una
pestaña de terminal, con puertos propios para no chocar con otra sesión que
tenga el suyo andando, y con el destino en el scratchpad para no ensuciar el
worktree con `_site/`:

```sh
bundle exec jekyll serve --source . --destination <scratchpad>/_site \
  --port 40NN --livereload --livereload-port 357NN
```

con `NN` el número de la clase. Antes de mostrarle nada al usuario,
confirmar que los SVG que usa la página respondan 200
(`curl -sI http://127.0.0.1:40NN/assets/clase-NN/<nombre>.svg`): un `src`
con un nombre mal escrito no rompe el build, deja el hueco.

## Cerrar la clase

La adopción de una clase sale en tres commits, en este orden: primero los
`.tex` (y lo que se haya sumado a `formas.tex` y `catalogo.tex`); después las
páginas que pasan a los SVG, con los SVG que usan y la línea de CLAUDE.md que
dice qué clases usan SVG ("Hoy usan SVG la clase 1 …"), que se actualiza con
la clase nueva y sus excepciones; y al final los ajustes de texto que
salieron de la revisión, como los pies reescritos o el párrafo que explica un
diagrama de tiempo. Así quedó la PR #36.

Antes de esos commits se resuelve lo que no se eligió: si para una figura
ganó la versión fiel, su `.tex` sale de `v1/` y pisa la mejorada en
`figuras/clase-NN/`; si ganó la mejorada, la fiel se descarta; y si ganó el
recorte, la página no cambia y el `.tex` que no se adopta se borra. Después
se borran `figuras/clase-NN/v1/`, `cambios.json` y `ESTADO.md`, si quedaron:
son de trabajo y no se versionan, y no llegan a la PR.
