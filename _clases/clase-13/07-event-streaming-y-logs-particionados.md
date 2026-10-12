---
title: "7. Event streaming y logs particionados"
parent: "Clase 13 — Sistemas de mensajería"
nav_order: 7
---

# 7. Event streaming y logs particionados
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Log persistente

Queda el último modelo, el que anunciamos como event streaming, en su forma concreta: los logs particionados. Los dos nombres no son sinónimos y hay que usarlos con cuidado: el event streaming es un tipo de uso, no una arquitectura, y no siempre se implementa con logs particionados. Lo que vamos a ver es Kafka, que sí es un log particionado y que se usa muchísimo para streaming de eventos. Están tan asociados que se los confunde, pero uno no implica al otro.

Empecemos por el caso de uso, que le da sentido al diseño. ¿Qué es un stream de eventos? El paper de Kafka está lleno de ejemplos, pero alcanza con uno cercano. Cuando alguien navega una página web, todo lo que hace queda registrado: cada clic, cada interacción, cada cosa que abre, con un propósito concreto: ofrecerle después productos y publicidad. En Twitter ese flujo tenía nombre: cada vez que un usuario veía un tweet, le ponía «me gusta» o lo abría para leerlo entero, quedaba anotado, y al conjunto de esas señales se le dice engagement. Ese stream se manda por un sistema de mensajería, y del otro lado una red neuronal lo consume, aprendiendo qué le gusta a cada uno para mostrarle cosas parecidas. En definitiva, el objetivo es comercial.

Ahora la diferencia principal con lo anterior, de la cual se deducen casi todas las demás. En los dos modelos anteriores los mensajes son efímeros. Cambiaba a quién le llegaba cada uno —en el fan-out a todos, en la cola a uno solo—, pero en los dos casos el mensaje se lee y desaparece: son sistemas de transporte, mueven mensajes y no los guardan como una base de datos. Este tercer modelo no. Lo que hay es un log, y el log es persistente: todos los mensajes quedan ahí. Eventualmente habrá que ir limpiándolo, porque el espacio en disco es finito, pero la idea, en teoría, es un log potencialmente perpetuo.

De esa persistencia salen un par de propiedades, y la primera es el orden. Los mensajes de un log están ordenados, son necesariamente FIFO. Enseguida se va a matizar, porque con particiones no todos los mensajes tienen un orden entre sí, pero hay un concepto de orden y es real. Eso habilita algo imposible con una cola: un log de todos los eventos de un usuario, en el orden exacto en que ocurrieron. Sirve para ver cómo evoluciona su comportamiento, y también para los problemas que ya aparecieron en la clase: si un usuario se modifica y después se elimina, el orden de esas dos cosas es justo lo que necesitamos para no dejar datos inconsistentes. Es un log en el sentido más tradicional, el mismo en que la palabra viene apareciendo en toda la materia.

Uno de los textos que recomendamos en la primera clase es de Jay Kreps, el inventor de Kafka, y trata justamente sobre esta idea del log: aquí es donde corresponde releerlo.

{: .nota }
> Jay Kreps es co-creador de Apache Kafka en LinkedIn, junto con Neha Narkhede y Jun Rao, y después cofundador y CEO de Confluent. El texto es «The Log: What every software engineer should know about real-time data's unifying abstraction», publicado en el blog de ingeniería de LinkedIn el 16 de diciembre de 2013 y expandido más tarde en el libro *I ❤️ Logs* (O'Reilly, 2014). La definición con la que abre es exactamente la idea de esta sección: «A log is perhaps the simplest possible storage abstraction. It is an append-only, totally-ordered sequence of records ordered by time».

