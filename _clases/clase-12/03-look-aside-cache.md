---
title: "3. Look-aside cache"
parent: "Clase 12 — Consistencia en cachés"
nav_order: 3
---

# 3. Look-aside cache
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Tipos de caché y arquitectura de Facebook

Hay una distinción previa que ordena todo: existen dos tipos de caché, y uno es mucho más común en los sistemas reales.

El primero es el que venimos usando sin nombrarlo. Se llama look-aside, mirar para el costado, y el nombre describe el dibujo: la aplicación, memcache y la base de datos, con la aplicación conectada por separado a cada una de las otras dos. El flujo ya lo conocemos: primero el caché, y si no está, la base, y se actualiza el caché.

El segundo se parece al de los procesadores, y quien haya visto cachés de CPU lo va a reconocer. Se llama look-through, mirar a través. La aplicación se conecta solo con el caché, y el caché con la base: siempre se accede a la base a través del caché. Esa caja del medio no se puede rotular memcached, porque memcached no funciona así: va un caché genérico, una pieza que hay que construir para el caso.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/look-aside-y-look-through.png' | relative_url }}" alt="Look-aside y look-through">
  <figcaption>
    <span class="figura-label">Figura</span>
    los dos tipos de caché — look-aside, con la app conectada por separado al caché y a la base; look-through, con la app, el caché y la base encadenados en línea recta
    <span class="figura-ref">notas pág. 5 / pizarra pág. 5</span>
  </figcaption>
</figure>

Esa segunda forma requiere pensarla mucho más, y se ve al preguntarse qué tiene que saber hacer la caja del medio. Tiene que tener lógica de negocio, porque hace una traducción. La aplicación le manda las operaciones típicas de un caché, un `get` de una clave y nada más. Si no la tiene, el caché tiene que saber armar la query, ir a la base, obtener el dato, guardárselo y devolvérselo al cliente.

A cambio hay una ventaja real, que anticipa buena parte de lo que sigue: look-through se lleva dentro de esa capa los problemas de consistencia con los que vamos a tropezar. En look-aside hay datos de un lado y del otro, con la base como fuente de verdad, y esos dos conjuntos se van a desincronizar: de ahí salen las race conditions. Look-through esconde ese asunto en la capa intermedia.

Y sin embargo, ese diseño casi nunca se implementa. Es mucho más difícil, porque requiere construir un sistema de caché entero. Es más fácil tomar Redis o memcached, ya hechos, y armar alrededor el look-aside. Y look-aside es exactamente lo que usó Facebook en el paper que nos ocupa de aquí en adelante: *Scaling Memcache at Facebook*, de Nishtala y otros, NSDI 2013.

El sistema completo empieza por una cuestión de geografía: Facebook estaba en muchas regiones separadas, en distintos lugares del mundo o de Estados Unidos, con data centers enteros que tenían réplicas de todo.

Esa dispersión no es exclusiva de Facebook: cualquier servicio de escala global reparte sus data centers por región. Un request va al data center más cercano, y si se cae uno siguen funcionando los otros. La redundancia típica, tan deseable.

Dentro de cada región hay tres capas. Arriba, los servidores de frontend, una capa stateless: los mismos Apache o nginx del principio. En el medio, un cluster de memcache shardeado: no se guarda todo en cada memcache, sino que la información se distribuye entre ellos, parecido a como se distribuían los datos en MapReduce. Abajo, la base de datos, con dos propiedades superpuestas. Está particionada: distintos usuarios viven en distintas bases, aunque el paper no especifica el criterio; es razonable imaginar que sea por usuario. Y esas bases están replicadas a la otra región.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/arquitectura-de-facebook.jpg' | relative_url }}" alt="Las regiones primary y secondary de Facebook">
  <figcaption>
    <span class="figura-label">Figura</span>
    la arquitectura de Facebook — dos regiones, primary y secondary, cada una con una fila de frontends stateless, una fila de memcaches shardeados y las bases particionadas; la flecha de escritura cross región desde el frontend del secondary hasta la base del primary, y la flecha de replicación primary-backup entre las bases
    <span class="figura-ref">notas pág. 5 / pizarra pág. 5 / figura 2 del paper</span>
  </figcaption>
</figure>

La replicación es primary/secondary: se escribe en el master, y las secondary sirven solo para lecturas. Eso encaja con el perfil de carga: Facebook, como casi todas estas redes sociales, tiene muchísimas más lecturas que escrituras. Todo está optimizado para mucho throughput de lecturas, no tanto de escrituras.

¿Qué ocurre cuando la escritura llega a la región equivocada? Según el paper, si alguien manda una escritura en una región secondary, llega al servidor web, y este la manda a la base de la otra región: una escritura cross región. Eventualmente, por la replicación, el dato llega también a las bases locales. Lo que no se puede, por cómo funciona primary/secondary, es ir directo a la réplica local, que es de solo lectura.

Esa primera cuestión ya alcanza para ver que el asunto no es simple: entre regiones hay muchas piezas que sincronizar. Conviene concentrarse primero en una sola región, y dejar para después cómo se sincronizan los cachés entre regiones.

## Lectura, escritura e invalidación

