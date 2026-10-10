---
title: "3. Qué significa que una lectura sea correcta"
parent: "Clase 11 — Spanner"
nav_order: 3
---

# 3. Qué significa que una lectura sea correcta

Que el two-phase commit tarde entre 10 y 100 milisegundos sería una mala noticia si todas las transacciones fueran así. Lo bueno es que no: las read-only son casi todas las transacciones del sistema, del orden del 99,9%.

{: .nota }
> En la clase el porcentaje se atribuye al paper, que no lo enuncia como tal. Sí se lo puede calcular de su tabla VI, la que mide el tráfico real de F1 durante veinticuatro horas: 21.500 millones de lecturas contra 31,2 millones de commits de un solo sitio y 32,1 millones multisitio. Las lecturas son, entonces, el 99,7% de las operaciones. Lo que el paper sí afirma en su sección 2 es algo distinto y también relevante: que la mayoría de las transacciones involucra un único grupo de Paxos, y por eso puede saltearse el transaction manager.

Si optimizamos las read-only y dejamos donde están las de escritura, con su commit lento, optimizamos la mayor parte del sistema. Este sistema se usa principalmente para leer, y por eso todo el esfuerzo y toda la rareza está en cómo implementaron las read-only.

¿Cómo consiguen esa baja latencia? Primero, leen de la réplica local. Ese es el primer punto que resuelven, y es importante: no hay que coordinar con todo el mundo para leer, sino que se trata de leer todo de las versiones locales que están al lado. Segundo, no toman locks. Los read locks y write locks que acabamos de recorrer son solo para las de escritura. No hay two-phase locking, y la forma de resolverlo es completamente diferente.

Lo que se logra es snapshot isolation. Recordemos que las escrituras garantizan serializabilidad: aunque las transacciones no ocurran realmente una después de otra, conceptualmente es como si así fuera. Podemos imaginarnos un log imaginario de transacciones, una fila de casillas: un read, otro read, un write, otro read, y así. Entre cada una se va formando un snapshot consistente.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-11/cinta-del-log.jpg' | relative_url }}" alt="Cinta del log de transacciones con una lectura que mezcla dos transacciones">
  <figcaption>
    <span class="figura-label">Figura</span>
    la cinta del log imaginario de transacciones (read | read | write | read | …), una lectura de X e Y que cae entre dos celdas —el snapshot del que hay que leer— y en rojo el caso de la lectura que mezcla dos transacciones distintas
    <span class="figura-ref">notas pág. 2 / pizarra pág. 2</span>
  </figcaption>
</figure>

Si hacemos un `begin`, un `read` de X, un `read` de Y y un `end`, lo que no podemos hacer es leer X de un lugar del log y Y de otro. Tenemos que leer los dos del mismo snapshot. Puede ser este, el de al lado o cualquier otro, pero no una mezcla. Eso es snapshot isolation, y eso es, básicamente, una transacción read-only.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-11/transaccion-read-only.png' | relative_url }}" alt="Transacción read-only: BEGIN, READ x, READ y, END">
  <figcaption>
    <span class="figura-label">Figura</span>
    bloque BEGIN / READ x / READ y / END
    <span class="figura-ref">notas pág. 2 / pizarra pág. 2</span>
  </figcaption>
</figure>

Ahora, ¿qué considera correcto Spanner, más que eso? Se autoimpusieron algo que llaman external consistency, que en lenguaje coloquial es: si la transacción T1 hace commit antes que T2, entonces T2 ve a T1.

La clave es ese "antes": es antes en tiempo físico. No hay causalidad ni nada parecido. Si mandamos una transacción T1 que escribe X, y físicamente después mandamos T2 que lee X, esa lectura tiene que ver la escritura, simplemente porque ocurrió antes.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-11/external-consistency.png' | relative_url }}" alt="T1 escribe X y T2, que empieza después, lee X">
  <figcaption>
    <span class="figura-label">Figura</span>
    los dos segmentos de external consistency — T1 escribiendo X y T2 leyendo X, con una flecha curva desde el final de T1 al comienzo de T2, sobre el eje de tiempo físico
    <span class="figura-ref">notas pág. 3 / pizarra pág. 3</span>
  </figcaption>
</figure>

Esto debería sonarnos: es prácticamente la definición de linealizabilidad. Las transacciones tienen que respetar el tiempo físico. Y eso es un problema serio.

La external consistency es la combinación de dos cosas: serializabilidad —leer snapshots— más el requerimiento de tiempo físico, que es la linealizabilidad. Son dos términos difíciles de pronunciar y dos requerimientos distintos, porque la serializabilidad no tiene ningún componente de tiempo real: lo que le importa es que las lecturas sean consistentes.

Veámoslo con un ejemplo. La transacción uno setea x = 1, y = 2, y la dos hace x = 3, y = 4. En un momento posterior a las dos hacemos un read de x y de y. Uno de los resultados posibles es x = 1, y = 2.

Debería parecernos raro que eso sea aceptable. Pero no viola la serializabilidad: es como si esa lectura hubiera caído en el pasado. Estamos leyendo un snapshot, y por lo tanto es una lectura serializable.

Lo que vamos a decir nosotros es que sí, que es serializable, pero que estamos leyendo algo del pasado y que no quisiéramos leer eso. Es justamente lo que debían decir los ingenieros que usaban el sistema: no quiero lecturas del pasado; si mandé x = 3, y = 4, y después leo, quiero ver x = 3, y = 4. Ese segundo requerimiento, el temporal, es la linealizabilidad. El caso dibujado es serializable y no es linealizable, porque leyó algo del pasado.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-11/serializable-no-linealizable.png' | relative_url }}" alt="Lectura que devuelve el snapshot de T1: serializable pero no linealizable">
  <figcaption>
    <span class="figura-label">Figura</span>
    la cinta de snapshots con las celdas de T1 (x=1, y=2) y T2 (x=3, y=4), y la lectura posterior que devuelve x=1, y=2, rotulada &quot;serializable ✓ / linealizable ✗&quot;
    <span class="figura-ref">notas pág. 3 / pizarra pág. 3</span>
  </figcaption>
</figure>

Algo más sobre la linealizabilidad. Aunque los ejercicios de esa clase eran siempre cosas superpuestas donde había que encontrar el punto de linealización, su propiedad fundamental es la más intuitiva: si envío un request, recibo la confirmación, y después leo lo que escribí, tengo que verlo. Linealizabilidad es otra forma de decir consistencia fuerte.

Queremos, entonces, que esto sea serializable y fuertemente consistente, y las dos cosas sin usar locks. Porque si usáramos locking pesimista las dos se lograrían automáticamente —no es inmediato explicarlo, pero pensándolo con detenimiento se ve—; el problema es que los locks pesimistas justamente bloquean, y nosotros queremos alta concurrencia. Eso es lo que queremos lograr: esas dos cosas, sin usar locks.

---