Si el log es persistente, la segunda propiedad aparece sola: varios consumidores pueden leer el mismo log por lugares distintos, cada uno en su propia posición. Típicamente todos leen del final, buscando lo nuevo, y en ese régimen el sistema se comporta como el fan-out del publisher-subscriber. Pero nada impide otra cosa: como el log es persistente, un consumidor puede empezar a leer desde un mes atrás y reprocesar todo desde entonces. Esa operación se llama replay, y el caso de uso es concreto: se rompió una base de datos y hay que reconstruirla, a veces reprocesando desde el principio todos los mensajes que la fueron construyendo. Los consumidores pueden empezar a leer desde cualquier lado, o rebobinar y hacer replay de lo viejo.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el log y los tres consumidores en offsets distintos — una tira de unas diez celdas, el log, con tres flechas que la apuntan desde abajo en posiciones diferentes, rotuladas C₁, C₂ y C₃; al costado, las anotaciones &quot;los mensajes están ordenados&quot; y &quot;los consumidores pueden empezar a leer desde cualquier lado o REBOBINAR y REPLAY&quot;
    <span class="figura-ref">notas pág. 7 / pizarra pág. 16</span>
  </figcaption>
</figure>

La tercera consecuencia resuelve casi sin esfuerzo el problema de la sección anterior: el fan-out se vuelve trivial. Hay un único log, muchos consumidores se cuelgan de él y cada uno lo consume. No hay nada que multiplicar, porque el mensaje no se destruye al ser leído.

Comparemos los dos caminos frente al problema del principio: muchos servicios que quieren enterarse de las actualizaciones de otro. Con lo que teníamos, el productor le manda el mensaje a SNS, SNS hace el fan-out hacia una cola de SQS por consumidor, y cada uno consume de la suya. Funciona, pero cada consumidor nuevo obliga a armar y conectar otra cola. Con un log, el productor hace una sola cosa: le dice al mundo que sus eventos están en tal topic —así se llaman estos logs en Kafka—, y ahí termina su responsabilidad. Los interesados vienen, se cuelgan del topic y se van enterando. Como consumir no elimina los mensajes, se pueden colgar muchos y todos obtienen lo que les interesa: bastante más potente que las versiones anteriores.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la comparación del fan-out — a la izquierda, con colas: &quot;SERVICIO PRODUCTOR&quot; → óvalo &quot;SNS&quot; → rectángulo &quot;SQS&quot; → &quot;SERVICIO CONSUMIDOR&quot;, con la leyenda &quot;el consumidor quita los mensajes de la cola&quot;; a la derecha, con log: &quot;SERVICIO PRODUCTOR&quot; → una tira de celdas rotulada &quot;TOPIC&quot;, con dos consumidores que apuntan con flechas a celdas distintas del log, y la leyenda &quot;el consumidor empieza a consumir directamente porque no destruye el log&quot;
    <span class="figura-ref">notas pág. 7 / pizarra pág. 16</span>
  </figcaption>
</figure>

Falta matizar «perpetuo», porque en la práctica nadie guarda todo para siempre. Estos sistemas suelen tener un período de retención: quizás después de una semana los mensajes viejos empiezan a borrarse. Lo importante es que la escala es larga —semanas, incluso meses—, justamente para que cualquier consumidor pueda hacer replay de mensajes viejos.

## Particionado del log

Con el modelo conceptual armado, la pregunta de siempre: cómo se escala. Una única máquina con un único log no daría abasto. Y no alcanza con hacerlo tolerante a fallas: con un Raft detrás seguiríamos teniendo un solo log absorbiendo toda la carga. Hay que particionarlo, y de ahí el nombre del modelo: los logs particionados son casi la innovación de Kafka.

La unidad en Kafka es el topic: un log es un topic, y el topic lo identifica. Cada topic está particionado, con una cantidad de particiones que se configura al crearlo. Los topics separan lógicas de negocio distintas: «actualizaciones de usuario», «engagements», cualquier flujo de eventos que tenga sentido tratar aparte.

Del lado del productor la operación es un `send` con tres parámetros: topic, key y payload. El topic es el log al que se escribe; el payload, el mensaje. Y el propósito de la key, a esta altura, es previsible: para shardear, con la técnica que conocemos desde hace muchas clases, `hash(key) % N`, con N la cantidad de particiones del topic. El resultado es la partición a la que va el mensaje.

