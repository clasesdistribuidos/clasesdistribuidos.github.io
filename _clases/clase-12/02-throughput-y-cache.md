---
title: "2. Throughput y caché"
parent: "Clase 12 — Consistencia en cachés"
nav_order: 2
---

# 2. Throughput y caché
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Paralelismo y tiempo de query

Volvamos al sistema web del principio, el del load balancer con los servidores stateless adelante de la base. Con la ley de Little lo podemos mirar de otra manera: igual que descompusimos el hospital, aquí podemos verlo como tres sistemas en serie: la capa de entrada, la capa de servidores web stateless y la base de datos. Y pasa lo mismo que en el hospital: si el conjunto está estable, por los tres pasa la misma λ. No es una condición que haya que imponer, sale sola de que nada se acumula. Con una aclaración: un request web suele hacer varias queries, y si hace `k`, la base ve `k·λ`; para simplificar vamos a suponer una query por request.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/web-como-tres-sistemas.png' | relative_url }}" alt="El sistema web como tres sistemas en serie">
  <figcaption>
    <span class="figura-label">Figura</span>
    el sistema web original visto como tres sistemas en serie — load balancer, capa de servidores stateless y base de datos, con el mismo λ atravesando los tres
    <span class="figura-ref">notas pág. 3 / pizarra pág. 4</span>
  </figcaption>
</figure>

Visto así se entiende mejor qué hacíamos al agregar servidores en paralelo: aumentábamos la capacidad de la capa del medio subiendo el paralelismo. Ese paralelismo es la cantidad de clientes que se pueden atender simultáneamente, que es el techo de la `L` de la ley.

Con la base de datos pasa algo parecido, y se ve haciéndole zoom. Dentro suele haber un pool de conexiones, una cantidad máxima de conexiones; el parámetro se llama típicamente `max_connections`. Ese número es el paralelismo de la base.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/pool-de-conexiones.png' | relative_url }}" alt="La base de datos con su pool de conexiones">
  <figcaption>
    <span class="figura-label">Figura</span>
    zoom a la base de datos — un cilindro con su pool de conexiones dentro y la etiqueta max_connections = paralelismo
    <span class="figura-ref">notas pág. 4 / pizarra pág. 4</span>
  </figcaption>
</figure>

Mirando la ley con esto presente, cada cantidad tiene un nombre propio en la industria. La tasa de arribos, de la base y del sistema en general, se llama throughput, un término estándar al monitorear: mientras el sistema no esté saturado, los requests por segundo que le llegan son su throughput. La `L` son los requests en vuelo, y su máximo es el paralelismo: según lo que miremos, la cantidad de threads o de conexiones simultáneas. Y la `W` es el tiempo promedio por query.

Puestas así aparece lo que veníamos buscando. El paralelismo típicamente es fijo, porque es un parámetro: la cantidad máxima de conexiones, o el tamaño del thread pool. El tiempo de las queries no es fijo ni lo controlamos del todo, pero tiene un promedio, una duración típica. Si conocemos el paralelismo máximo y lo que tarda una query cuando no espera a nadie —el tiempo de servicio, `S`—, tenemos un throughput máximo, `paralelismo / S`: el número que nos dice cuánto puede soportar el sistema. Conviene usar `S` y no la `W` que se mide en producción, porque la `W` incluye la espera en cola y crece justo cuando el sistema se acerca a la saturación.

Y ahí se vuelve importante la asimetría que anticipamos. λ es lo que no controlamos: es la demanda, aquello para lo que diseñamos el sistema. Si queremos que el sistema soporte una λ más grande, la ley nos deja exactamente dos caminos: aumentar la `L` máxima, poner más paralelismo, o bajar el tiempo que cada request le pide al recurso. Ese tiempo es la demanda, `D = V · S`: el tiempo de servicio de una visita por la cantidad de visitas `V` que hace cada request —la `k` de antes—. Con una query por request, `D` es simplemente `S`. Despejando, el throughput máximo es `L_max / D`, y se confirma con la lógica: más paralelismo, más throughput máximo; menos demanda por request, también. Son las dos únicas perillas que hay, y la segunda se puede girar de dos maneras: acelerando la query, que es bajar `S`, o haciendo que menos requests lleguen al recurso, que es bajar `V`.

Cuando surgen problemas en producción y aparece un pico de clientes, lo que pasó es que aumentó muchísimo la λ. La reacción habitual, a menudo apresurada, es agregar más servidores. Es decir que la fórmula ya la conocíamos intuitivamente; lo que agregamos es la base matemática que explica por qué funciona. Más paralelismo, mejor.

Con la base de datos es más difícil, porque no es fácil agregar más bases. A lo sumo, más réplicas; pero si aumentan las escrituras la situación se complica, porque de la réplica solo se puede leer. La otra opción es parar la base y subirle la cantidad máxima de conexiones, pero en la práctica tampoco funciona demasiado bien: las bases no funcionan bien con una cantidad muy grande de conexiones. Cada conexión consume memoria —en Postgres, un proceso entero—, y a partir de cierto punto las conexiones compiten por los mismos locks y la misma CPU, y el throughput baja en lugar de subir.

