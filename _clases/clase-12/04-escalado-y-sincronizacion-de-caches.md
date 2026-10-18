---
title: "4. Escalado y sincronización de cachés"
parent: "Clase 12 — Memcache en Facebook"
nav_order: 4
---

# 4. Escalado y sincronización de cachés
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Sharding del cluster de memcache

Al describir la arquitectura dijimos que el cluster de memcache está shardeado y dejamos el cómo pendiente. Un frontend accede a muchos memcaches, pero no son réplicas: no tienen la misma información. Hay un reparto: distintas claves asignadas determinísticamente a distintos memcaches, parecido a como distribuimos los datos en MapReduce.

En su versión más simple cabe en una línea. A la clave se le hace un `MD5`, y a ese hash, módulo 3 si tenemos tres memcaches. Eso da el índice del servidor —cero, uno o dos— donde guardamos el valor. La próxima vez, la misma cuenta nos lleva al mismo lugar.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/sharding-de-memcache.png' | relative_url }}" alt="Un frontend con tres shards de memcache">
  <figcaption>
    <span class="figura-label">Figura</span>
    el sharding de memcache — un frontend con tres flechas hacia MC1, MC2 y MC3, y al costado la regla MD5(k) % 3 = índice del shard
    <span class="figura-ref">notas pág. 6 / pizarra pág. 5</span>
  </figcaption>
</figure>

Con eso el diagrama se lee distinto: esos memcaches alineados no son réplicas, son shards.

¿Por qué shardear un caché? Porque cada memcache es una máquina con memoria y una hash table dentro. Si nos quedamos sin memoria, la única salida es partir eso en varias máquinas: usar la memoria de muchas y repartir los requests entre ellas.

Hay un detalle contraintuitivo del paper. Para armar un response, el frontend típicamente necesita muchísimas claves: la información del usuario, el timeline, el texto de cada elemento del timeline, y así siguiendo. El resultado es que, por cada request, termina accediendo a todos los memcaches. Así que si bien el sharding sirve para escalar en memoria, el frontend accede a todos y los carga a todos.

La cuenta del `MD5` con módulo es, por otra parte, la versión didáctica. La técnica que se usa de verdad es consistent hashing, con algunos refinamientos: el anillo con máquinas distribuidas sobre él, que ya apareció en Concurrencia y que también usa DynamoDB.

Queda una última pieza, también del paper. Dentro de cada región arman muchos clusters. Cada cluster es uno de esos bloques que en el diagrama aparecen uno delante del otro: un conjunto de frontends y un conjunto de shards de memcache, y de esa pieza hay varias copias. Los requests llegan aleatoriamente a los distintos clusters, y así le agregan capacidad al sistema.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/clusters-en-una-region.jpg' | relative_url }}" alt="Dos clusters de frontends y memcaches en una región">
  <figcaption>
    <span class="figura-label">Figura</span>
    los clusters dentro de una región — dos bloques idénticos, cada uno con su conjunto de frontends arriba y su conjunto de shards de memcache abajo, y debajo la base con mcsqueal, que recibe el update y manda el delete a los dos
    <span class="figura-ref">notas pág. 7</span>
  </figcaption>
</figure>

## Invalidación cross región con mcsqueal

Resuelto el sharding, volvemos a la pregunta abierta: ¿cómo funciona la invalidación de cachés cross región? Es el mecanismo más interesante del paper, y no solo por el problema que resuelve: muestra una técnica que se termina usando en cualquier sistema que deba mantener dos piezas sincronizadas.

Dibujemos dos regiones bien simplificadas, con un frontend, un memcache y una base en cada una. El sharding y los clusters siguen estando, pero para lo que viene no aportan nada. La segunda base es la réplica de la primera, y los frontends son los Apache de la capa de arriba.

Repasemos la escritura. Primero la escritura contra la base —`k` pasa a valer `V2`— y después el `delete(k)` contra el caché. Y aquí hay un detalle que dejamos pasar: ese delete es solo local a la región. No se hace un delete contra el servidor del otro lado del mundo; se le hace a la máquina que tenemos al lado.

La consecuencia es todo el problema. En el memcache de la otra región, `k` sigue guardada con `V1`. El valor nuevo eventualmente se replica a la base de esa región, para eso está la replicación. Pero mientras la clave no expire del caché remoto, el frontend de esa región sigue consultando su memcache y sigue recibiendo `V1`. A nadie le avisaron nada. Necesitamos alguna forma de invalidar ese memcache del otro lado del mundo, y los de todos los data centers.

