---
title: "5. Arquitectura, localidad y tolerancia a fallas"
parent: "Clase 2 — MapReduce"
nav_order: 5
---

# 5. Arquitectura, localidad y tolerancia a fallas
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Ya sabemos qué hace un mapper por dentro y qué hace un reducer. Ahora sí: ¿cómo es la arquitectura de todo eso? Quién reparte el trabajo, cómo se detecta que un nodo falló, y por dónde viajan los datos.

## El coordinador, los workers y los heartbeats

La figura 1 del paper es el esquema de ejecución completo. Tiene detalles que no hacen falta para entender lo esencial —el fork del programa del usuario, por ejemplo— y podemos dejarlos de lado. Lo importante que aparece ahí es esto: existe un **coordinador**, un proceso que se encarga de coordinar todo. El paper lo llama *master*; nosotros venimos diciéndole coordinador. Para lanzar un trabajo de MapReduce hay que comunicarse con él, y es él quien se encarga de asignarle trabajo a todo el mundo.

Ahora bien, la forma de repartir el trabajo que vamos a adoptar aquí es la inversa de la que cabría esperar. Del otro lado tenemos muchos workers genéricos, workers que de alguna manera reciben el código del map y el del reduce, y cómo lo reciben es un detalle. Y esos workers conocen al coordinador, no el coordinador a los workers.

La razón es que así resulta más simple de implementar. La alternativa sería pasarle al coordinador una lista de workers, y esa lista puede ser dinámica: los workers se agregan y se dan de baja, así que habría que mantenerla actualizada. En lugar de eso, el coordinador permanece fijo en su lugar, y el trabajo de encontrarlo queda del otro lado. Cuando un worker se levanta, se le pasa la dirección del coordinador —el nombre del proceso, el socket, lo que sea— y el worker le pregunta si hay trabajo para él. Esa es la pregunta básica.

Del lado del coordinador, lo primero que tiene que hacer cuando recibe un job es armar un plan de trabajo con los parámetros que ya conocemos. Con tres mappers y dos reducers, ese plan tiene una primera fase con M1, M2 y M3 —tres mappers distintos, cada uno con su input— y una segunda fase con el reducer 1 y el reducer 2.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la Figure 1 del paper anotada — el coordinador sobre el master, los heartbeats sobre la flecha del worker hacia él, y al costado el plan de trabajo en dos fases: primero M1, M2 y M3 con el worker 1 asignado a M1, después R1 y R2
    <span class="figura-ref">pizarra pág. 10</span>
  </figcaption>
</figure>

Con ese plan delante podemos volver sobre algo que quedó pendiente y contestarlo con precisión: por qué no se puede empezar con los reducers antes de que terminen todos los mappers. Lo que un reducer tiene que hacer es agregar todas las apariciones de la misma clave: tomar todas las K1 que emitieron todos los mappers. Si lanzamos el reducer antes de que M3 haya terminado, cuando ese tercer resultado todavía no está, el reducer va a considerar solamente las claves de los dos primeros mappers, y se van a perder todas las claves del mapper que todavía no terminó. Ese es, en general, un problema de MapReduce: hay que terminar todos los mappers para conocer todas las claves que aparecieron —todas las K1, en este caso— antes de poder enviárselas a los reducers.

Tiene, de todos modos, un aspecto favorable, porque nos simplifica el trabajo en el coordinador. El coordinador tiene que hacer dos fases y nada más: en la primera, encontrar la forma de repartir el trabajo de ejecutar M1, M2 y M3; y en la segunda, cuando esas tres terminaron, repartir el de R1 y R2.

La mecánica de la asignación es entonces directa. Un worker pregunta si hay trabajo para él, y el coordinador le responde que sí y le asigna, por ejemplo, la tarea M1. El coordinador, a partir de ahí, tiene que recordar que ese trabajo lo está haciendo el worker 1. Y después necesita algún mecanismo para verificar que ese worker está progresando: que el worker, cada tanto, le envíe una señal indicando que todo está bien. Esas señales se llaman **heartbeats**, y lo que el worker comunica con cada una es, básicamente, que sigue progresando y que no debe darse por caído.