Ante un pico, la respuesta habitual seguirá siendo aumentar el paralelismo. Pero cuando uno diseña el sistema desde el principio —y ese es exactamente el problema que tuvo Facebook— la salida es otra. Lo que trataron de hacer no fue tener muchísimo paralelismo, aunque el sistema termina teniéndolo, sino sacarle trabajo a la base, girando la segunda perilla por el lado de la `V`: que la mayoría de los requests ni siquiera lleguen a ella. Puede parecer sorprendente, pero es lo que nos lleva al tema de esta clase: los cachés. Un caché sirve, en definitiva, para que una query repetida no vuelva a la base, más que para aumentar la velocidad.

## Efecto del caché sobre el throughput

La herramienta es el caché. La idea no debería ser nueva: en las materias de procesadores apareció un caché con la misma idea de guardar cerca lo que se usa seguido, aunque el nuestro funciona de otra manera, como vamos a ver enseguida.

Instalamos un sistema aparte. El clásico es memcached, un sistema viejo; hoy la alternativa más nombrada es Redis. El funcionamiento de memcached es sencillo: en esencia, un hashmap en memoria. A favor, es muy rápido; en contra, es poco versátil. Las operaciones que nos importan son tres: un `get` de una clave, un `set` —o `store`— de una clave y un valor, y un `delete` de una clave, que en la sección siguiente va a ser la pieza central de la invalidación. memcached tiene algunas más, como `add`, `cas` o `incr`, pero no mucho más que eso; Redis, en cambio, va bastante más allá de un hashmap: tiene listas, sets, sorted sets, pub/sub y persistencia opcional.

Con un modelo así de simple, los tiempos quedan en el orden de un milisegundo como mucho, contando la red, porque típicamente memcache va en otra máquina: hay un cluster aparte dedicado a los memcaches. También se lo puede poner en las mismas máquinas que atienden los requests, pero eso no tiene tanto sentido frente a lo que vamos a ver que hizo Facebook.

El caché no desplaza a nadie: la fuente de verdad sigue siendo la base de datos. La técnica típica para combinar las dos piezas se llama look-aside cache, y tiene cuatro pasos. El request llega a la app, que se fija primero si lo que necesita está en memcache. Si está, lo devuelve desde ahí: un hit. Si no, va a la base, hace la query común y corriente, guarda el resultado en el caché y solo entonces devuelve. La próxima vez que venga el mismo request lo va a encontrar en el caché. Se parece a los cachés de procesador, pero solo en la idea: el de procesador lo maneja el hardware, que lo llena solo en un miss y lo mantiene coherente entre núcleos; el look-aside lo maneja la aplicación a mano, y nadie garantiza que lo que hay en el caché coincida con la base. Ese es justamente el problema del resto de la clase.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/look-aside-cache.jpg' | relative_url }}" alt="Look-aside cache: la app, memcache, la base y los pasos del algoritmo">
  <figcaption>
    <span class="figura-label">Figura</span>
    el look-aside cache — la app con una flecha hacia memcache y otra hacia la base de datos, con los cuatro pasos del algoritmo (buscar en el caché; hit → return; miss → buscar en la DB, actualizar el caché, return)
    <span class="figura-ref">notas pág. 4 / pizarra pág. 4</span>
  </figcaption>
</figure>

Ahora la cuenta, que le da sentido a todo el rodeo por la teoría de colas. Supongamos un hit ratio del 98%. Parece muchísimo, pero en sistemas bien diseñados, con localidad temporal de las claves, no es raro: es el número al que se apunta. Supongamos que Redis responde en 1 milisegundo y Postgres en 10, por inventar un número; a veces tarda más. Y supongamos que la base tiene `max_connections = 100`.

Sin caché, la base aguanta como mucho `100 / 10 ms = 10.000` queries por segundo, y con una query por request ese es el techo de todo el sistema: por más servidores web que pongamos adelante, no pasa de ahí. El caché no cambia ese techo de la base, porque sus 100 conexiones siguen tardando 10 milisegundos por query. Lo que cambia es cuántos requests llegan hasta ella. Con un hit ratio del 98%, solo el 2% pasa por la base —la `V` baja de 1 a 0,02—, así que esas mismas 10.000 queries por segundo alcanzan para `10.000 / 0,02 = 500.000` requests por segundo: 50× más capacidad. En general, si `h` es el hit ratio, la base soporta `1/(1 − h)` veces más tráfico. La velocidad del caché no aparece en la cuenta; lo que importa es cuánto filtra. Con 90% ganamos 10×, con 98% ganamos 50× y con 99% ganamos 100×: pasar de 98 a 99 duplica la capacidad, y por eso se pelea cada punto de hit ratio.

