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

Un punto que tiene que caer sobre una curva, como la interfaz sobre el borde
de un óvalo, se ubica con coordenadas de la curva y no calculado a mano:
`(0,0) ++(20:3.0 and 2.3)` en vez de `(2.82,0.78)`.

## Compilar y mirar

```sh
python3 scripts/render_figuras.py --clase N --png
```

Deja un `.svg` y un `.png` por figura en `figuras/salida/clase-NN/`, que git
ignora. Mirar el PNG **después de cada compilación, también después de cada
arreglo chico**: un subíndice corrido o un rótulo pisado no se ven sin
mirarlos. Cosas que hubo que corregir en la prueba: la curva de un gráfico con
una S rara al arrancar, una flecha despegada del punto al que señalaba, una
cruz que pisaba el rótulo de la flecha, un rótulo flotando sin nada al lado.

Para que el usuario las revise, conviene armarle una página que muestre el
recorte y el redibujo lado a lado, con una línea por figura que diga qué se
aparta de la pizarra.

## Feedback del usuario

El usuario puede marcar las correcciones dibujando arriba del PNG, en Vista
Previa, en el iPad o en lo que tenga a mano, y pasar la imagen anotada, ya sea
pegándola o con su ruta. Leer la imagen, listar qué entendimos de cada marca
antes de tocar el `.tex`, y si una marca es ambigua preguntar. Si en vez de
eso deja comentarios en la página de antes/después, se leen con la
herramienta de comentarios del artifact.

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