De ahí sale la primera pieza de la tolerancia a fallas, que vamos a ver en detalle enseguida. Si el worker al que le asignamos M1 deja de enviar heartbeats —falló, agotó su memoria, dejó de responder—, el coordinador puede decidir asignarle ese M1 a otro worker diferente, y con eso el trabajo sigue avanzando.

{: .nota }
> Conviene saber que el sistema del paper hace las dos cosas en la dirección contraria a la que describimos aquí, y que la elección de arriba es una decisión de diseño legítima pero distinta. En §3.1 el paper dice que **el master elige workers que están ociosos y le asigna a cada uno una tarea** de map o de reduce: la iniciativa es del master, que por lo tanto sí conoce a sus workers. Y en §3.3, sobre la detección de fallas, dice que **el master le hace ping a cada worker periódicamente**, y que si no recibe respuesta en un cierto tiempo marca a ese worker como fallado; o sea que el latido va del coordinador hacia el worker y no al revés. Las dos variantes resuelven lo mismo y el argumento de la clase a favor de la que adoptamos se sostiene: si los workers son los que buscan al coordinador, la lista de workers no hay que mantenerla en ningún lado y se pueden agregar y quitar máquinas sin avisarle a nadie. Es la diferencia entre un modelo *pull* y un modelo *push*, y vale tener presente cuál es cuál al leer el paper.

## La red como cuello de botella: co-locación con GFS

El problema principal de todo este sistema, según el paper, era la red: mover datos de un lugar a otro.

Y ahí hay dos partes bien distintas. Una es el shuffle, donde no hay demasiado margen: es inevitable que muchas máquinas le tengan que enviar información a muchas otras, y ese costo hay que pagarlo. La otra es la parte en que los mappers reciben su input y los reducers emiten su output, y esa sí se podía optimizar, porque no tiene por qué viajar de un lugar a otro.

Lo que hicieron obliga a adelantar de manera general algo del Google File System, que vamos a estudiar en detalle unas clases más adelante. MapReduce se ejecutaba en nodos que tenían un worker, sí, pero que además tenían un **chunk server**, que es un concepto de GFS. En los mismos nodos convivían entonces los servidores de MapReduce y los servidores del Google File System. Lo que hace un chunk server es usar los discos locales de la máquina para guardar pedazos de archivos gigantes, de 64 MB cada uno; el Google File System se encarga de que todos esos pedazos repartidos entre muchas máquinas parezcan un único archivo gigantesco, y cada pedazo de 64 MB es un chunk. Ese número explica hacia atrás el ejemplo de los mil mappers: mil chunks de 64 MB son un archivo de 64 GB, así que la cantidad de mappers no es un número elegido arbitrariamente sino una consecuencia de en cuántos pedazos quedó dividido el archivo de entrada.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    un nodo que contiene a la vez un worker de MapReduce y un chunk server de GFS, con el coordinador decidiendo qué map asignarle según qué chunks tiene en su disco local
    <span class="figura-ref">notas pág. 5, fig. 2 / pizarra pág. 9</span>
  </figcaption>
</figure>

La solución que adoptaron en Google fue ingeniosa: hacer que esos chunks funcionen directamente como los inputs de los mappers. Todo funcionaba de manera coordinada. Cuando el coordinador tiene que asignarle trabajo a una de esas máquinas físicas, en vez de darle un map cualquiera observa cuáles de los chunks que la máquina ya tiene en su disco local le hacen falta a algún mapper, toma uno de esos y se lo asigna. Así, en lugar de ir por la red a buscar ese chunk, la lectura del input es una lectura local de disco.

Esto es *best effort*: de lo que se trata es de reducir al máximo la necesidad de ir a otra máquina a buscar un chunk para poder ejecutar el mapper, no de garantizar que nunca haga falta.