La solución que adoptaron es muy interesante. La base de datos —MySQL en este caso, pero podría ser Postgres o cualquier otra— tiene dentro, como todas, un log: el write-ahead log, el WAL. Los ingenieros de Facebook inventaron un sistema aparte, mcsqueal, que se conecta a ese log y observa las operaciones que van llegando.

El mecanismo sale de ahí. Cuando mandamos un update en la región primaria —el write se traduce, dentro de la base, en un update—, ese update llega por la replicación al log de la otra región. mcsqueal lo detecta, infiere qué clave tiene que invalidar y hace el `delete` contra el memcache de esa región. La invalidación viaja montada sobre la replicación que ya existía.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/invalidacion-cross-region.png' | relative_url }}" alt="Invalidación cross región con mcsqueal leyendo el WAL">
  <figcaption>
    <span class="figura-label">Figura</span>
    la invalidación cross región — dos regiones; en la primaria el frontend escribe en la base y hace el delete contra su memcache local; la base se replica a la región secundaria, donde mcsqueal está conectado al WAL, detecta el update y dispara el delete contra el memcache remoto
    <span class="figura-ref">notas pág. 6 / pizarra pág. 5</span>
  </figcaption>
</figure>

Falta lo más delicado: cómo se infiere la clave a partir del update. El paper resuelve esto sin inferir nada: las sentencias SQL que modifican datos llevan agregadas las claves de memcache que hay que invalidar una vez que la transacción se confirma. Una forma de hacerlo es la siguiente. El frontend manda una query cualquiera, por ejemplo `UPDATE users SET name = 'foo' WHERE id = 123`. MySQL, como SQL en general, admite comentarios: con dos guiones lo que sigue queda ignorado por el motor. Se le agrega al final la clave a invalidar:

```sql
UPDATE users SET name = 'foo' WHERE id = 123 -- KEYS ['users:123']
```

Así se embebe en la query misma la información que después le llega indirectamente a mcsqueal. mcsqueal parsea la query, extrae el comentario y sabe que —además de lo que la query haga dentro de la base, que no se va a poner a analizar— tiene que invalidar la clave `users:123` en todos los cachés que tenga.

Esto no se queda en lo teórico. mcsqueal es de Facebook y muy específico, pero hay versiones de la misma idea que se pueden usar. A la técnica de inspeccionar el log se la llama change data capture, CDC. La herramienta concreta que se puede descargar es Debezium, que se usa mucho: está escrita en Java, uno la instala, le pasa los datos de la base y se conecta a su write-ahead log. Debezium puede mandar los eventos a Kafka, y después uno consume esa cola y hace lo que quiera. Con herramientas open source actuales esto se podría armar; es una arquitectura complicada, pero se podría. Siempre considerando que hay que hacer deletes: con updates pueden aparecer race conditions, y con deletes todo cierra más fácil.

mcsqueal vale más allá de este caso: es una forma alternativa de actualizar cachés en general. Y quizás ni siquiera sea un caché lo que se actualiza, sino otro subsistema que necesita responder a los cambios del original. Componer un Debezium y con eso actualizar, por ejemplo, una réplica de la base es perfectamente pensable. Pero —y se deriva directamente del ejemplo de por qué usar `delete` y no `update`— si no se lo piensa bien, puede producir race conditions muy concretas. En los sistemas distribuidos hay muchas race conditions ocultas que no son evidentes al principio, y la razón para usar `delete` es justamente de las que no se ven a primera vista.

## Invalidación local y remota

Planteado así, queda una objeción pendiente, la que cualquiera se haría: no se termina de ver cómo esto resuelve que la máquina esté del otro lado del mundo. ¿El objetivo era evitar que corra la query entera y usar el registro que corresponde, mucho más rápido que ejecutar la query completa? Porque mirado así, el problema distribuido no parece resuelto por ningún lado.

Para contestarla hay que volver al escenario. Tenemos el primary de un lado y el secondary del otro. En el primary todo cierra. El secondary funciona de manera independiente en todo lo que hace a las lecturas: cuando su frontend quiere leer, va al caché de su región, no encuentra el dato, accede a la réplica local y con eso actualiza el memcache. El problema es que, si actualizamos el primary, el frontend de la región primaria solo invalida el memcache de su propia región.

