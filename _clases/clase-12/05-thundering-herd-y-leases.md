---
title: "5. Thundering herd y leases"
parent: "Clase 12 — Consistencia en cachés"
nav_order: 5
---

# 5. Thundering herd y leases
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Hot keys y estampida

El problema que viene tiene un nombre muy gráfico: *thundering herd*, en castellano una estampida. Aparece principalmente en sistemas muy grandes, y el caso típico es Twitter, en particular las cuentas de gente muy famosa. Un tweet muy famoso lo tiene todo el mundo en el timeline, y todo el mundo lo está leyendo constantemente. A una clave así, muy leída, se la llama *hot key*.

Una hot key parece, de entrada, el caso fácil. Se consulta en el caché como cualquier otra clave, y el hit ratio es muy alto, porque todo el mundo accede al mismo tweet. Un tweet muy popular está siempre haciendo hit y casi nunca se termina accediendo a la base. Desde el punto de vista de la capacidad, es exactamente el escenario que queríamos.

Ahora imaginemos que ese tweet se actualiza, por ejemplo porque se edita. Al editarlo hay que modificar la base y después hacer un `delete` para borrar la versión vieja del caché, sea memcache, Redis o lo que haya.

A primera vista no parece grave: tras el delete, el primer frontend que acceda no lo encuentra, va a la base y lo deja actualizado en el caché. Eso es lo obvio, y es lo que pasa la mayor parte del tiempo.

Pero cuando se trata de un tweet —o un post de Facebook— al que acceden literalmente miles de veces por segundo, pasa otra cosa. Ese miss no le ocurre a un frontend: les ocurre a miles de servidores a la vez. Todos se encuentran el miss, todos van al mismo tiempo a la base y todos tratan de actualizar al mismo tiempo el memcache.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/thundering-herd.png' | relative_url }}" alt="Muchos frontends contra un memcache al borrarse la clave">
  <figcaption>
    <span class="figura-label">Figura</span>
    la estampida — cuatro frontends con flechas hacia un único memcache, la etiqueta delete() sobre la clave borrada, y las flechas que atraviesan el memcache y van todas juntas contra el cilindro de la base de datos
    <span class="figura-ref">notas pág. 8 / pizarra pág. 7</span>
  </figcaption>
</figure>

De esos dos efectos, el segundo es el menor: actualizar el memcache todos a la vez no es tan terrible. El problema es la base. Estaba bien protegida detrás del memcache, y de repente, solo por borrar un elemento del caché, le caen encima miles de requests por segundo todos juntos. Se satura, e inclusive se puede caer. Y hay un daño de segundo orden: como la base se satura, el resto de los requests —los que no tienen nada que ver con esta clave— también empiezan a tener delays, esperando detrás de una base que ya no da abasto.

Esto no es intuitivo. Lo sorprendente es la desproporción: borramos una única clave, una de las operaciones más inofensivas que hay, y el resultado es una base caída. En sistemas que no están a gran escala no suele pasar tan fácilmente; en sistemas grandes sí.

El fenómeno es más general que memcache y que Facebook. El thundering herd no es algo de lo que se hable seguido al pensar en cachés: uno imagina que todo funciona bien, pero no piensa qué pasa cuando se invalida un valor. Y aunque todo funcione como corresponde, puede llegar una estampida a la base. Siempre que se desbloquean muchos sistemas a la vez y todos tratan de acceder al mismo recurso, aparece un problema que puede ser complicado y nada evidente al diseñar.

Un ejemplo hipotético muestra hasta qué punto no es evidente. Supongamos que hay que cambiar una configuración del caché, y para eso invalidar todas sus claves. Se hace con todo el cuidado, precisamente para no sobrecargar la base: de forma muy gradual, invalidando, por ejemplo, un uno por ciento de las claves por hora. Lo que no se tiene en cuenta es que algunas de esas claves son hot keys. Cuando les toca el turno, aunque sean tres o cuatro —muchas menos que ese uno por ciento tan prudente—, cada una produce una estampida contra la base: se satura, y con ella se degrada el resto del sistema. El sistema falla durante la operación diseñada justamente para que no se rompiera.

Esa es la moraleja: lo que determina si hay estampida no es el volumen de lo que se invalida, sino cuál es la clave que se toca.

## Leases

Lo que queremos frente a la estampida tiene una forma conocida. Si mil frontends acceden a la vez al memcache y borramos la clave, nos gustaría hacer una pequeña elección de líder entre esos mil, y que solo uno llegue a la base y actualice el memcache. Los otros novecientos noventa y nueve tienen que quedarse donde están.

