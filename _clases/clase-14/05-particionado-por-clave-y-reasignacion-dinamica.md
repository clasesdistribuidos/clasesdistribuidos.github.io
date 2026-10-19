---
title: "5. Particionado por clave y reasignación dinámica"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 5
---

# 5. Particionado por clave y reasignación dinámica
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


En MillWheel los cómputos no son determinísticos. No son funciones puras: guardan estado. Esa diferencia con MapReduce —y también con Spark— quedó implícita hasta aquí, y explica buena parte de lo que viene.

Y eso cambia por completo qué se puede hacer cuando algo falla. Si un mapper o un reducer falla en MapReduce, la salida es simple y la conocemos: se reasigna el trabajo y se re-ejecuta desde el principio. La función es pura, la entrada sigue estando ahí, y volver a correrla da exactamente el mismo resultado. En MillWheel eso no se puede, y la razón de fondo es que faltan los récords de entrada. El nodo que se cayó consumía un flujo de eventos que ya pasó, no un archivo que sigue ahí para releerlo. No hay forma de hacer replay en todos los nodos del grafo; a veces sí en la fuente —cuando es un Kafka que guarda los eventos, como ya dijimos—, pero no en el medio del pipeline.

De ahí sale la necesidad del estado persistente que acabamos de ver. Si no se puede recalcular, hay que haber guardado: esa es la cadena de razonamiento que justifica todo el mecanismo. No es el único diseño posible: hay sistemas que eligieron el otro camino, el del replay desde la fuente, y el caso más conocido es Flink.

{: .nota }
> El caso más conocido de ese otro camino es Apache Flink, que resuelve la tolerancia a fallas con snapshots distribuidos —una variante del algoritmo de Chandy-Lamport, con barreras asincrónicas— en vez de con un checkpoint por récord. Cuando algo falla, Flink restaura el último snapshot y reposiciona las fuentes en los offsets que ese snapshot tenía guardados: en el caso de Kafka, le dice al consumidor desde qué offset volver a leer, y reprocesa todos los récords posteriores al checkpoint. Es decir que apoya toda su corrección en que la fuente sea reproducible, que es exactamente la propiedad que MillWheel decide no dar por supuesta.

Con eso arrancamos la implementación por la pregunta de cómo se escala. En el dibujo del grafo, las cajas superpuestas ya sugieren un sistema distribuido; hay que ver concretamente qué quieren decir.

## Particionado por clave y shuffle

Pensemos en un stream de enorme volumen; el mejor ejemplo es el de los tweets: un Kafka enorme, con miles de particiones, que contiene todos los tweets del mundo. Una única máquina procesando todo eso se cae: no hay máquina que aguante ese flujo.

¿Cómo se soporta un stream tan grande? Particionando por clave. Otra vez lo mismo: la única forma que sabemos de resolver las cosas es particionando.

Y ahí se entiende algo del récord que habíamos dejado pasar sin justificar. Su estructura era una clave, la data —digamos, bytes— y un timestamp. No es arbitrario que tenga clave: es obligatoria, y es lo que le informa al sistema cómo distribuir los récords entre las máquinas.

A partir de ahí hay paralelismos con MapReduce y cosas muy diferentes. Volvamos a dos etapas del grafo, el Window Counter y el Spike Detector, recordando que en el dibujo del paper cada una no es una caja sino muchas. Llamémoslas A y B. Dibujado en abstracto, una caja conectada a otra por una flecha no nos dice nada. En la vida real tenemos muchos nodos ejecutando particiones de A y muchos ejecutando particiones de B. Termina siendo algo parecido a MapReduce, pero continuo. El sistema tiene que hacer efectivamente un shuffle: si hay dos particiones de A, de cada una pueden salir eventos hacia todas las particiones de B, siempre que en el dibujo abstracto las dos etapas estén conectadas por una flecha. Esa flecha gruesa es, en la terminología de MapReduce, un shuffle. Y lo mismo con cualquier otra flecha: cada una que conecta dos etapas en el dibujo abstracto es, en la implementación, un shuffle entre las particiones de una y las de la otra.

## Intervalos lexicográficos de claves

Aquí, sin embargo, el asunto es bastante diferente, porque MapReduce empezaba con una configuración fija —tantos nodos para el mapper, tantos para el reducer— y no se movía demasiado. En MillWheel no solo hay un grafo entero en lugar de mappers y reducers: además el reparto es más dinámico. Como esto no termina nunca, los nodos siguen vivos constantemente; no empiezan, procesan y terminan. Inclusive se pueden dividir: si uno se satura, agregamos nodos para distribuir mejor la carga. Esas son las complejidades a resolver, a la vez una complicación y una mejora respecto de MapReduce.

