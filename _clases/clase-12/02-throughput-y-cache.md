---
title: "2. Throughput y caché"
parent: "Clase 12 — Memcache en Facebook"
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

Volvamos al sistema web del principio, el del load balancer con los servidores stateless adelante de la base. Con la ley de Little lo podemos mirar de otra manera: igual que descompusimos el hospital, aquí podemos verlo como tres sistemas en serie: la capa de entrada, la capa de servidores web stateless y la base de datos. Para que el conjunto sea estable vale la misma condición que en el hospital: la λ que entra al primero tiene que ser igual a la que entra al del medio y a la que entra a la base.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/web-como-tres-sistemas.png' | relative_url }}" alt="El sistema web como tres sistemas en serie">
  <figcaption>
    <span class="figura-label">Figura</span>
    el sistema web original visto como tres sistemas en serie — load balancer, capa de servidores stateless y base de datos, con el mismo λ atravesando los tres
    <span class="figura-ref">notas pág. 3 / pizarra pág. 4</span>
  </figcaption>
</figure>

Visto así se entiende mejor qué hacíamos al agregar servidores en paralelo: aumentábamos la capacidad de la capa del medio subiendo el paralelismo. Ese paralelismo es la cantidad de clientes que se pueden atender simultáneamente, que es exactamente la `L` de la ley.

Con la base de datos pasa algo parecido, y se ve haciéndole zoom. Dentro suele haber un pool de conexiones, una cantidad máxima de conexiones; el parámetro se llama típicamente `max_connections`. Ese número es el paralelismo de la base.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/pool-de-conexiones.png' | relative_url }}" alt="La base de datos con su pool de conexiones">
  <figcaption>
    <span class="figura-label">Figura</span>
    zoom a la base de datos — un cilindro con su pool de conexiones dentro y la etiqueta max_connections = paralelismo
    <span class="figura-ref">notas pág. 4 / pizarra pág. 4</span>
  </figcaption>
</figure>

Mirando la ley con esto presente, cada cantidad tiene un nombre propio en la industria. La tasa de arribos, de la base y del sistema en general, se llama throughput, un término estándar al monitorear: los requests por segundo de un sistema son su throughput. La `L` es el paralelismo: según lo que miremos, la cantidad de threads o de conexiones simultáneas. Y la `W` es el tiempo promedio por query.

Puestas así aparece lo que veníamos buscando. El paralelismo típicamente es fijo, porque es un parámetro: la cantidad máxima de conexiones, o el tamaño del thread pool. El tiempo de las queries no es fijo ni lo controlamos del todo, pero tiene un promedio, una duración típica. Si conocemos el máximo de ese tiempo promedio y el máximo del paralelismo, tenemos un throughput máximo: el número que nos dice cuánto puede soportar el sistema.

Y ahí se vuelve importante la asimetría que anticipamos. λ es lo que no controlamos: es la demanda, aquello para lo que diseñamos el sistema. Si queremos aumentarlo, la ley nos deja exactamente dos caminos: aumentar la `L`, poner más paralelismo, o bajar la `W`, que las queries tarden menos. Despejando, `λ = L/W`, y se confirma con la lógica: más paralelismo, más throughput; queries más cortas, también. Son las dos únicas perillas que hay.

Cuando surgen problemas en producción y aparece un pico de clientes, lo que pasó es que aumentó muchísimo la λ. La reacción habitual, a menudo apresurada, es agregar más servidores. Es decir que la fórmula ya la conocíamos intuitivamente; lo que agregamos es la base matemática que explica por qué funciona. Más paralelismo, mejor.

Con la base de datos es más difícil, porque no es fácil agregar más bases. A lo sumo, más réplicas; pero si aumentan las escrituras la situación se complica, porque de la réplica solo se puede leer. La otra opción es parar la base y subirle la cantidad máxima de conexiones, pero en la práctica tampoco funciona demasiado bien: las bases no funcionan bien con una cantidad muy grande de conexiones. Cada conexión consume memoria —en Postgres, un proceso entero—, y a partir de cierto punto las conexiones compiten por los mismos locks y la misma CPU, y el throughput baja en lugar de subir.

Ante un pico, la respuesta habitual seguirá siendo aumentar el paralelismo. Pero cuando uno diseña el sistema desde el principio —y ese es exactamente el problema que tuvo Facebook— la salida es otra. Lo que trataron de hacer no fue tener muchísimo paralelismo, aunque el sistema termina teniéndolo, sino reducir enormemente el tiempo de las queries. Puede parecer sorprendente, pero es lo que nos lleva al tema de esta clase: los cachés. Un caché sirve, en definitiva, para reducir el tiempo de una query —siempre que se trate de queries repetidas—, más que para aumentar la velocidad.

## Efecto del caché sobre el throughput

Queremos reducir la `W`, y la herramienta es el caché. La idea no debería ser nueva: en las materias de procesadores apareció un caché que es básicamente lo mismo, aunque el nuestro sea de otro tipo.