El que elige al líder es el propio memcache. Los ingenieros de Facebook descargaron el código de memcached, lo modificaron y le agregaron este mecanismo, al que llamaron *leases*. Elegir líder aquí es simple por una razón: el memcache es una única máquina, centralizada, y puede usar sus propias primitivas de concurrencia para decidir quién llegó primero. No hacen falta Raft, ni términos, ni mayorías. El problema difícil aparece cuando el que elige está distribuido; aquí no lo está.

El algoritmo es ingenioso. El cliente 1 trata de obtener la clave. Normalmente obtendría un miss e iría a la base; ahora obtiene dos cosas: el miss, la señal de que la clave no está, y además un lease, un random de 64 bits, nada más que eso.

Para entender qué hace memcache con ese número hay que mirar su tabla interna: claves, valores y ahora un campo más, el lease. Ante un miss —y esta es una de las innovaciones centrales del paper— la versión modificada carga de todos modos la clave en la tabla junto con el lease entregado, pero sin valor, porque todavía no lo tenemos. Queda una fila a medio llenar que no sirve para responder lecturas y cuyo único propósito es dejar constancia de que alguien ya salió a buscar ese valor.

Eso permite lo siguiente. Si otro cliente hace un `get` de la misma clave, memcache ve en la tabla que alguien ya la pidió. El valor sigue sin estar, así que la respuesta sigue siendo un miss; pero en vez de pasarle un lease, como ya entregó uno, le responde `retry`. El paper lo plantea del lado del servidor y con un número concreto: memcache entrega un lease para una misma clave **una sola vez cada diez segundos**, y todo cliente que pida esa clave dentro de esa ventana tiene que esperar en lugar de salir a buscar el valor.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/mecanismo-de-leases.png' | relative_url }}" alt="Leases: miss con lease, miss con retry y la tabla de memcache">
  <figcaption>
    <span class="figura-label">Figura</span>
    el mecanismo de leases — el cliente 1 hace get(k) y recibe (miss, lease) de 64 bits; el cliente 2 hace get(k) y recibe (miss, retry); al costado, la tabla interna de memcache con las columnas clave, valor y lease, con la clave y el lease ya cargados y el valor todavía vacío
    <span class="figura-ref">notas pág. 8 / pizarra pág. 7</span>
  </figcaption>
</figure>

Esa señal quiere decir que el cliente tiene que esperar unos milisegundos, porque todo ocurre muy rápido: existe solo para evitar el pico, y en unos milisegundos se resuelve. Espera cien milisegundos, por ejemplo, y reintenta. Lo crítico —y por eso tiene que estar bien implementado— es que mientras tanto no intenta acceder a la base ni actualizar nada: espera a que el cliente 1 deje el memcache actualizado.

El cliente 1, entretanto, va a la base, lee el valor y manda un `set` como antes: la clave, el valor, y ahora también el lease que le habían devuelto. Ese tercer argumento es la novedad. Memcache vuelve a la tabla, se fija si la clave está y si el lease coincide con el que entregó. Si no coincide, no tiene por qué creerle: ese cliente no es el que salió a buscar el valor. Con el lease correcto, solo entonces memcache pone el valor. Después puede dejar el lease o borrarlo; probablemente no importe demasiado.

El desenlace es el esperado. La próxima vez que el cliente 2 haga un `get`, encuentra un valor de verdad, ni miss ni retry. Se resolvió el thundering herd: solo el cliente 1 vino, no encontró la clave, fue a la base y la dejó actualizada. Del cliente 2 al N se quedaron en memcache, nunca accedieron a la base, y se evitó la estampida.

## Leases y optimistic locking

Queda una tercera race condition —la última de las tres que fueron apareciendo a lo largo de la clase—, con la particularidad de que se resuelve con el mecanismo que acabamos de construir, sin piezas nuevas.

Empecemos por la traza. El cliente 1 trata de obtener una clave y obtiene un miss. Va a la base, hace su read y lee, por ejemplo, `V1`. Con eso vuelve al memcache y hace su `set(k, V1)`. Nada inusual: una lectura común.

El punto está en el espacio entre el read a la base y el set al caché. En el dibujo casi no se ve, pero es real, y ahí nos vamos a meter en problemas. Una lectura sola nunca se rompe; pero se puede combinar con una escritura, y ahí se complica.

Supongamos que el cliente 2 aparece justo en ese medio. Hace un write: pone `k = V2` en la base y después el `delete(k)` que acompaña a toda escritura. Todo correcto. Pero el cliente 1 se quedó lento por alguna razón, y su `set` con `V1` aterriza después del delete y termina imponiéndose.

Lo que tendría que haber pasado es fácil de perder de vista. Después de ese delete uno esperaría que el cliente 1 hiciera su `get`, fallara, leyera el valor actualizado y solo entonces hiciera el `set`. Ese es el orden sano. Pero basta un delay cualquiera para que un set viejo llegue tarde.

