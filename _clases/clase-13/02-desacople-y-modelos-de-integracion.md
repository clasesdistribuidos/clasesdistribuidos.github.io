---
title: "2. Desacople y modelos de integración"
parent: "Clase 13 — Sistemas de mensajería"
nav_order: 2
---

# 2. Desacople y modelos de integración
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Con el ejemplo del NASDAQ ya tenemos la intuición de para qué poner algo en el medio. Antes de clasificar los sistemas de mensajería conviene aislar la idea que todos comparten: la comunicación indirecta, contrapuesta a la comunicación directa por RPC que venimos usando en toda la materia. El mecanismo por el cual se consigue tiene nombre: desacople, del inglés *decoupling*. Cuando uno llama a otro sistema por RPC, los dos quedan muy acoplados: aunque corran en máquinas distintas, hay una invocación directa de uno sobre el otro. Con un sistema de mensajería buscamos aumentar esa separación, y hay tres tipos concretos de desacople que vamos a lograr.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    los tres desacoples — figura 2 de Eugster et al., tres paneles rotulados &quot;Space decoupling&quot;, &quot;Time decoupling&quot; y &quot;Synchronization decoupling&quot;, cada uno con Publisher → Event Service (Notify()) → Subscriber (Notify()); en el panel del espacio, un arco curvo del Publisher directo al Subscriber, que es el camino que el desacople evita, y &quot;SNS&quot; anotado debajo del Event Service
    <span class="figura-ref">pizarra pág. 3</span>
  </figcaption>
</figure>

El primero es el desacople *en espacio*, el que ya vimos en el ejemplo: el publisher no necesita conocer a todos los destinatarios. Uno le manda el mensaje a un *tópico* —así suelen llamarse estos canales— y es el sistema el que conoce a los destinatarios y se lo hace llegar a cada uno. Eugster y sus coautores le ponen, metafóricamente, ese nombre espacial.

{: .nota }
> Los tres desacoples y la figura vienen de Patrick Th. Eugster, Pascal A. Felber, Rachid Guerraoui y Anne-Marie Kermarrec, «The Many Faces of Publish/Subscribe», ACM Computing Surveys, vol. 35, n.º 2, junio de 2003, pp. 114-131. Los tres nombres son literales del paper —space, time y synchronization decoupling— y el epígrafe de la figura 2 es «Space, time, and synchronization decoupling with the publish/subscribe paradigm». Vale la pena mirar también su Table 1, que cruza esas tres dimensiones contra ocho paradigmas de interacción —message passing, RPC/RMI, RPC asincrónico, futures, notifications, tuple spaces, message queuing y publish/subscribe—: el único que consigue las tres es publish/subscribe.

Ese mismo desacople tiene una segunda lectura, organizacional: el equipo que desarrolla el publisher no necesita conocer a todos los equipos que consumen sus mensajes. Si el publisher tuviera que mandarle un RPC directo a cada consumidor, cada nuevo interesado tendría que venir a hablar con nosotros, y habría que mirar el calendario del proyecto para ver cuándo se programa esa nueva llamada, y así con cada uno. Los sistemas de mensajería desacoplan exactamente eso: publicamos el mensaje en el sistema de mensajería, y este se lo distribuye a todos los suscriptos. El principal ejemplo que vamos a ver es SNS, de Amazon.

El segundo es el desacople *en tiempo*: el receptor no necesita estar activo cuando se emite el mensaje. Esto es importantísimo, y se aprecia por contraste. Con un RPC uno hace un par de retries, pero si el otro servicio está caído, lo único que queda es un error. Los sistemas de mensajería actuales suelen ser persistentes: el mensaje queda guardado en el sistema, y cuando el receptor se vuelve a conectar, recién ahí lo recibe.

Ese desacople tiene un problema evidente, que suele pasarse por alto al adoptar estos sistemas: si algo falla, también falla desacopladamente en el tiempo. Con un RPC, el servicio que lo recibe valida y devuelve el error en el momento. Con un sistema de mensajería, el intermediario guarda el mensaje en un buffer y el receptor falla después; de esa falla nos vamos a enterar de otra forma y en otro momento: asincrónicamente.

El tercero, bastante relacionado, es el desacople *en sincronicidad*. Los RPC suelen ser llamadas sincrónicas —gRPC tiene opciones para que no sea así, pero es el caso habitual—: uno manda el mensaje y le llega la respuesta; casi es la definición clásica de RPC. Aquí no hace falta recibir la respuesta en el momento, y esa es otra razón para recurrir a estos sistemas.

## Modelos de integración

A partir de estos desacoples podemos preguntarnos qué semánticas se pueden construir sobre un intermediario. Los vamos a llamar modelos de integración básicos, y son tres. El primero es *producer-consumer*, la variación distribuida de algo que ya conocemos de otras materias; vamos a empezar por él. El segundo es *publisher-subscriber*, el del ejemplo del NASDAQ. Y al tercero lo llamamos *event streaming*, el que menos tiene un nombre establecido.