Lo que se gana eligiendo bien la key es lo interesante, y la regla es que sea representativa del negocio. Si mandamos actualizaciones de un usuario, la key va a ser el user ID. Así todas las cosas del mismo usuario caen en la misma partición y, dentro de ella, quedan ordenadas en el orden real en que ocurrieron. Entre usuarios distintos, en cambio, están desordenadas, porque nada relaciona las posiciones de una partición con las de otra. Esa es la garantía del sistema, con estas palabras exactas: FIFO por partición. Si se quiere consumir en orden, el orden se consume por partición.

Las dos piezas juntas —el módulo y el orden por partición— explican por qué la cantidad de particiones se decide al crear el topic y después es tan caro tocarla. Si se pasa de diez a once particiones, el resto de la división cambia para casi todas las keys: solo alrededor de una de cada once conserva su partición, un 9 %, así que más del 90 % de las claves se muda. Es la misma cuenta del rehashing con módulo de la clase 10, la razón de ser del consistent hashing. Pero aquí el costo no es solo mover datos, y esa es la parte más costosa: como el orden solo vale dentro de cada partición, mudar una clave le rompe el orden a sus mensajes. Los viejos quedan en una partición, los nuevos caen en otra, y nada relaciona las dos posiciones.

Las particiones típicamente están distribuidas en máquinas distintas, los brokers del sistema —el mismo término de toda la clase, aplicado ahora a las máquinas de un clúster de Kafka—. De ahí sale la escalabilidad: un log con mucha carga se particiona en diez, las diez particiones quedan en diez máquinas, y cada una absorbe una décima parte del tráfico. Dentro de cada una, las cosas siguen en orden.

La contrapartida es un punto que suele generar confusión: no hay forma de combinar las particiones y obtener un orden global. No existe el orden total de un topic; siempre es relativo a la partición. Aparece una pregunta natural: si el orden solo vale por partición, cuando uno mira el final del log, la operación justo antes de la última no es necesariamente la que la precede en el tiempo. Exacto. Dentro de cada partición el orden es el real, pero no existe «el log» al consumir, y esta es otra idea clave del diseño: ninguna abstracción permite consumir un log entero como si fuera una única secuencia. Los consumidores tienen noción de la partición; la partición no está abstraída. Cómo se consume muestra que no podía ser de otra manera.

## Consumer groups y coordinador

Producir es simple: logs a los que se les hace append en paralelo. Consumir es donde está toda la complejidad. La biblioteca de Kafka y sus variantes no es una simple biblioteca de RPC, como las de los casos anteriores: tiene bastante lógica, toda al servicio de consumir de muchas particiones a la vez de manera coordinada.

La regla de base es una sola: N particiones son consumidas por un consumidor. Un consumidor puede leer varias particiones, pero nunca puede pasar lo contrario, dos consumidores leyendo la misma partición a la vez, compitiendo por sus mensajes. El paralelismo es por partición, y esa es la unidad del reparto.

La razón se sigue de la propiedad que hace posible todo lo demás: como el consumidor no saca el mensaje del log, dos consumidores sobre la misma partición leerían los mismos mensajes, que se repetirían. Con un Kafka de una sola partición, la idea es tener un solo consumidor. Que cada partición sea leída por exactamente un consumidor es la forma más elemental imaginable de evitar la duplicación.