Conviene enunciar la consecuencia con claridad. En el secondary podemos seguir indefinidamente —sin expiración, indefinidamente de verdad— con el caché guardando un valor incorrecto. El frontend primario escribió `V2` en su base, y eso llegó a la otra base por la replicación. Pero el frontend remoto sigue teniendo hits en su memcache, y en cada uno recibe el valor viejo, de forma indefinida. Hay que invalidar ese otro caché de alguna forma, y eso es lo que estamos resolviendo: no tiene nada que ver con la velocidad.

La forma más obvia —obvia de imaginar, difícil de armar— sería que el frontend, además de invalidar su caché local, le mandara un `delete` al caché de la otra región. Eso funcionaría. Pero no optaron por ese camino, porque requería que ese frontend conociera toda la estructura de otro data center. Lo hicieron indirectamente: el frontend invalida solo la copia local, y para la otra región el cambio viaja por la replicación, lo levanta mcsqueal, y eventualmente llega el delete. Dos caminos para el mismo objetivo, y eligieron el más desacoplado.

Detrás de la objeción hay un sesgo que tenemos todos: pensamos que los cachés siempre tienen un tiempo de expiración y que las cosas se van solas. Es más fácil pensar el problema al revés: ¿cómo sería este sistema si nada expirara? De hecho, en sistemas como Twitter o Facebook tratan de que las cosas no expiren nunca, porque cuando expiran la carga es tan grande que todos acceden a la base, y eso puede ser problemático. Hay una solución para eso también, pero en general se trata de que, en lo posible, no expire nunca.

El paper deja una duda que no pudimos saldar: no queda claro si dice que las cosas expiran automáticamente de los cachés, si al cabo de media hora se van solas cuando no se las borró a mano. La impresión es que quedan indefinidamente y uno está obligado a borrarlas.

El dibujo esconde una redundancia. mcsqueal no está solo en la región remota: la región local también lo tiene, leyendo su propio log y haciendo el mismo análisis. Así que el `delete` que el frontend mandó directo a su memcache eventualmente le llega también por mcsqueal. Eso nos salva de un caso problemático: si el frontend pudo escribir en la base pero justo el request del `delete` falló y nunca se mandó, como hay otro sistema leyendo la base, el delete termina llegando por el otro lado. Un segundo mecanismo que hace lo mismo y le da más seguridad al asunto.

Queda la pregunta simétrica: si mcsqueal manda el delete de todos modos, ¿para qué el primero, el que el frontend hace contra su caché local? Es una decisión de diseño. Los ingenieros de Facebook querían que, cuando el frontend hace una escritura, dentro del mismo request pueda leer inmediatamente del caché lo que acaba de escribir en la base. Presumiblemente por la correctitud de ese request. Por eso fuerza la invalidación llamando directo al `delete` local. Pero no sería estrictamente necesario, porque el otro sistema le manda los deletes por detrás. Es una sutileza interesante: ese primer delete está ahí por la correctitud de un request, no porque el sistema no funcionaría sin él.

## Réplica atrasada y remote marker

Hay otra race condition escondida, y aparece precisamente por haber agregado mcsqueal. Es una sutileza y hay que recorrerla despacio: lo importante es ver de cuántas maneras se pueden hacer mal las cosas.

Volvamos a la versión fácil del dibujo: la región primary con un frontend, un memcache y una base; la secondary con lo mismo, salvo que pondremos dos frontends en lugar de uno. Esa es toda la diferencia, y alcanza para meternos en problemas. Que sean dos importa: el que escribe y el que lee no son la misma máquina, y ninguno puede enterarse de lo que hace el otro.

Llega un pedido de escritura al primer frontend del secondary. No lo puede resolver localmente, porque la base que tiene al lado es una réplica de solo lectura: tiene que ir a la región primary y escribir en ella. Ese es el write cross región, el paso uno. El paso dos es que además borra la clave de su caché local. Es un detalle que no habíamos mencionado: aunque escribamos en otro lugar del mundo, sabemos que lo que tenemos en el caché local va a ser inválido y que eventualmente se va a borrar, así que conviene invalidarlo ya para acelerar las cosas. Hasta aquí, el mismo par de pasos de siempre, con la escritura apuntando lejos.