De ahí sale que el truco de MapReduce no sirva. Allí tomábamos el hash de la clave y le hacíamos módulo N —módulo tres, si los reducers eran tres—. Eso funciona si el tres es fijo. En MillWheel no lo es, y el precio se puede poner en números: pasar de tres particiones a cuatro con `hash(clave) mod N` cambia de lugar el 75% de las claves, porque entre los dos módulos hay doce clases de resto posibles y solo en tres la clave se queda donde estaba. Entonces el particionado es diferente: a cada partición se le asigna un intervalo lexicográfico de claves. De la A a la H para una, de la H a la P para otra, de la P a la Z para la tercera, en el reparto más simple; en la realidad es más complicado. Es como las mesas de votación: cada mesa atiende un tramo del abecedario. El paper no aclara si le hace hash a la clave antes de ubicarla o si usa la clave tal cual, y para nuestros fines es indistinto; lo seguro es que asigna el intervalo. Con eso, dividir un nodo por la mitad es fácil: partimos el rango en dos, les informamos a los demás y empiezan a mandar por ahí. Partir así uno de los tres intervalos toca la mitad de un tercio del espacio de claves —un sexto, alrededor del 17%— y nada más: contra el 75% del módulo, esa es la razón concreta de que eligieran rangos y no hash. Esa es la primera complicación resuelta.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/shuffle-por-rangos.png' | relative_url }}" alt="Shuffle entre las particiones de A y las de B por rangos de claves">
  <figcaption>
    <span class="figura-label">Figura</span>
    el shuffle entre dos cómputos: las particiones de A mandando eventos a todas las particiones de B, y los rangos lexicográficos de claves de la A a la H, de la H a la P y de la P a la Z
    <span class="figura-ref">notas pág. 6 / pizarra pág. 10</span>
  </figcaption>
</figure>

Queda una pregunta sobre las flechas: ¿cómo se mandan los registros de un nodo a otro? No hay ningún Kafka secreto intermedio, ni broker ni cola: es RPC directo. El paper no aclara qué tecnología de RPC usa. No es gRPC, que no existía en la época del paper; pero como gRPC es de Google, debe tratarse de algún antecesor suyo, así que podemos imaginar algo parecido. Debe haber optimizaciones —el paper las menciona— y seguramente no manda récords individuales sino que agrupa varios en lotes para hacerlo más eficiente. Son RPCs directos entre nodos, y así se realiza un shuffle permanente, que nunca termina.

## Master y asignación de cómputo y rango

¿Quién controla todo esto? Hay un master, muy parecido al de MapReduce, y debajo los nodos que ejecutan el cómputo. Ese master podría ser una máquina sola, como en MapReduce; el paper aclara que es un subsistema replicado actuando como master, y podemos imaginar un Paxos adentro, una especie de Raft.

{: .nota }
> El paper dice literalmente que el balanceo de carga lo maneja un *replicated master*, y no nombra con qué protocolo está replicado: el Paxos es una suposición nuestra, no algo que diga el paper. Lo que sí especifica, y con estas palabras, es qué hace: divide cada cómputo en un conjunto de intervalos lexicográficos de claves que cubren todo el espacio posible, se los asigna a un conjunto de máquinas, y ante un aumento de carga de CPU o de presión de memoria —que le reporta un monitor por proceso— puede mover esos intervalos, partirlos o fusionarlos. Akidau et al., VLDB 2013, §7.1.

El master le asigna a cada máquina qué cómputo hacer y para qué rango. Si los cómputos son el Window Counter, el Spike Detector y los demás, a cada nodo que pida trabajo le indica: «serás Window Counter para este rango de claves». Todos los demás se enteran de que ese nodo físico hace ese rango y le mandan las cosas de ese rango para esa computación.

Es una especie de master dinámico. Si un nodo muere o se satura, el master puede asignarle ese rango de claves a otro nodo, o partirlo por la mitad y asignárselo a dos nodos diferentes. Es mucho más dinámico que MapReduce, y el motivo es siempre el mismo: esto no termina nunca.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/master-y-nodos.png' | relative_url }}" alt="El master y los nodos de cómputo">
  <figcaption>
    <span class="figura-label">Figura</span>
    el master con el grafo adentro y los nodos de cómputo debajo
    <span class="figura-ref">notas pág. 6 / pizarra pág. 10</span>
  </figcaption>
</figure>

Falta ver cómo asigna, que es interesante en sí mismo. El paper tampoco lo detalla: lo menciona al pasar y remite a Centrifuge, de Microsoft, que integra justamente las dos piezas que aquí hacen falta juntas, el manejo de leases y el particionado por rangos. De ahí tomó MillWheel la idea de reasignar cómputo basado en rangos de manera dinámica.

{: .nota }
> La referencia es Adya, Dunagan y Wolman, «Centrifuge: Integrated Lease Management and Partitioning for Cloud Services», NSDI 2010 (Microsoft Research). Conviene tener presente qué se toma prestado exactamente: lo que MillWheel dice haber tomado de Centrifuge es el mecanismo de imposición de leases, y su nombre para lo que en la clase llamamos epoch es *sequencer* —un token que viaja con cada escritura y que el mediador del backing store valida antes de dejarla commitear—. Cada intervalo tiene su sequencer único, y se invalida cada vez que el intervalo se mueve, se parte o se fusiona; un worker nuevo invalida los sequencers existentes antes de empezar a trabajar. Akidau et al., VLDB 2013, §6.2 y §7.1.

