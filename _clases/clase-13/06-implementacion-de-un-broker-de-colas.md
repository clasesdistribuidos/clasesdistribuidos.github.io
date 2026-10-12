---
title: "6. Implementación de un broker de colas"
parent: "Clase 13 — Sistemas de mensajería"
nav_order: 6
---

# 6. Implementación de un broker de colas
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Nos queda el ejercicio pendiente, ahora con la otra punta: cómo implementar un broker de producer-consumer, de la familia del que venimos usando. Lo vamos a hacer de manera incremental, desde la versión más rudimentaria, agregándole de a una las propiedades que le faltan.

La salvedad metodológica pesa aquí todavía más. De SQS por dentro no hay documentación pública: ni paper ni especificación. Lo que sigue se reconstruye con información que se consigue por ahí y describe cómo funcionaba hace unos veinte años, no cómo funciona hoy, que seguramente sea muy distinto. Eso no le quita valor: si nos quedáramos en la API y los casos de uso, la clase se reduciría a una promoción de los productos de Amazon. Y lo notable es que para ver cómo se implementan no hace falta ninguna técnica nueva, solo las que aprendimos en la materia.

## Opción 1: base de datos como cola

La primera opción es la no distribuida, y es literalmente lo que dice su nombre: un broker que atiende los RPCs de productores y consumidores, y detrás una base de datos cualquiera. Vamos a usar Postgres, la más común.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    opción 1, la versión no distribuida — una flecha entrante desde arriba hacia un rectángulo &quot;BROKER&quot;, y de ahí una flecha hacia abajo a un cilindro de base de datos rotulado &quot;POSTGRES&quot;
    <span class="figura-ref">notas pág. 6 / pizarra pág. 12</span>
  </figcaption>
</figure>

El dibujo no tiene misterio; lo interesante es la pregunta de atrás: ¿cómo se implementa con Postgres el visibility timeout? Era importante por dos razones: que no haya varios consumidores procesando el mismo mensaje, y que el mensaje se restaure solo cuando el timeout expira. Con saber SQL alcanza para seguir el razonamiento.

La tabla es lo mínimo imaginable: un ID, el mensaje y una columna con el visibility timeout. Tres columnas.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la tabla de la cola — tres columnas rotuladas &quot;ID | MSG | VISIBILITY_TO&quot; y dos filas vacías
    <span class="figura-ref">pizarra pág. 14</span>
  </figcaption>
</figure>

Y las dos operaciones.

```sql
-- send: encola un mensaje, visible de entrada
INSERT INTO cola (mensaje, visibility_timeout) VALUES ($1, now());

-- receive: toma un mensaje visible y lo esconde 60 segundos
UPDATE cola
   SET visibility_timeout = now() + interval '60 seconds'
 WHERE id = (SELECT id FROM cola
              WHERE visibility_timeout < now()
              ORDER BY id
                FOR UPDATE SKIP LOCKED
              LIMIT 1)
RETURNING id, mensaje;
```

El `send` es trivial: un `INSERT`, una fila nueva, con el mensaje, un ID seguramente autoincremental —no importa cómo se genere— y el visibility timeout en `now()`. Esa es la primera pieza del mecanismo: un timeout puesto en el presente significa que cualquier consumidor que llegue después lo va a encontrar ya en el pasado, y por eso lo va a poder leer.

El `receive` es el interesante, y tiene una forma un poco inusual: un `UPDATE` que hace un `SELECT` al mismo tiempo. La clave está en el `WHERE` del select interno, una sola condición: las filas cuyo visibility timeout ya expiró. Si el timeout está en el pasado, el mensaje es visible; esa es toda la definición, y por eso el `send` lo inicializaba en `now()`.

El resto es accesorio, aunque cada pieza está por algo. El `FOR UPDATE SKIP LOCKED` lockea la fila por concurrencia: si dos consumidores llegan juntos, el segundo pasa de largo a la fila siguiente en lugar de llevarse el mismo mensaje. El `LIMIT 1`, porque queremos un solo valor. Y el orden por ID hace que la entrega sea FIFO; implementado así, va a ser exactamente FIFO, una garantía que estos sistemas en general no dan.