En el paso tres empieza el problema. Llega un read al segundo frontend, justo sobre la clave que acabamos de actualizar. Hace su `get(k)`, no la encuentra porque la acabamos de borrar, y hace lo que dicta el algoritmo: va a la base local y la lee de ahí.

Ahí ocurre la race condition. La clave es el delay: lo que escribimos en otra región tarda un tiempo en llegar a la actual. El segundo frontend se encuentra con una réplica que todavía no recibió el cambio, lee un valor desactualizado y con él actualiza el memcache local. Quedamos otra vez en un estado inconsistente. Y ese frontend no hizo nada mal: siguió el algoritmo al pie de la letra y fue a la fuente que tenía disponible, solo que esa fuente todavía no se había enterado. Si nada se elimina automáticamente, esa clave queda desactualizada en memcache para siempre.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/replica-atrasada.png' | relative_url }}" alt="Race condition con la réplica atrasada">
  <figcaption>
    <span class="figura-label">Figura</span>
    la race condition de la réplica atrasada — dos regiones; el frontend del secondary escribe cross región contra la base del primary y borra su caché local; un segundo frontend lee, no encuentra nada, lee la réplica todavía atrasada y reinstala el valor viejo; la flecha de replicación rotulada &quot;se retrasa&quot;
    <span class="figura-ref">notas pág. 7 / pizarra pág. 6</span>
  </figcaption>
</figure>

Lo resolvieron con un marcador, una modificación de los dos algoritmos. El frontend que escribe normalmente haría el `update_master` —la escritura contra la base de la otra región— y después el `delete(k)` local: el camino donde puede pasar la race condition. Ahora hace un paso más, antes de todo: en el mismo memcache local crea una clave especial, un marcador, que indica que esa clave se está modificando en la otra región y por lo tanto no es válida. Hace un `set(RK)`. Es una clave aparte, que convive en el mismo caché con `k` y existe únicamente para dejarle un aviso al que venga después. La R es de *remote*: el paper lo llama el **remote marker**, y describe a `rk` como un registro de memcache que guarda información adicional sobre la clave `k`.

También cambia la lectura, con un paso más. El `get(k)` da miss, y normalmente iríamos a la base, que es justo donde podemos romper todo. Ahora, tras el miss, se verifica si la clave está marcada como inválida, con un `get(RK)`. Si da hit, hay algún otro frontend, en algún lugar, modificando esa clave en el master de la otra región.

Con eso el frontend sabe que no puede tomar el camino local. Tiene que hacer una lectura con consistencia fuerte, y eso significa leer del master. Mientras el marcador esté activo no se puede leer de la réplica local, que está desactualizada. Va al master, lee de ahí, y solo con ese valor puede actualizar el memcache sin que pase nada.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/algoritmo-con-marcador.png' | relative_url }}" alt="Escritura y lectura con el remote marker">
  <figcaption>
    <span class="figura-label">Figura</span>
    el algoritmo con marcador — a la izquierda el frontend que escribe, con set(RK), update_master y delete(k); a la derecha el frontend que lee, con get(k) → miss, get(RK) → hit y la lectura redirigida al primary
    <span class="figura-ref">notas pág. 7 / pizarra pág. 6</span>
  </figcaption>
</figure>

¿Quién borra el marcador? El encargado es mcsqueal: además de invalidar la clave, se fija si hay marcas puestas por el frontend y las borra. El mismo sistema de las invalidaciones baja la bandera cuando ya no hace falta.

Es una forma ingeniosa de resolverlo, y dice algo sobre el paper entero. No tiene algoritmos tan sofisticados como los de Raft: son soluciones prácticas a problemas que los ingenieros de Facebook seguramente se fueron encontrando sobre la marcha. No sabemos si pensaron en esta race condition desde el principio; lo más probable es que, al encontrársela, hayan decidido que durante la transición —mientras las cosas llegan de una región a la otra y mcsqueal las actualiza— corresponde marcar la clave como inválida. Que es, básicamente, deshabilitar localmente el memcache para esa clave.

Queda una incertidumbre que el paper no despeja: cuando el frontend busca el valor en la otra región, no está claro si va directo a la base del primary o si podría pedirle al frontend de esa región que le optimice algo.

---