{: .nota }
> La sección 3.4 del paper, *Locality*, agrega dos precisiones que explican por qué este best effort acierta tan seguido. La primera es que GFS no guarda cada bloque de 64 MB en una sola máquina sino que mantiene **varias copias, típicamente tres**, en máquinas distintas: el coordinador no tiene un único candidato donde el chunk es local, tiene tres. La segunda es que el best effort tiene **dos niveles y no uno**: si no consigue programar la tarea en una máquina que tenga una réplica del dato, intenta programarla *cerca* de una réplica — por ejemplo, en una máquina que esté colgada del mismo switch de red que la que tiene el dato. El resultado que el paper reporta es contundente: cuando se corren operaciones grandes de MapReduce sobre una fracción significativa de los workers del clúster, la mayor parte del input se lee localmente y no consume ancho de banda de red.

Del lado del reducer se hace lo mismo. En vez de que cada reducer tenga que escribir su output en un chunk server remoto, se elige el local: el chunk que sale es el mismo, pero queda en la propia máquina, y con eso se evita que el output se disperse por la red. Por eso el paper de MapReduce dice que los inputs y los outputs los toma del Google File System, que es justamente el sistema que vamos a ver después.

El shuffle, en cambio, quedó afuera de esta optimización y se hace con comunicación directa entre los nodos. Ahí no aparece GFS: un worker de MapReduce se comunica con otro worker y se intercambian los archivos que se tienen que intercambiar. La razón es que el beneficio de guardar esos archivos intermedios en el Google File System era escaso, porque de todos modos había que enviarlos por la red.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el nodo con su worker y su chunk server, el chunk de 64 MB en el disco local entrando como input, y la flecha del shuffle saliendo directamente hacia otro worker
    <span class="figura-ref">pizarra pág. 9</span>
  </figcaption>
</figure>

Esta última optimización es una de las combinaciones más interesantes que vamos a ver, y vale volver sobre ella cuando estudiemos el Google File System, que es donde termina de cerrar. Lo que hicieron fue combinar los dos primeros sistemas de la materia —el de cómputo y el de storage— de manera tal que cada uno le resolviera al otro su problema más costoso.

## Reintentar y la condición de determinismo

Y ahora sí, la tolerancia a fallas. Vale empezar por una observación: la de MapReduce es la más simple de todas las que vamos a ver. No es un accidente, sino la consecuencia de una decisión de diseño que atraviesa el sistema entero.

La decisión es esta: todo está hecho de manera tal que cada unidad de trabajo —mappers y reducers— se pueda ejecutar más de una vez sin que eso comprometa el resultado y sin que aparezcan duplicados. Veamos por qué vale en el caso del mapper, que escribe sus archivos localmente, en su propio disco. Si ese worker falla y otro worker toma ese mismo map y hace lo mismo, termina escribiendo lo mismo. No queda ningún residuo anómalo: quedan los mismos archivos, en otra máquina.

¿Cuál es entonces la estrategia básica de tolerancia a fallas? Reintentar los trabajos que fallaron. Es toda la estrategia, y ahí está su simplicidad.

Hay, eso sí, un requisito importante, y se ve mejor con un escenario concreto. Tenemos un mapper que genera un archivo y falla, otro mapper que reintenta ese mismo trabajo, y un reducer que recibe la mitad de sus archivos de una de esas dos ejecuciones y la otra mitad de la otra. Esos archivos tienen que ser iguales. ¿Cómo se garantiza eso? No se garantiza. Lo tiene que garantizar quien escribe el programa: hay que asegurarse de que los mappers sean deterministas. Si a un mapper se le da un input y genera una cantidad N de archivos intermedios, esos archivos siempre tienen que ser los mismos.

Es una condición del sistema, no una recomendación. Map y reduce tienen que ser deterministas, y de ahí salen tres prohibiciones concretas: no pueden generar números aleatorios, no pueden hacer entrada y salida, y en general no pueden tener estado. Si volvemos a ejecutar el mapper, el resultado no puede ser distinto del de la vez anterior. Es muy parecido a la idempotencia, en ese sentido.