Falta la parte que hace el trabajo de fondo: antes de devolver el mensaje le adelantamos el visibility timeout sesenta segundos, y durante ese minuto ningún otro `receive` va a coincidir con esa fila. Si el consumidor termina y borra el mensaje, la fila desaparece. Si muere en el medio, pasan los sesenta segundos, el timeout vuelve al pasado y la fila reaparece. Con eso está implementada una cola con visibility timeout en dos sentencias de SQL, usando una tabla como cola.

Los problemas son igual de evidentes: no es escalable y no es tolerante a fallas. Lo segundo merece precisión, porque el punto débil no está donde uno esperaría. El broker es stateless —todo lo que sabe está en la base—, así que si falla se levanta otro. El problema es la base: si muere ese Postgres, se van todos los mensajes. Vamos a tener que replicar eso.

Lo anterior parece una idea muy poco recomendable, y sin embargo no lo es. Es una técnica poco difundida, pero implementar la cola como una tabla dentro de la propia base de datos tiene una ventaja concreta, y para verla hay que volver al problema que dejamos abierto.

En el pipeline de transcodificación, el frontend tenía que guardar el video en S3 y encolar el pedido en SQS, dos sistemas que no comparten nada. Eso es una especie de transacción distribuida: tienen que pasar las dos cosas o ninguna. La forma general del problema aparece todo el tiempo: un frontend que guarda algo en una base de datos y además manda un `schedule job` por una cola. Necesitamos atomicidad porque el que consuma el job va a buscar metadata a la base: si programamos el job y no llegamos a guardar porque la base se cayó o se rompió la red, el worker no encuentra la metadata y falla. O peor, el job llega antes de que la base esté actualizada.

El truco, que se usa mucho más de lo que su aspecto sugeriría, es no usar una cola aparte sino implementarla como una tabla más de la misma base. Si lo que queremos es una transacción, Postgres nos da transacciones: escribir en la cola y en una tabla de negocio pasa a ser una única transacción convencional, sin coordinación entre sistemas.

El worker cambia poco: en lugar de hacer `receive` contra un servicio de cola, consulta la tabla cada tanto —exactamente el `receive` que escribimos en SQL— y toma el job. Y como esa tabla se escribió transaccionalmente con la metadata, si obtiene el job también va a obtener la metadata. Es atómico, sin construir nada.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el flujo del patrón cola-como-tabla — un cuadrado &quot;FE&quot; con una flecha hacia abajo a un cilindro de base de datos; a la derecha un cuadrado &quot;WORKER&quot; con una flecha larga curva rotulada &quot;RECEIVE&quot; que vuelve al cilindro; y del worker una flecha hacia un cilindro &quot;SQS&quot; y de ahí a una pila de rectángulos
    <span class="figura-ref">pizarra pág. 14</span>
  </figcaption>
</figure>

Puesto así parece una mala práctica —usar una base relacional como broker tiene todo el aspecto de una mala decisión—, y sin embargo el patrón está muchísimo más extendido de lo que uno creería. Quien haya trabajado con colas probablemente se lo cruzó o lo implementó más de una vez. Es tan práctico que merecería un ejercicio en profundidad para él solo.

Tiene incluso bibliografía propia. Salió hace poco un libro dedicado a resolver con Postgres cosas para las que uno instalaría un sistema aparte, con un capítulo entero sobre Postgres como cola de mensajes. Su lectura es muy recomendable. Ahí aparece algo que conviene saber: el patrón se puede implementar a mano, como acabamos de hacer, pero también hay extensiones de Postgres que ya lo traen resuelto. Con ellas se consigue justo lo que buscábamos: implementar una transacción distribuida eludiendo hacer una transacción distribuida.

{: .nota }
> El libro es Denis Magda, *Just Use Postgres! All the database you need*, Manning Publications, noviembre de 2025. El capítulo es el 11, «Postgres as a message queue», y está en la parte final del libro —parte 3, «Extensions and the broader ecosystem»—, aunque no es el último. Cubre cuándo y por qué conviene usar Postgres como cola, cómo implementar una cola propia con las capacidades nativas del motor, cómo notificar a los suscriptores con `LISTEN`/`NOTIFY` en lugar de hacer polling, y el uso de la extensión pgmq como solución ya hecha, que es la que corresponde a los «plugins» que se mencionan en la clase.