Dentro de una región, la pregunta es cómo funciona una lectura. Escribamos el algoritmo del look-aside tal cual, porque de esas pocas líneas salen todos los problemas del resto de la clase. Queremos hacer un `read` de la clave `k`. La clave puede representar cualquier dato: qué se guarda bajo ella lo define la lógica de Facebook —un usuario, la dirección de la foto de perfil, lo que sea—. Solo importa que haya una clave y un valor. Primero tratamos de obtener el valor del caché con un `get(k)` a memcache. Si vuelve nulo, vamos a la base: un fetch que en la práctica será un `select`, o lo que corresponda. Con el valor en la mano lo guardamos en el caché con un `set(k, v)`, y solo entonces lo devolvemos. Es lo mismo que describimos en palabras, un algoritmo que se habrá visto en varias materias.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/algoritmos-read-write.png' | relative_url }}" alt="Los algoritmos read y write del look-aside">
  <figcaption>
    <span class="figura-label">Figura</span>
    los algoritmos read(k) y write(k,v) del look-aside, con la anotación de a qué componente le habla cada línea y el delete marcado como invalidación de caché
    <span class="figura-ref">notas pág. 5 / pizarra pág. 9 / figura 1 del paper</span>
  </figcaption>
</figure>

Cada línea le habla a un componente distinto, y ahí está la sustancia: el `get` y el `set` van a memcache; el fetch del medio va a la base. Son los dos componentes que van a interactuar, y van a generar problemas muy pronto, porque se desincronizan apenas haya varios usuarios haciendo lo mismo al mismo tiempo.

Falta la escritura. Un `write` de `k` y `v` tiene dos pasos, en este orden: primero escribe el valor en la base, y después hace un `delete(k)` en el caché. Esa segunda línea literalmente borra el valor, pero conceptualmente es una invalidación: no tiramos un dato, declaramos que lo guardado ya no vale.

Hay un atajo que se toma siempre con estos cachés, y conviene sacarlo del camino. Memcache, Redis y compañía suelen tener un *time to live*: a los 60 segundos, o a la media hora, según la configuración, el caché borra el valor por viejo. Casi no vamos a hablar de ese mecanismo, porque se puede asumir que siempre puede llegar a pasar. Si el valor se borra solo, la próxima lectura no lo encuentra y recorre el camino largo.

Lo interesante es cómo hacer que una invalidación ocurra rápido. Para eso hay que hacer lo que dice el algoritmo: después de escribir en la base, la fuente de verdad, borrar el valor del caché, así el próximo que lo busque recorre el camino completo y enseguida el valor está de vuelta, actualizado.

Aun así, es consistencia eventual. Entre que se escribe en la base y se borra del caché alguien puede leer el valor viejo. Y está bien: los cachés look-aside nos ponen inevitablemente en consistencia eventual. Lo que no queremos es una consistencia eventual de media hora.

Es una distinción que se pasa por alto con frecuencia notable. Un error común es agregar un caché sin pensar cómo se invalida, confiando en que el TTL lo borre solo a la media hora. Durante esa media hora el sistema puede devolver datos incorrectos. Bajar el TTL a un segundo tampoco lo resuelve: con un segundo deja de servir como caché; el hit ratio se derrumba y todos los requests vuelven a pegarle a la base. Lo mejor es tener un TTL, por las dudas, porque suele restaurar el sistema cuando algún bug extraño hace que algo no se borre. Pero las invalidaciones hay que pensarlas, y son la parte difícil, porque ahí empiezan las race conditions.

¿Por qué en la escritura pusimos un `delete` y no directamente el valor nuevo? Si escribimos `V2` en la base y el caché tenía `V1`, podríamos hacer un `set(k, V2)` y dejar el caché al día, sin obligar al próximo lector a ir a la base. Eso trae problemas, y es la primera cuestión de concurrencia que nos toca: la primera race condition de la clase.

Alcanza con dos clientes y la versión mal programada del frontend, la que hace `set` en lugar de `delete`. El cliente 1 escribe `X = 1` en la base. El cliente 2, con el mismo algoritmo, escribe `X = 2` en la base y hace su `set(X, 2)` en el caché. Y entonces llega el cliente 1, atrasado con su segundo paso, y lo sobrescribe con `set(X, 1)`. Al final, en la base `X` vale 2, que se escribió segundo, y en memcache vale 1. Una inconsistencia importante: con un TTL, memcache eventualmente se limpia, pero puede tardar media hora en limpiar ese `X = 1`.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-12/race-condition-set.png' | relative_url }}" alt="Race condition entre dos sets al caché">
  <figcaption>
    <span class="figura-label">Figura</span>
    la primera race condition — dos columnas, C1 y C2; C1 escribe X=1 en la base, C2 escribe X=2 y hace set(X,2), y C1 llega tarde con su set(X,1); el resultado es memcache con X=1 y la base con X=2
    <span class="figura-ref">notas pág. 6 / pizarra pág. 9</span>
  </figcaption>
</figure>

Si en cambio ponemos `delete(X)` y `delete(X)`, no pasa nada. Como dice el paper, el `delete` es idempotente: el orden no importa. Se borra dos veces, y la segunda probablemente ni haya nada que borrar. Después, el primero que lea se encuentra el caché vacío, va a la base, lee el valor actualizado —el 2— y solo entonces lo setea. Más adelante vamos a ver que las lecturas también pueden producir una race condition, pero al menos aquí los valores no quedan al revés.

La raíz de todos los males es que esto termina siendo una pequeña transacción distribuida: escribir algo en una base y después en otra, que es memcache, que aunque esté en memoria y no sea persistente es igualmente un storage de datos. Y las cosas pueden fallar en el medio. Puede escribirse en la base y que memcache falle y después reviva: el dato quedó en la base pero no en el caché. Eso no es tan terrible, porque la próxima lectura no lo va a encontrar en memcache, irá a la base y lo actualizará. Al revés sí puede haber problemas: si se actualiza primero memcache y después la base, y en la base no queda, el problema es mucho más serio.

---