La prohibición que más resistencia genera es la de entrada y salida. ¿Por qué el mapper no puede hacer entrada y salida? Su input es el archivo de entrada, y con eso no hay problema. Lo que no puede hacer es pedirle algo por consola a una persona, o conectarse a la red para obtener la hora actual. Puede acceder a recursos externos, siempre y cuando eso no cambie el resultado final. Si accede a un archivo externo que es modificable, o a un servidor que le devuelve la hora, es muy probable que el diseño sea incorrecto. Así que no está estrictamente prohibido hacer entrada y salida: lo que está prohibido es hacerla de una forma que cambie el resultado.

{: .nota }
> El paper es preciso sobre este "no estrictamente prohibido", y la precisión vale. Cuando map y reduce son funciones deterministas de sus valores de entrada, la implementación distribuida produce **la misma salida que produciría una ejecución secuencial sin fallas** del programa entero: esa es la garantía fuerte, y es la que se pierde al romper el determinismo. Cuando los operadores son no deterministas, el paper dice que ofrece semánticas **más débiles pero todavía razonables**, y explica en qué consiste esa debilidad: la salida de una tarea de reduce dada equivale a la que produciría *alguna* ejecución secuencial del programa no determinista, pero la salida de otra tarea de reduce puede corresponder a una ejecución secuencial **distinta**. Es decir que cada partición del resultado es individualmente coherente, y el conjunto puede no corresponder a ninguna corrida única. De ahí que hacer entrada y salida no esté prohibido sino que degrade la garantía.

{: .nota }
> La sección 3.3 del paper agrega una asimetría que se deduce de todo lo que ya vimos y que conviene tener explícita. Cuando un worker se cae, **las tareas de map que ya había completado se vuelven a ejecutar**, porque su output quedó en el disco local de la máquina caída y es por lo tanto inaccesible; pero **las tareas de reduce ya completadas no hace falta re-ejecutarlas**, porque su output está en el sistema de archivos global. La distinción entre disco local y GFS que motivaba la co-locación reaparece aquí determinando qué se pierde y qué no. El paper también da el mecanismo concreto detrás de que el coordinador use una sola versión de cada mapper: cuando una tarea de map la ejecuta primero el worker A y después el worker B porque A falló, **todos los workers que están ejecutando tareas de reduce son notificados de la re-ejecución**, y cualquier reduce que todavía no haya leído los datos de A los va a leer de B. Como muestra de que el mecanismo funciona en la práctica, el paper cuenta que durante una operación de MapReduce un mantenimiento de red dejaba inalcanzables grupos de 80 máquinas por varios minutos, y el master simplemente re-ejecutó el trabajo de las máquinas inalcanzables y siguió avanzando.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la estrategia de tolerancia a fallas —reintentar los trabajos que fallaron— y la condición que la habilita: map y reduce deterministas, sin números aleatorios, sin entrada/salida y sin estado
    <span class="figura-ref">pizarra pág. 9</span>
  </figcaption>
</figure>

## Ejecución especulativa y renames atómicos

Si quien programa cumple con esa condición, MapReduce va a reintentar los trabajos cuando fallen. Y va a hacer además lo que venimos anticipando: reintentarlos también cuando no fallen.

La mecánica es la que apareció con los heartbeats. Si el coordinador observa que un map está lento, que no progresa y que todos están esperando ese map, entonces —a pesar de que no haya fallado nada— puede iniciar el mismo job en otro nodo y dejar que los dos compitan entre sí. El primero que termina define el resultado. El trabajo del segundo se descarta, sin consecuencias.

Lo que se obtiene a cambio de ese desperdicio se ve poniéndole números al nodo lento. Un disco que se degrada de 30 MB/s a 1 MB/s —uno de los dos casos de nodo lento que da el paper— multiplica por treinta lo que tarda una tarea: la que en una máquina sana lleva un minuto, ahí lleva media hora. Y la fase no termina hasta que termina la última tarea, así que ese único nodo defectuoso retrasa el job entero.