Y las piezas se combinan. Si de todos modos queríamos escribir en SQS —porque la flota consumidora ya existe—, el worker que consume de la tabla puede actuar de intermediario: toma el job y recién ahí lo manda a SQS, donde espera la flota. Lo que hubiera sido escribir en la base y en SQS directamente, con el riesgo de que una escritura fallara y quedara todo a medio hacer, se resuelve con la tabla en el medio: el paso frágil ocurre después de que la transacción ya cerró.

Hecho el elogio, la objeción de fondo: la materia se llama Sistemas distribuidos, y un Postgres no distribuido falla y no escala. Veamos cómo mejorar el diseño.

## Opción 2: sharding aleatorio

La opción dos ataca la escalabilidad. En lugar de un broker con una base, tres pares de broker más base, cada uno con su storage propio, y el frontend le manda el mensaje a uno o a otro. Es solamente sharding.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    opción 2, sharding — un cuadrado &quot;FE&quot; arriba con tres flechas en abanico hacia tres rectángulos &quot;BROKER&quot; en fila; cada broker tiene debajo su propio cilindro de base de datos, y el primero tiene un punto verde dentro, que es el mensaje guardado
    <span class="figura-ref">notas pág. 6 / pizarra pág. 15</span>
  </figcaption>
</figure>

¿Qué tiene de particular shardear colas de mensajes? Que es fácil, porque el orden no importa: no hay una secuencia, hay una gran bolsa de mensajes. Para escribir, el frontend elige un shard al azar y guarda ahí. Para leer, lo mismo: elige uno al azar y toma un mensaje, o consulta a los tres y devuelve lo primero que aparezca. Escribiendo y leyendo al azar el sistema funciona, y es muy simple. No hace falta shardear por key ni por ningún criterio, justamente porque el orden no importa.

Lo que sí se vuelve un tema es el borrado. Supongamos que el frontend eligió al azar el primer shard, encontró el mensaje y se lo devolvió al consumidor. Si al recibir el acknowledge volvemos a elegir un nodo al azar, vamos a intentar borrar el mensaje de un shard donde nunca estuvo: la operación falla y el mensaje sigue vivo hasta que expire su visibility timeout.

El truco que suelen usar los que construyen estos sistemas es que el mensaje devuelto incluya la información del shard: el consumidor recibe el mensaje y además en qué shard estaba, y al borrarlo devuelve ese dato, con lo cual el frontend sabe a cuál ir.

Parece un artificio dudoso, y en algún sentido lo es: le damos al usuario información interna para que nos la devuelva. Se atenúa no mandando el shard en claro sino encriptado, para no exponer la estructura interna: una información opaca, ilegible para él, que devuelve tal cual la recibió.

Uno diría que nadie diseñaría un sistema así. Pero volvamos a la API de SQS y al parámetro que no parecía tener razón de ser: el `ReceiptHandle`, que `ReceiveMessage` devuelve y `DeleteMessage` exige de vuelta, cuando con el ID y el nombre de la cola parecería alcanzar. La respuesta es que Amazon hace internamente exactamente esto: al escribir un mensaje elige un shard al azar y lo guarda ahí, y al borrarlo hay que decirle en qué shard estaba. Obviamente no lo presenta así: lo abstrae, lo llama `ReceiptHandle` y lo describe como un bloque de metadata encriptada cuyo contenido el usuario no puede conocer. Es un intercambio: el servicio lo entrega, el usuario lo devuelve, Amazon lo desencripta, sabe a dónde ir y borra el mensaje.

Este sharding no se parece al que venimos viendo, y ese contraste es el punto conceptual. Hasta ahora estudiamos sharding determinista: el shard sale de aplicarle una función —típicamente un hash— a la key, y cualquiera que tenga la key puede calcular dónde está el dato. Aquí el shard se elige al azar, así que nadie puede calcular dónde quedó un mensaje. La dificultad se corre de lugar: repartir es trivial y lo difícil es encontrar después lo que se guardó.