De ahí la regla práctica de dimensionamiento: conviene que haya más particiones que consumidores. Con una partición y dos consumidores, uno queda ocioso, sin ninguna partición libre que asignarle. Lo ideal es tener muchas particiones y menos consumidores, cada partición leída por exactamente uno.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la figura 11-3 de Kleppmann — &quot;Topic A&quot; con Partition 0 (celdas 1..10) y Partition 1 (1..8); &quot;Topic B&quot; con Partition 0 (1..4), Partition 1 (1..7) y Partition 2 (1..12); dos &quot;Producer client&quot; con flechas de `append` a la punta de las particiones; y un &quot;Consumer group&quot; con dos &quot;Consumer client&quot;, el primero con &quot;offset for B.0 = 4 / offset for B.1 = 5&quot; y el segundo con &quot;offset for B.2 = 9&quot;; anotado a mano debajo, `SEND(TOPIC, KEY, PL)` → `HASH(KEY) % N` ⇒ &quot;FIFO POR PARTICIÓN&quot;
    <span class="figura-ref">pizarra pág. 17</span>
  </figcaption>
</figure>

{: .nota }
> La figura es la 11-3 del capítulo 11, «Stream Processing», en la página 448 de la primera edición de Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017 —el libro que en clase se identifica por el jabalí de la tapa, un *Indian wild boar*—. Su epígrafe es «Producers send messages by appending them to a topic-partition file, and consumers read these files sequentially».

En ese dibujo aparece la terminología que faltaba: al grupo de consumidores que se reparte las particiones de un topic se lo llama consumer group. Conceptualmente, un consumer group es una aplicación: un servicio que quiere enterarse de todas las actualizaciones de usuarios corre muchos consumidores —muchos procesos, muchas máquinas—, y todos forman un consumer group. La biblioteca de Kafka les da la sincronización para repartirse el trabajo sin pisarse.

En el dibujo hay tres particiones y dos consumidores: el primero consume dos y el segundo la tercera. Si apareciera un tercer consumidor, la asignación se redistribuiría y quedaría una partición para cada uno. Lo que nunca puede pasar es que dos del grupo lean la misma partición.

Eso plantea la pregunta importante: ¿quién decide qué consumidor va a qué partición? Hace falta alguna suerte de coordinador, cuya forma fue evolucionando, pero el proceso es siempre el mismo. El consumidor le pide trabajo al coordinador, que tiene las tres particiones anotadas y le contesta, por ejemplo, la uno. Le pide otra, y le da la tres. Le pide otra, y le da la que queda. Si después viene el otro consumidor a pedir, no le da nada, porque ya están todas asignadas.

Hay entonces un subsistema coordinador, y hay que registrar lo que cuesta: se termina la simplicidad. El productor sigue haciendo un append a un archivo, pero el consumidor necesita una lógica grande que distribuya las particiones y las redistribuya cuando el conjunto cambia.

La primera versión se armó con piezas que ya estudiamos. La biblioteca de Kafka usaba ZooKeeper —el de la clase 8— como storage del estado. La lógica del coordinador no vivía en el servidor sino en cada consumidor, y ZooKeeper era donde se coordinaban para ver qué partición estaba libre. Un consumidor obtenía una partición atómicamente creando un nodo efímero, el mecanismo que vimos en esa clase; cuando moría, su nodo efímero desaparecía y la partición quedaba liberada. Los demás se enteraban por las notificaciones asincrónicas de ZooKeeper, los watches, y redistribuían la carga. Los consumidores, además, le mandan checkpoints al coordinador con su progreso, para que la posición desde la cual seguir leyendo no se pierda cuando la partición cambia de dueño.

Hoy el mecanismo es el mismo —los consumidores le piden particiones a un coordinador y el reparto queda en un storage replicado—, pero ya no se usa ZooKeeper: el coordinador está integrado en el propio servicio de Kafka, y lo que reemplazó a ZooKeeper se llama KRaft. Lo que hay que retener es la asimetría: los logs son mucho más simples de lo que uno esperaría —se producen en paralelo y nada más—, pero consumirlos es muchísimo más complicado, y el rebalanceo cuando se muere un nodo no se resuelve con un truco: requiere un subsistema aparte dedicado a distribuir la carga entre los consumidores.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el consumer group y su coordinador — un rectángulo &quot;COORDINADOR&quot; arriba; tres tiras de celdas apiladas a la izquierda, numeradas 1, 2 y 3, que son las particiones; las tiras 1 y 2 conectan con un consumidor C₁ y la tira 3 con un consumidor C₂; del bloque de consumidores sube una flecha al coordinador y otra hacia un cilindro rotulado &quot;ZOOKEEPER&quot;
    <span class="figura-ref">notas pág. 8 / pizarra pág. 18</span>
  </figcaption>