El promedio pesado de los tiempos también dice algo, pero de otro recurso. En look-aside un miss cuesta el caché más la base, 11 milisegundos, así que un request tarda en promedio, visto desde la app, `0,98 × 1 ms + 0,02 × 11 ms = 1,2 ms`. Si lo que limita es la capa web, porque cada thread queda bloqueado esperando la respuesta, la ley de Little con la misma `L` de threads da unas 8× más capacidad para esa capa. Pero esa es la capa que se escala fácil, agregando servidores; la que motivaba el caché es la base, y ahí la ganancia es de 50×.

Una vez que la base deja de limitar, el techo lo pone otro: el propio caché, o la capa web. La diferencia es que el caché sí escala fácil, porque las claves se reparten entre muchos servidores; sobre eso volvemos más adelante.

{: .nota }
> La cuenta por recurso es lo que en la literatura de performance se llama la ley del cuello de botella (*bottleneck law*): para cada recurso, el throughput del sistema está acotado por `N/D`, con `N` su paralelismo y `D = V · S` la demanda que cada request le pone; el recurso con el cociente más chico es el cuello de botella (Harchol-Balter, *Performance Modeling and Design of Computer Systems*, 2013; Lazowska et al., *Quantitative System Performance*, 1984). Con el caché, la `V` de la base es `1 − h`, y de ahí sale el `1/(1 − h)`. Un promedio pesado de los tiempos no sirve para esta cuenta, porque mete en una única `L` dos recursos distintos, cuando un hit no ocupa ninguna conexión de la base.

Ese resultado se lee mal casi siempre. No agregamos el caché para que la query sea más rápida: lo agregamos porque obtuvimos cincuenta veces más capacidad con la misma base. ¿Para qué agregamos cachés? No es la respuesta que uno diría de entrada: no es para mejorar la experiencia de usuario.

La justificación viene de un terreno ajeno a la materia. En UX se manejan unos umbrales clásicos: por debajo de unos 100 milisegundos la respuesta se percibe instantánea, hasta un segundo se nota la demora pero no corta el hilo de lo que uno está haciendo, y pasados los diez segundos se pierde la atención (Nielsen, *Usability Engineering*, 1993). Hay otro número que se cita mucho, el umbral de Doherty (Doherty y Thadani, *The Economic Value of Rapid Response Time*, IBM, 1982): cuando el sistema responde en menos de unos 400 milisegundos, la productividad del usuario sube de forma marcada. Con esa vara, bajar una query de 100 milisegundos a 10 no se justificaría por el usuario, que no nota la diferencia. Lo que hacemos en realidad es establecer las condiciones de posibilidad para soportar mucho más tráfico con la misma base.

Con un matiz: una página no hace una query sino muchas —en el paper de Facebook, cargar una página popular trae en promedio 521 ítems de memcache—, en parte una detrás de la otra, así que los milisegundos que se ahorran por lectura se suman, y la demora de la página la domina la lectura más lenta. La experiencia de usuario no es el motivo principal, pero tampoco es irrelevante.

Todo este recorrido se resume en una línea. Cachés: objetivo, aumentar la capacidad del sistema, entendida como el throughput máximo. Dicho de otro modo, cuántos requests por segundo podemos soportar.

Y la cuenta muestra que proteger la base, que a veces se da como un segundo motivo, es en realidad el mismo. Un hit ratio del 98% no solo quiere decir que ese 98% de requests es más rápido, sino que es un 98% que se evitó ir a la base, y de ahí sale toda la ganancia de capacidad: podemos tener una base más chica que no se sature. Y hay un efecto más. Una base descargada trabaja lejos de la saturación, donde la espera en cola se dispara, así que también los misses se responden más rápido.

Nada de esto es tan obvio como parece una vez dicho. La idea no surge intuitivamente: la tendencia habitual, cuando aumenta el tráfico, es agregar paralelismo; si hay diez máquinas, pasar a veinte. Pensar qué se puede cachear para que la mayoría de los requests no lleguen a la base queda en segundo plano. En parte es porque eso es más difícil: es un tema de diseño. Agregar máquinas es casi automático: basta con modificar un parámetro en el proveedor de cloud. Los cachés hay que pensarlos: cuál es la clave, agregar un componente nuevo al sistema. Por eso se posterga, y sin embargo es fundamental para escalar el throughput.

Con eso llegamos adonde había que llegar en esta primera mitad. Los cachés no son para que ande más rápido, son para que el sistema tenga más capacidad, y eso es lo que quería Facebook. Que se perciba más rápido es un efecto secundario deseable, pero secundario. Manejándonos en pocos milisegundos, con internet en el medio enlenteciendo todo, uno pensaría que no se justifica un caché; sí se justifica, y la justificación viene de la teoría de colas y de esa fórmula con exactamente dos perillas, de las que el caché gira la segunda sin tocar la base: no hace más rápidas sus queries, hace que le lleguen muchas menos. Lo que sigue son las sutilezas que complican el asunto, que son unas cuantas y ocupan el resto de la clase.

---