Eso tiene una consecuencia visible desde afuera. Si alguien manda un solo mensaje y enseguida hace una lectura que cae en otro shard, no encuentra nada: es como si nunca lo hubiera mandado. Con tres shards eso no es un caso de borde sino el típico: la probabilidad de acertar al primer intento es una en tres, un 33 %, así que dos de cada tres lecturas inmediatas vuelven vacías aunque el mensaje esté guardado y a salvo. La respuesta de Amazon es la que ya conocemos: consistencia eventual. El mensaje puede aparecer o no en una lectura inmediata, y la documentación lo dice sin rodeos. Esos dos tercios de fallo explican también la otra mitad de la respuesta: en la práctica los frontends hacen un par de retries antes de contestar que no hay mensajes, o prueban todos los shards, y el efecto casi nunca se nota.

{: .nota }
> La reconstrucción tiene en este punto respaldo en la documentación pública de AWS, que sin describir la implementación deja ver su forma. Al explicar el *short polling* —el comportamiento por omisión de `ReceiveMessage`— AWS dice que la consulta se hace sobre un subconjunto de los servidores que almacenan los mensajes, elegido con una distribución aleatoria ponderada, y que por eso una llamada puede devolver cero mensajes aunque la cola no esté vacía; con *long polling*, en cambio, la consulta va a todos los servidores. Por la misma razón la métrica de cantidad de mensajes de una cola se llama `ApproximateNumberOfMessages`: es aproximada porque el dato está repartido entre muchas máquinas.

¿Qué resolvimos con la opción dos? La escalabilidad: si recibimos un volumen muy alto de mensajes, agregamos brokers con sus bases y el sistema absorbe la capacidad extra. Lo que sigue sin resolver es la tolerancia a fallas: si muere una base, mueren con ella todos sus mensajes.

## Opción 3: sharding con replicación

La opción tres es sharding más replicación. Imaginemos cinco shards en fila, sin la parte de arriba, que no cambia.

Lo primero que uno piensa es en Raft, el de las clases 5 y 6 y del trabajo práctico. Se podría, pero es complicarnos la vida, porque el problema es mucho más simple: no necesitamos un log replicado, ni orden total, ni una máquina de estados determinista, sino solamente que un mensaje no se pierda si se muere una máquina. Y eso sale más barato.

Al escribir, el frontend elige un shard al azar —por ejemplo, el del medio— y le manda el mensaje. Ese shard lo escribe localmente y elige dos shards al azar para las réplicas. En el dibujo elige a sus vecinos, pero podrían ser dos cualesquiera: lo importante es que el mensaje quede copiado en dos lugares más.

Hay un detalle en lo que guarda, que es lo que permite borrarlo después: cada réplica guarda el mensaje y la lista de hosts donde quedó, el uno, el dos y el tres. Para eso el nodo que recibió la escritura elige primero a todos los destinatarios y recién después les manda el mensaje con la lista incluida. Así los tres saben dónde están las otras copias.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    opción 3, sharding con replicación — cinco cilindros en fila, los shards; una flecha entrante desde arriba cae sobre el tercero; puntos verdes dentro del 2.º, 3.º y 4.º unidos por líneas verdes horizontales con puntas de flecha hacia ambos lados, que es la replicación a los vecinos; y una flecha verde que baja del cilindro central hacia el rótulo `MSG, [H₁, H₂, H₃]`
    <span class="figura-ref">notas pág. 6 / pizarra pág. 15</span>
  </figcaption>
</figure>

Para leer, lo más simple: se elige un shard cualquiera, se leen sus mensajes, se procesan y se devuelven.

Y ahí, si no tenemos cuidado, aparece un problema con el visibility timeout y los duplicados. Si un consumidor lee del shard del medio y otro al mismo tiempo lee de una réplica, cada uno lee su propia versión del mismo mensaje y los dos lo procesan en paralelo. Podríamos hacer que el primero que lee les avise a las réplicas que ese mensaje deje de ser visible; funcionaría, sin duda. Pero complicaría notablemente un diseño que, tal como está, es el más simple de replicación de toda la materia: elegir dos nodos al azar y copiarles el mensaje, sin líderes, sin términos, sin votaciones y sin quórums.