</figure>

## Tolerancia a fallas

Un último tema, tratado a grandes rasgos, casi como contexto. Para dimensionar de dónde viene el sistema: la primera versión de Kafka no tenía tolerancia a fallas.

La que tiene hoy es una especie de primary-backup, partición por partición. Para cada partición, una réplica es el primary y las demás son backups. El primary recibe la escritura, se la manda a los backups, y estos confirman que la tienen. Recién entonces el primary considera el mensaje comiteado y lo empieza a mostrar al resto del mundo; hasta ahí no se sirve a ningún consumidor. Ese umbral tiene nombre: el primary les notifica a los followers el high-watermark, la posición hasta la cual el log está comiteado, y solo lo que queda por debajo es visible.

Lo que funciona ahí es una especie de Raft simplificado, y la simplificación está en el quórum: no hay quórum. Con N réplicas, el primary no le escribe a una mayoría sino a sus N−1 followers, y solo cuando todos confirmaron hace el commit. Ante una falla, la reconciliación se parece a la de Raft: hay una elección de líder —con ZooKeeper en las versiones viejas, con KRaft en las nuevas— y el nuevo líder les fuerza su log a los demás. Pero hay una diferencia que es la parte elegante del diseño. Raft necesita una condición de elegibilidad del líder: no cualquiera tiene todas las entradas comiteadas, y la votación tiene que descartar a los atrasados. Aquí no hace falta: como el commit exigió la confirmación de todos, todas las réplicas tienen por definición todos los mensajes comiteados, y cualquiera puede ser el nuevo líder. Escribirles a todos en lugar de a un quórum se paga en disponibilidad de escritura y se cobra en simplicidad de la elección.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la replicación de una partición en Kafka — cuatro rectángulos &quot;broker 1&quot; a &quot;broker 4&quot;, cada uno con una sección &quot;logs&quot; que contiene cajas `topic1-part1` y/o `topic1-part2` etiquetadas &quot;leader&quot; o &quot;follower&quot;: el broker 1 tiene `topic1-part1` como leader y los brokers 2 y 3 la tienen como follower; el broker 4 tiene `topic1-part2` como leader y los brokers 2 y 3 la tienen como follower; dos &quot;producer&quot; a los costados apuntan a los dos leaders y flechas grises van de cada leader a sus followers; anotado a mano, &quot;PRIMARY&quot; sobre el leader del broker 1 y &quot;BACKUPS&quot; sobre el arco que abarca sus dos followers
    <span class="figura-ref">pizarra pág. 20</span>
  </figcaption>
</figure>

Con eso se cierra el tercer modelo y la clase, que es distinta de las anteriores: probablemente la más práctica de la materia en términos de lo que uno se encuentra en la vida real. El resto del curso es sobre cómo funcionan los sistemas distribuidos por dentro; esta fue sobre primitivas que podemos usar directamente para construir cosas.

Y queda la moraleja, después de haber abierto las tres cajas. Los sistemas de mensajería modernos, con brokers, son un caso de uso muy especial de sistema de storage. Lo único que hacían era guardar mensajes de distintas maneras: en una tabla, en una bolsa shardeada al azar, en un log al que se le hace append. Bases de datos muy especializadas, y mucho más simples que un Postgres. Tienen dos caras, mensajería y storage, y es la segunda la que los explica y la que cierra el recorrido por los sistemas de storage que veníamos haciendo: son bases de datos a las que se les pidió una sola cosa —guardar un mensaje el tiempo justo para poder soltarlo—, y es por haber renunciado a todo lo demás que pueden permitirse ser tan simples.