Y el resultado es el peor de todos: `V2` en la base y `V1` en el caché. Si la clave no tiene TTL, `V1` queda para siempre, y ningún hit sobre ella va a leer el valor actualizado.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/lease-como-optimistic-locking.png' | relative_url }}" alt="El set con un lease borrado por un delete">
  <figcaption>
    <span class="figura-label">Figura</span>
    la tercera race condition — dos columnas; C1 hace get(k) → (miss, lease) y read de la base → V1; en el medio C2 hace write k=V2 y delete(k), que tacha la fila entera de la tabla clave/valor/lease; el set(k, V1, lease) de C1 falla porque ese lease ya no existe
    <span class="figura-ref">notas pág. 8 / pizarra pág. 8</span>
  </figcaption>
</figure>

Esto no es privativo de este diseño: puede pasar con cualquier caché, o en cualquier situación con el mismo dato guardado en dos lugares. Otros cachés ofrecen herramientas para este caso. Redis, por ejemplo, implementa optimistic locking con `WATCH`: si la clave observada cambia antes del `EXEC`, la transacción se aborta.

Lo que sí sabemos es lo que hizo Facebook, y aquí está el giro: termina siendo una especie de optimistic locking, y no hubo que construir nada, porque el mecanismo ya estaba. El miss devuelve un lease, como acabamos de ver; estaba pensado para el thundering herd, pero el hecho es que lo devuelve.

La pieza que faltaba está en el delete. En la tabla interna —clave, valor, lease—, con el miss del cliente 1 se cargaron la clave y el lease, con el valor vacío. Cuando llega el delete del cliente 2, memcache —y esto es lo fundamental— borra la entrada entera: clave, valor y lease, todo junto, igual que antes.

La consecuencia es directa. El `set` del cliente 1 da error, porque manda `V1` con un lease que ya no existe en la tabla. Y con evitar ese set alcanza: después vendrá otro cliente, leerá de la base, obtendrá un lease nuevo y dejará el valor correcto.

Verificar ese lease es prácticamente lo mismo que vimos con Zookeeper en la clase 7. Tratamos de setear un valor y verificamos, de paso, que nada haya cambiado mientras tanto; el lease hace las veces de la versión del optimistic locking. Al no encontrarla, la operación tira un error de concurrencia, que es exactamente lo que queríamos: los threads se combinaron mal, y el sistema se da cuenta.

memcached ofrece operaciones de este tipo, llamadas CAS, por *check-and-set*: `gets` devuelve el valor junto con un identificador de versión, y `cas` solo escribe si ese identificador no cambió; si cambió, da error. El lease de Facebook cumple el mismo papel que ese identificador.

Esta race condition se ve poco, y el TTL explica por qué. Es una variación de un problema que puede ocurrir con cualquier caché, y normalmente pasa inadvertido: el caché suele tener un TTL, y no suele ser crítico que el valor se actualice al instante. El TTL borra la entrada y el problema se arregla solo. Pero si no se tiene cuidado, puede ocurrir de todos modos.

Queda un punto, y ahí se termina de entender el mecanismo. Si el set contra una clave ausente da error, ¿no debería dar error también el caso feliz? Al fin y al cabo, el cliente que hizo el get tampoco encontró la clave. La respuesta es que, al no estar, el get la inicializa: deja puestos la clave y el lease. Imaginemos que la escritura concurrente no existe. El caso feliz es: el cliente va a la base, lee el valor y manda clave, valor y lease; y ese lease coincide con el que memcache le devolvió. La verificación es doble: ¿está la clave? Sí, quedó inicializada con el miss. ¿Está el lease y es el mismo? Sí. Coinciden las dos cosas, y solo entonces pone el valor. El problema aparecía cuando la entrada no estaba porque antes se había hecho un delete.

También el lease expira. Al agregar la clave se le pone un TTL de unos milisegundos, para que la clave no quede bloqueada indefinidamente. Si el cliente obtiene el lease y falla, al cabo de un segundo o algo así se reinicia y memcache acepta a otro cliente.

Y hay otro caso que se resuelve del mismo modo. Si un cliente obtiene un lease, queda bloqueado, otro obtiene mientras tanto un lease nuevo, y después el primero intenta actualizar con el lease viejo, memcache ve que no coincide y lo rechaza. Optimistic locking de nuevo, la misma verificación haciendo el mismo trabajo.

Mirado desde lejos, todo esto deja ver el problema de fondo. Lo que Facebook tenía entre manos era escalar memcache, y el paper lo cuenta con bastante más detalle del que le dimos aquí. Pero la forma del problema ya está entera en lo que recorrimos: al escalar el caché, las piezas se les fueron desincronizando, y cada sistema adicional que construyeron —mcsqueal conectado al log, el marcador que bloquea la lectura local, el lease que arbitra entre mil frontends— no es más que otra manera de volver a sincronizarlas.