Estos tres modelos se usan muchísimo, y es muy probable que tengamos contacto con ellos en cuanto trabajemos en una empresa con varios equipos, porque son los mecanismos con los que esos equipos se comunican. Ya conocemos uno, el RPC, la versión sincrónica: mi equipo quiere datos de otro, lo llamo por gRPC o REST. Cuando uno quiere invertir ese sentido —que sea el otro equipo el que avise de los cambios—, la solución cae necesariamente en una de estas tres categorías, usando alguno de los productos que ya existen.

Vamos a ver un ejemplo de cada una: SQS para producer-consumer, SNS para publisher-subscriber y Kafka para event streaming. Los dos primeros tienen menos difusión porque son bastante más antiguos, y Kafka es más conocido, pero los tres son importantes.

Adelantemos la forma de cada uno. En producer-consumer, un productor manda mensajes a una *cola de mensajes* y del otro lado muchos consumidores compiten por obtenerlos. En el segundo, el productor le manda el mensaje a un sistema que se lo distribuye a mucha gente, así que el mensaje se multiplica, a diferencia del primer caso. Y en el tercero, el productor escribe en un log, en el sentido que ya conocemos, y distintos consumidores se conectan y lo van leyendo en orden. Son tres variaciones de mensajería asincrónica.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    los tres modelos de integración numerados — ① una P con flechas a un cilindro y del cilindro varios círculos alrededor (la cola con consumidores compitiendo); ② una P → un cuadrado → tres círculos en abanico (el fan-out); ③ una P → una tira de celdas, con dos círculos abajo que apuntan con flechas a celdas distintas (los consumidores con su offset)
    <span class="figura-ref">pizarra pág. 3</span>
  </figcaption>
</figure>

## Producer-consumer

Empecemos por el que quizás sea el más práctico. En la bibliografía también se lo llama *point-to-point*; los dos nombres son indistintos. Hay un productor, una cola —el término típico es *cola de mensajes*— y un consumidor del otro lado.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    producer-consumer — PRODUCTOR --&quot;PUSH&quot;--&gt; cilindro horizontal (la cola) --&quot;RECEIVE&quot;--&gt; CONSUMIDOR, con &quot;RPC&quot; rotulado sobre las dos flechas; debajo del cilindro, una llave rotulada &quot;COLA DE MENSAJES&quot;, y del extremo del cilindro una flecha hacia la llave con las tres variantes de RECEIVE
    <span class="figura-ref">notas pág. 2 / pizarra pág. 4</span>
  </figcaption>
</figure>

No debería resultarnos extraño: el TP de sistemas operativos con pipes tiene exactamente esta forma, solo que las tres piezas viven en la misma máquina. Lo interesante aparece cuando hay muchos productores y muchos consumidores, y a eso vamos a llegar.

La característica principal es que el mensaje se borra al ser consumido. Parece obvio, pero no siempre es así: en Kafka cada consumidor consume un mensaje y el mensaje sigue ahí. En una cola, cuando un consumidor se lleva el mensaje, otro ya no lo encuentra.

Sobre el orden: la cola no es necesariamente FIFO, aunque el dibujo lo sugiera. Algunos sistemas garantizan el orden; en otros hay más bien una gran bolsa de mensajes que trata de entregar lo más o menos reciente, sin comprometerse con la secuencia exacta.

Y hay un tema escondido en el dibujo. Si esto es mensajería asincrónica, ¿qué son las dos flechas, del productor a la cola y del consumidor a la cola? Son la misma flecha de siempre: un RPC para mandarle mensajes a la cola y otro para consumirlos, cuando el consumidor llama a la cola. Es habitual abstraerse al punto de creer que se reemplazó el RPC por «mandar un mensaje a una cola». Pero la cola, que dibujamos como una sola figura, es típicamente un sistema distribuido, y para hablarle hay que mandarle un RPC. Por eso le dedicamos tanta atención al RPC: es la primitiva sobre la cual se construye todo lo demás, incluida la mensajería asincrónica.

Del lado del productor casi siempre hay un estilo push, con el productor mandando mensajes a la cola. Del lado del consumidor hay alternativas. La operación es un `receive`, que puede ser bloqueante —el consumidor se queda bloqueado hasta que aparezca un mensaje— o de polling —si no hay nada, el consumidor vuelve a preguntar cada treinta segundos, cada diez, cada uno—. Blocking o non-blocking, siendo el non-blocking el polling. El SQS clásico es un ejemplo de la segunda variante.

Y el sentido de la comunicación puede ir, según el diseño, en una dirección o en la otra. Puede ser push: la cola le empuja los mensajes al consumidor. Puede ser notify: la cola le avisa que hay un mensaje nuevo y el consumidor viene a leerlo. O el consumidor viene y los lee sin que nadie le avise, que es el caso de SQS.

---
