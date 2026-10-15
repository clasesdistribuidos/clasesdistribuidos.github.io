---
name: redibujar-figuras
description: >-
  Redibuja en TikZ una figura de la pizarra ya recortada en `assets/clase-NN/`,
  para que el sitio se vea más de libro, y la compila a SVG con
  `scripts/render_figuras.py`. Usar cuando el usuario pide pasar una figura (o
  varias) a TikZ, o corregir una ya redibujada. Está en prueba: no reemplaza
  el recorte de la skill `recortar-figuras` ni toca las páginas salvo que el
  usuario lo pida.
---

# Redibujar figuras en TikZ

La figura recortada de la pizarra es la referencia de *qué* hay que dibujar;
el redibujo cambia *cómo* se ve. No se inventa contenido: si algo no está en
la pizarra ni en el pie de la figura, no va, y si se agrega un rótulo para que
se entienda, se le avisa al usuario.

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

`figuras/estilo.tex` trae todo lo compartido y no se redefine por figura. El
entorno `figura` recorta la página al dibujo, y estos son los estilos y
colores que trae:

- `caja` para procesos, nodos y stores; `msg` para las flechas de mensajes;
  `vida` para las líneas de vida de un diagrama de secuencia.
- `etiq` para los rótulos, y `cod` (monoespaciada) para llamadas como
  `send(record, id)` o `check(id)`.
- Los colores: `tinta`, el trazo normal; `suave`, para las anotaciones
  secundarias, que van en gris y con llave cuando agrupan; `acento`, el rojo
  de la pizarra (watermark, rechazos, los rótulos que el profesor escribió en
  rojo); `segundo`, el verde de la pizarra, para una segunda serie.
- Un rechazo se marca con una cruz roja hecha con dos líneas de 1.4pt, no con
  el carácter ×, que queda chico.
- Las fórmulas se escriben como texto, con `\var{W}` para las variables y `≥`
  en unicode. La matemática en Computer Modern no combina con la Helvetica, y
  con TeX Live basic no hay `unicode-math`.

Si un estilo hace falta solo en una figura (un círculo para componentes, por
ejemplo), se define en el `tikzpicture` de esa figura. Si se repite en varias,
se sube a `estilo.tex`.

Trampas que ya aparecieron:

- Helvetica Neue no tiene → ni ∥. La flecha dentro de un texto va como
  `\tikz[baseline=-0.55ex]\draw[->] (0,0) -- (0.5,0);`; ∥, como `$\parallel$`.
- `\@car` y compañía no andan en un `.tex` común. Para rótulos como p₁,
  iterar con dos variables: `\foreach \l/\i in {p/1, q/2}` y
  `\var{\l}\textsubscript{\i}`.
- La punta de una flecha que llega a un evento pisa el rótulo que está de ese
  lado: ponerlo del lado opuesto (`above right` si la flecha llega desde
  arriba a la izquierda), con un parámetro de lado por evento en el
  `foreach`.
- En el PNG algunas líneas se ven más gruesas: es redondeo de píxeles, no el
  dibujo. Se confirma con `grep -o 'stroke-width="[^"]*"' x.svg | sort | uniq -c`.
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

`estilo.tex` pide **Helvetica Neue** y **Menlo** por nombre, con `fontspec`:
vienen con macOS. En Linux o Windows hay que instalarlas o cambiarlas ahí
(TeX Gyre Heros y DejaVu Sans Mono andan), y avisar que el resultado cambia.

## Llevarlas al sitio

Ninguna página usa los SVG todavía. Si el usuario pide verlas en el sitio:

```sh
python3 scripts/render_figuras.py --clase N --salida assets/clase-NN
```

y en el `.md`, cambiar `.png` por `.svg` en el `src` del `<img>`. Se queda
todo lo demás: el pie y la `figura-ref`, que sigue diciendo de qué página de
la pizarra salió el dibujo. El SVG sale agrandado 1,5× (`--escala`) porque el
CSS solo pone `max-width: 100%`, y a tamaño natural queda chico al lado de los
PNG de 1400 px.

Adoptarlo en serio (reemplazar recortes en una clase publicada) es una
decisión del usuario, y cuando la tome hay que actualizar la regla "las
figuras no se dibujan de nuevo" del CLAUDE.md.