Instalamos un sistema aparte. El clásico es memcached, un sistema viejo; hoy la alternativa más nombrada es Redis. Su funcionamiento es sencillo: es un hashmap en memoria y nada más. A favor, es muy rápido; en contra, es muy poco versátil. Se hacen dos operaciones y no hay una tercera: un `get` de una clave, y un `set` —o `store`— de una clave y un valor. Con esa austeridad los tiempos quedan en el orden de un milisegundo como mucho, contando la red, porque típicamente memcache va en otra máquina: hay un cluster aparte dedicado a los memcaches. También se lo puede poner en las mismas máquinas que atienden los requests, pero eso no tiene tanto sentido frente a lo que vamos a ver que hizo Facebook.

El caché no desplaza a nadie: la fuente de verdad sigue siendo la base de datos. La técnica típica para combinar las dos piezas se llama look-aside cache, y tiene cuatro pasos. El request llega a la app, que se fija primero si lo que necesita está en memcache. Si está, lo devuelve desde ahí: un hit. Si no, va a la base, hace la query común y corriente, guarda el resultado en el caché y solo entonces devuelve. La próxima vez que venga el mismo request lo va a encontrar en el caché. Es la misma mecánica de los cachés de procesador.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/look-aside-cache.jpg' | relative_url }}" alt="Look-aside cache: la app, memcache, la base y los pasos del algoritmo">
  <figcaption>
    <span class="figura-label">Figura</span>
    el look-aside cache — la app con una flecha hacia memcache y otra hacia la base de datos, con los cuatro pasos del algoritmo (buscar en el caché; hit → return; miss → buscar en la DB, actualizar el caché, return)
    <span class="figura-ref">notas pág. 4 / pizarra pág. 4</span>
  </figcaption>
</figure>

Ahora la cuenta, que le da sentido a todo el rodeo por la teoría de colas. Supongamos un hit ratio del 98%. Parece muchísimo, pero en sistemas bien diseñados, con localidad temporal de las claves, no es raro: es el número al que se apunta. Supongamos que Redis responde en 1 milisegundo y Postgres en 10, por inventar un número; a veces tarda más. Hacemos el promedio pesado: `0,98 × 1 ms + 0,02 × 10 ms = 1,18 ms`. Y a la ley de Little le importan justamente los promedios. Al agregar ese caché redujimos la `W` de 10 milisegundos a 1,18, y eso es aproximadamente 8× más capacidad.

Ese resultado se lee mal casi siempre. No agregamos el caché para que la query sea más rápida: lo agregamos porque obtuvimos ocho veces más capacidad para procesar queries. ¿Para qué agregamos cachés? No es la respuesta que uno diría de entrada: no es para mejorar la experiencia de usuario.

La justificación viene de un terreno ajeno a la materia. En UX se maneja una regla, el umbral de Doherty (Doherty y Thadani, *The Economic Value of Rapid Response Time*, IBM, 1982), según la cual hasta unos 400 milisegundos la respuesta es imperceptible: el usuario la ve como instantánea. Si son más de 400 milisegundos, o un segundo, ahí sí la percibe lenta. Con esa vara, bajar de 100 milisegundos a 10 no justificaría un caché, porque el usuario no nota la diferencia. Lo que hacemos en realidad es establecer las condiciones de posibilidad para soportar diez veces más tráfico, porque redujimos por diez el tiempo de cada request.

Todo este recorrido se resume en una línea. Cachés: objetivo, aumentar la capacidad del sistema, entendida como el throughput máximo. Dicho de otro modo, cuántos clientes podemos soportar en paralelo.

Y hay una segunda razón, mirando el mismo número desde otro ángulo. Un hit ratio del 98% no solo quiere decir que ese 98% de requests es más rápido, sino que es un 98% que se evitó ir a la base. Eso la descarga: podemos tener una base más chica que no se sature. Proteger la base de datos es el otro motivo.

Nada de esto es tan obvio como parece una vez dicho. La idea no surge intuitivamente: la tendencia habitual, cuando aumenta el tráfico, es agregar paralelismo; si hay diez máquinas, pasar a veinte. Pensar qué se puede cachear para que cada request sea mucho más corto queda en segundo plano. En parte es porque eso es más difícil: es un tema de diseño. Agregar máquinas es casi automático: basta con modificar un parámetro en el proveedor de cloud. Los cachés hay que pensarlos: cuál es la clave, agregar un componente nuevo al sistema. Por eso se posterga, y sin embargo es fundamental para escalar el throughput.

Con eso llegamos adonde había que llegar en esta primera mitad. Los cachés no son para que ande más rápido, son para que el sistema tenga más capacidad, y eso es lo que quería Facebook. Que se perciba más rápido es un efecto secundario deseable, pero secundario. Manejándonos en pocos milisegundos, con internet en el medio enlenteciendo todo, uno pensaría que no se justifica un caché; sí se justifica, y la justificación viene de la teoría de colas y de esa fórmula con exactamente dos perillas. Lo que sigue son las sutilezas que complican el asunto, que son unas cuantas y ocupan el resto de la clase.

---
