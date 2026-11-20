# Clase 14 en TikZ: dónde quedó

Notas de trabajo para retomar el redibujo de la clase 14 (procesamiento de
streams, MillWheel) desde otra máquina o en otra sesión. No es contenido del
sitio: `figuras/` está excluida del build. Borrar este archivo cuando la clase
esté adoptada.

## Hecho (2026-11-19)

- **20 de las 21 figuras redibujadas.** `low-watermark-lag` no se redibuja: es
  la figura 15 del paper, un gráfico de latencias medidas, y rehacerlo sería
  inventar datos. Se queda el recorte.
- **Dos versiones de cada una:**
  - `figuras/clase-14/v1/*.tex`: la primera, fiel a la pizarra. Seis salieron
    de los borradores de octubre de la branch `figuras-tikz` (PR #23):
    `event-time-contra-processing-time`, `master-y-nodos`,
    `pipeline-de-watermarks`, `protocolo-exactly-once`,
    `reasignacion-con-epoch` y `shuffle-por-rangos`.
  - `figuras/clase-14/*.tex`: la mejorada, que el usuario pidió "a partir del
    concepto, buscando también el contexto del transcript", con simetría y
    alineamiento. Qué cambió en cada una está en `cambios.json`, que es el
    pie de cada página del PDF de comparación.
- **Biblioteca:** `formas.tex` suma `\stream` (el tubo de Kafka), con su fila
  en `catalogo.tex`.
- **Script nuevo:** `scripts/comparar_figuras.py --clase 14` arma
  `figuras/salida/clase-14/revision-clase-14-mejoradas.pdf` (pizarra y v1
  arriba, mejorada con grilla abajo, y la nota al pie). El PDF de revisión
  común (`render_figuras.py --revision`) compara la pizarra con la mejorada.

Las páginas `_clases/clase-14/*.md` todavía usan los PNG y no hay SVG en
`assets/clase-14/`: no se adoptó nada.

## Pendiente

1. **El usuario revisa el PDF de comparación**: marca en Xournal++ (azul o
   magenta, nunca rojo) y dice qué páginas tocó. Abrir solo esas
   (`pdftoppm -png -r 100 -f N -l N`), listar qué se entendió de cada marca
   antes de tocar los `.tex` y preguntar lo ambiguo.
2. **Elegir, figura por figura, v1 o mejorada.** Si gana v1, copiarla sobre la
   de `figuras/clase-14/`. Después se borra `v1/` y `cambios.json`.
3. **Adoptar** como dice la skill `redibujar-figuras`: `render_figuras.py
   --clase 14 --salida assets/clase-14`, commitear solo los SVG que se usan,
   cambiar `.png` → `.svg` en el `src` y ajustar `alt` y pie si el redibujo
   agrega algo. La `figura-ref` se queda.
4. PR de `figuras-clase-14` contra `main`.

## Lo que se aparta de la pizarra (para mirar con atención)

Agregado o inventado por nosotros, no está ni en la pizarra ni en el texto:

- `event-time-y-processing-time`: el processing time de ejemplo, 8:00:07 (lo
  pidió el usuario).
- `master-y-nodos`: las asignaciones de cada nodo (window counter [a–m), …)
  son un ejemplo con los cómputos de Zeitgeist. Adentro del master, en vez
  del grafo de la pizarra, un pentágono regular de réplicas: Multi-Paxos
  (lo pidió el usuario, 2026-11-20).
- `watermark-log-particionado`: los números de las celdas, salvo 10, 8 y 12.
- `genealogia-de-millwheel`: repensada a partir del último párrafo del
  apunte (el modelo de programación se desprendió del motor). El interior de
  Dataflow (worker y Windmill) y las primitivas debajo de MillWheel salen del
  texto, no de la pizarra.
- `protocolo-exactly-once`: el final (ack de C y `delete(producciones)`) sale
  del paper, §6.1 (strong productions), no de la pizarra. Lo pidió el usuario
  desde la sesión de las diapositivas, que la usa en la diapositiva 37 del
  deck de la clase 14. Después pidió sacarle los textos en gris: lo que se
  guarda quedó en la llamada, `update(estado, producciones, timers, id)`.
- `sistema-de-streaming`: el destino del RPC era un trazo sin rótulo; ahora
  dice "otro sistema".

Decisiones de color: el evento atrasado va en rojo (`acento`) en
`linea-de-tiempo-zeitgeist` y `micro-batching`; por eso en `micro-batching`
los cortes, rojos en la pizarra, pasan a negro punteado. Los watermarks van
siempre en rojo. En `join-stream-stream` el segundo stream va en verde, como
en la pizarra.

Las dos figuras del paper (`grafo-de-computos-zeitgeist`,
`arquitectura-de-millwheel`) mantienen los rótulos en inglés.

## Fuentes

- **El transcript** de la clase está en el repo de trabajo `clases-apuntes`,
  `raw/clase16/clase.es.txt` (la clase 14 del sitio es la grabación 16, ver
  `FUENTE_POR_CLASE` en `scripts/recortar_figuras.py`). Hay un índice de
  pizarra y notas en `raw/clase16/notas/indice.md`. Se leyó por tramos, con
  `grep -n` por tema (Britney, lote, enriquec, join, punto de corte, perfect,
  shuffle, master, zombi, at most, autoridad, Flink), no entero: son ~18k
  palabras.
- Los recortes de referencia están en `assets/clase-14/`.

## Cómo trabaja el usuario (para no repetir errores)

- Antes de algo caro (muchas imágenes, el transcript entero), **estimar el
  costo y dejarlo elegir**.
- Las correcciones se hacen en el texto o en la figura; nada de notas del tipo
  "en la clase se dijo…".
- Figuras que comparan variantes: tabla, misma entrada en todas las filas, y
  que el resultado muestre la diferencia (así quedó `semanticas-de-entrega`).
- Al mejorar, pide **simetría** (piezas equivalentes iguales y a la misma
  distancia) y **alineamiento** (lo que se corresponde, en la misma fila o
  columna).
- Push: el remote solo acepta la cuenta `gh` `eespina-fiuba` (`gh auth
  status`; si no está activa, `gh auth switch -u eespina-fiuba`).

## Choque conocido

En la máquina donde se empezó, la clase 13 estaba a medias sin commitear
(branch `figuras-clase-13`) y agrega a `formas.tex` un estilo `cola`. Está en
otro bloque del archivo que `\stream`, así que el merge debería entrar solo.