Al arrancar, el master tiene para cada cómputo un valor inicial de cuántas particiones quiere, y lo divide en partes iguales: un cómputo con tres particiones, otro con cuatro, otro con dos, según lo que le toque hacer. Y la idea es que haya más particiones que nodos, para que un nodo pueda tomar muchas: la misma idea de MapReduce, más trabajo que nodos disponibles, así se puede reasignar.

Desde esa configuración inicial, el master elige un nodo y le manda trabajo. Bien podría ser al revés, que el nodo pida trabajo, como en MapReduce; el paper no especifica las llamadas, así que lo que sigue es una reconstrucción. Esa llamada es un `assign`, que necesariamente lleva un compute ID —Window Counter, Model Calculator o el que sea—: le indica al nodo que asuma el rol de Window Counter. Cada nodo puede actuar de cualquiera de los cómputos: todos tienen básicamente el mismo código y se activan distintas partes dinámicamente para distribuir el trabajo, según lo que elija el master. El assign lleva además un epoch, parecido a un lease, que en un momento vamos a ver para qué sirve. Es una de las ventajas de llegar al final de la materia: a esta altura se puede combinar todo con todo, y el epoch es un buen ejemplo.

El assign tiene también una expiración —quizás fija, quizás informada por el master—, así que el nodo tiene que mandar un `renew` de vez en cuando. Ese renew funciona como heartbeat: cada cinco segundos, por ejemplo, el nodo le dice al master que sigue vivo y que todo está bien, o que está saturado.

Y hay una tercera llamada, que engancha con el estado persistente. Cuando a un nodo le asignan trabajo, tiene que comunicarse con el backing store, esa capa que por debajo usa Spanner o Bigtable, con un `reload state` que lleva el compute ID, el intervalo y el epoch. Si el sistema arranca de cero, no hay estado guardado y no pasa nada. El reload está para el otro caso: un nodo murió después de ir guardando estado persistente, y otro lo reemplaza. Lo primero que hace el nodo nuevo, antes de procesar un solo récord, es cargar todo lo que guardó el anterior. Para esto, entre otras cosas, usamos el persistent store en lugar de variables globales. Después empieza a ejecutar, y a medida que recibe récords va guardando otras cosas en ese storage.

## Nodos zombie y epoch

Y ahí aparece un problema interesante, la razón de ser del epoch. Había un nodo ejecutando ese cómputo para ese rango. Eventualmente falló un renew: se colgó el proceso, se saturó la máquina, se rompió la red. El master decidió que estaba muerto, dejó de considerarlo, y le asignó el mismo rango a otro nodo para que el trabajo siga avanzando. Lo que se quiere evitar es que el viejo trate de hacer un `set state` y los dos empiecen a sobrescribirse. No queremos dos nodos vivos a la vez ejecutando lo mismo.

El nodo viejo no tiene por qué morirse, y eso hay que precisarlo. Puede seguir vivo y ejecutando: si alguien le manda récords, los procesa. Lo que no puede pasar es que le pise el estado al otro, que hace exactamente lo mismo, porque los dos van a competir y corromper el estado.

La clave está en que el set state manda el estado y también el epoch. Cada vez que el master le asigna un rango a un nuevo nodo, incrementa el epoch. Se lo informa al nodo; el nodo, al hacer el reload, se lo informa al store; y el store sabe desde ese momento que para este compute ID y este intervalo el epoch es, por ejemplo, cuatro. Si un nodo zombie, que quedó atrás en la asignación anterior, quiere poner cualquier estado, el store lo rechaza por venir con un epoch viejo.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/reasignacion-con-epoch.png' | relative_url }}" alt="Assign, renew, reload state y el set state del zombie rechazado">
  <figcaption>
    <span class="figura-label">Figura</span>
    la reasignación dinámica de un rango: el assign del master con compute ID, intervalo y epoch, el renew que sube como heartbeat, el reload state contra el backing store, y el set state del nodo zombie rechazado por traer un epoch viejo
    <span class="figura-ref">notas pág. 7 / pizarra pág. 10</span>
  </figcaption>
</figure>

Así resuelven, con una especie de elección de líder —una variación más de todas las que vimos—, que no haya dos nodos escribiendo en la misma row del storage persistente y pisándose. Algo parecido hacía Google File System con las particiones. Aquí lo implementaron de nuevo, pero la idea es de Centrifuge.

Falta una pieza para la visión global: cómo se entera el resto del sistema. Los demás nodos saben que ese nodo está a cargo de ese cómputo porque el master se lo informa. Y si alguno se entera tarde y le sigue mandando cosas al zombie, no pasa nada: el zombie las procesará, pero no va a poder guardar el estado. Con eso queda cerrada la visión global de cómo cada parte se entera de lo que hacen las otras.

Con el escalado resuelto, queda la garantía de que cada récord se procese una sola vez.

---