Y es un muy buen sistema. Para aumentarle capacidad, se agregan shards; para aumentarle replicación, se configura cada nodo para que copie a tres en vez de a dos. El precio son los duplicados, que van a aparecer tantos como réplicas haya.

## Opción 3.1: replicación con primary

Lo que sigue no es una solución definitiva sino una forma posible de arreglar eso. Pongamos ahora seis nodos, para no dar la impresión de que el número siempre es tres.

El frontend escribe eligiendo un nodo al azar, como antes. Pero en lugar de dos réplicas simétricas introducimos una jerarquía: el nodo que recibe la escritura es el primary, y elige dos en orden, un secondary y un tertiary, y les escribe el mensaje. Y agregamos la regla que resuelve los duplicados: solo el primary responde mensajes.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    opción 3.1, solo el primary responde — cinco o seis círculos dispuestos en cruz; una flecha rotulada &quot;RCV&quot; y otra entrante desde la izquierda llegan al círculo central, que está tachado con una X roja y rotulado &quot;VISIBILITY TIMEOUT&quot;; de ahí salen dos flechas verdes hacia los círculos ② arriba a la derecha y ③ abajo a la derecha
    <span class="figura-ref">notas pág. 6 / pizarra pág. 15</span>
  </figcaption>
</figure>

Sigamos una lectura completa. Llega un `receive` y el frontend elige un nodo al azar; no tiene el mensaje, no devuelve nada. Elige otro; lo tiene, pero es el secondary, que no está autorizado a responder. Elige un tercero, que lo tiene y es el primary: ese lo devuelve. Cuántos intentos hace el frontend es política suya: uno solo y devolver vacío, tres, cuatro, o todos, quedándose con el primero que responda. La regla, lo único que hay que retener del diseño, es siempre la misma: solamente el primary devuelve el mensaje.

¿Para qué sirven entonces el secondary y el tertiary, si nunca devuelven mensajes? Porque en algunos casos sí van a devolverlos. Los nodos se comunican mediante gossip, el mecanismo que vimos en la clase 9 con Dynamo: se van diciendo quién está vivo y quién no, sin coordinador central. También se podría usar un servicio externo de detección de fallas, un ZooKeeper como el de la clase 7. Con cualquiera de los dos, cuando el primary muere y el secondary se entera, queda habilitado a responder.

Falta el visibility timeout, y ahí el diseño muestra su costo. El timeout se guarda localmente y no se replica: cuando un nodo entrega un mensaje, anota en su propia copia que queda invisible por sesenta segundos, y esa anotación no viaja a las réplicas. Si el primary entrega el mensaje, pone su timeout y se muere, el próximo `receive` llega al secondary, que ahora puede responder y tiene el mensaje sin ninguna marca de invisibilidad: lo entrega de nuevo. El mensaje aparece duplicado, no por error sino por diseño.

Eso cierra el caso incómodo que habíamos anticipado: una falla interna del servicio puede entregarle el mismo mensaje a otro consumidor a los pocos segundos, con los dos procesándolo en paralelo, a pesar del timeout. Está contemplado, y es coherente con lo único que estos sistemas prometen: at-least-once. El mensaje llega por lo menos una vez, y el consumidor tiene que ser idempotente.

Con esto el sistema está armado, y la afirmación que corresponde, con toda la cautela que le cabe, es que por lo que se sabe SQS funcionaba así. No hay documentación pública que lo confirme, y esto describe cómo funcionaba hace unos veinte años. Falta una corrección de escala: no eran seis nodos sino miles de grupos de seis, con otra capa de distribución por encima que repartía el tráfico entre ellos. Pero la replicación y el sharding se resolvían dentro de cada grupo de seis nodos, con esta copia fácil a un par de vecinos y con gossip para saber quién estaba vivo. Es posible que hoy utilicen Raft; no hay forma de saberlo con certeza.

---