Lo que hace que eso no altere el resultado es que el coordinador toma una sola versión de cada mapper. No le va a enviar dos veces el mismo archivo a un reducer, uno salido de cada mapper reintentado: esa parte la resuelve correctamente, y los reducers terminan trabajando con los mismos archivos, hayan salido de la primera ejecución o de un reintento.

Del lado del reducer el mecanismo es otro. El output del reduce, como vimos, va al Google File System, que tiene una forma de hacer escrituras atómicas. Lo que hace el reducer es generar ahí un archivo temporal y, al final, cambiarle el nombre. Ese es el output definitivo.

Si hay dos réplicas del reducer 1 trabajando en lo mismo, las dos van a estar escribiendo en el Google File System, pero en archivos temporales distintos. Eventualmente una termina y le cambia el nombre a su temporal, que queda como el output definitivo. La otra probablemente también termine y le cambie el nombre al suyo; ese archivo va a sobrescribir al primero. Pero como el reduce es determinista, el contenido es igual al que ya estaba, y el resultado no se altera. El trabajo duplicado no aportó nada, y el resultado final es exactamente el mismo.

{: .nota }
> El paper llama a esto **backup tasks** y lo trata en §3.6, con un disparador algo distinto del que describe la clase. No es que el coordinador vigile a cada tarea y reaccione al verla lenta: lo que hace es esperar a que la operación de MapReduce esté **cerca de completarse** y ahí programar ejecuciones de respaldo de todas las tareas que todavía siguen en curso, marcando cada una como completada en cuanto termina la primaria o la de respaldo, cualquiera sea. Está calibrado para que el costo no pase de unos pocos por ciento de recursos adicionales, y lo que compra es mucho: el paper mide que el programa de sort que usa como benchmark tarda un **44% más** en completarse cuando se desactiva el mecanismo de backup tasks. Los dos ejemplos de straggler que da son buenos para entender de dónde viene el problema: una máquina con un disco en mal estado, cuyos errores corregibles frecuentes le bajaban la velocidad de lectura **de 30 MB/s a 1 MB/s**; y un bug en el código de inicialización de las máquinas que dejaba deshabilitadas las cachés del procesador, lo que hacía a las máquinas afectadas **más de cien veces más lentas**.

## El talón de Aquiles: si falla el coordinador

Queda el caso que el esquema no cubre: ¿qué ocurre si falla el coordinador? Ahí el sistema queda en serios problemas, porque falla todo. Hay que iniciar todo el MapReduce nuevamente, y ese era uno de sus puntos débiles.

Se puede hacer algo para mitigarlo, aunque no lo resuelva. El coordinador podría guardar su estado en un disco rígido en vez de mantenerlo todo en memoria, porque el plan de trabajo y toda esa información administrativa la estábamos suponiendo implícitamente en memoria: un array con todos los jobs y el registro de quién fue tomando cada uno. Si eso se va persistiendo en un archivo, tal vez se pueda recuperar algo: si falla el coordinador, se lo vuelve a levantar y es posible que se restablezca. Pero en general este sistema no es muy resistente a que falle el master. Por defecto, si el master falla, hay que reintentar todo el trabajo.

{: .nota }
> El paper describe la mitigación en los mismos términos y da además la razón por la que decidieron no implementarla. Dice que es fácil hacer que el master escriba **checkpoints periódicos** de sus estructuras de datos, y que si el master muere se puede arrancar una copia nueva desde el último checkpoint. Pero agrega: dado que hay un **único** master, su falla es improbable, y por eso la implementación de entonces aborta la computación entera si el master falla, dejando que los clientes detecten esa condición y reintenten la operación si quieren. O sea que el punto débil es una decisión consciente sobre un evento raro, no un descuido.

Y eso es todo. El sistema es relativamente simple y no incluye mucho más.
