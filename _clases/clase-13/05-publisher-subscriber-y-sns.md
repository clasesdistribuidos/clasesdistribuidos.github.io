---
title: "5. Publisher-subscriber y SNS"
parent: "Clase 13 — Sistemas de mensajería"
nav_order: 5
---

# 5. Publisher-subscriber y SNS
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


El segundo ejemplo tiene dos capas: cómo funciona SNS, el servicio de publisher-subscriber de Amazon, y cómo funciona por dentro. Y lo que hay por dentro, en el fondo, es SQS: un sistema de Amazon implementado sobre otro.

Antes, una advertencia que cambia el estatuto de lo que sigue: Amazon nunca publicó papers ni documentación sobre cómo funcionan SNS ni SQS. Lo que hay es lo que se sabe de cómo funcionaban en algún momento, así que la implementación que vamos a reconstruir es una hipótesis plausible y no documentación; quizás hoy el diseño sea completamente distinto. Eso distingue este tramo del resto de la materia, donde estudiamos papers. El valor del ejercicio no está en su fidelidad al original sino en que todas las piezas que van a aparecer ya las conocemos.

## SNS y fan-out

Comencemos por la interfaz externa. SNS es el servicio de publisher-subscriber de AWS, el segundo modelo de integración. Su dibujo queda casi idéntico al de una cola: productores a la izquierda, una caja en el medio, consumidores a la derecha. Por eso conviene dibujar esa caja como un rectángulo y no como el cilindro de la cola: SNS no es conceptualmente una cola, y lo que cambia de un dibujo al otro no es la forma sino la explicación.

Los publishers hacen lo mismo que antes: le mandan sus mensajes a SNS. La diferencia está del otro lado: el mismo mensaje se reparte a todos. Si el productor emite m₁, le llega m₁ al primer consumidor, al segundo y al tercero. La semántica es completamente diferente: en la cola los consumidores competían y el que tomaba el mensaje se lo llevaba; aquí no compite nadie, se enteran todos.

La operación que hace eso es la que hay que retener de esta sección: fan-out. *Fan*, en inglés, es ventilador pero también abanico, y la traducción que sirve es la segunda: el mensaje se abre en abanico hacia muchos consumidores. Es la característica principal del publisher-subscriber y resuelve un problema frecuentísimo: multiplicar un mensaje hacia varios destinos.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/fan-out-de-sns.png' | relative_url }}" alt="SNS repartiendo el mismo mensaje a tres consumidores">
  <figcaption>
    <span class="figura-label">Figura</span>
    el fan-out de SNS — dos cuadrados P a la izquierda con flechas hacia un cuadrado &quot;SNS&quot; (cuadrado y no cilindro, deliberadamente, para que no parezca una cola); del SNS salen tres flechas verdes curvas hacia tres cuadrados C apilados, y cada mensaje viaja como un cuadrado verde pequeño rotulado &quot;m₁&quot;; una llave a la derecha de los tres C dice &quot;HETEROGÉNEO&quot; y debajo una llave verde rotulada &quot;FAN-OUT&quot;
    <span class="figura-ref">notas pág. 4 / pizarra pág. 10</span>
  </figcaption>
</figure>

Eso cierra la pregunta que quedó abierta. Una cola no sirve cuando varios sistemas tienen lógica de negocio distinta —la baja del usuario que todos los microservicios tienen que procesar—, porque el primero que consume el mensaje se lo lleva. Ese es el caso de los consumidores heterogéneos: sistemas, departamentos, microservicios o incluso compañías distintas. Si todos se tienen que enterar del mismo mensaje, hace falta algo con fan-out incorporado, y esa es la razón de ser de SNS.

Hay una segunda diferencia, de mecánica: SNS hace push. En SQS el consumidor hacía `receive`, solicitándole activamente a la cola que le entregara algo. Aquí el sentido se invierte y es el servicio el que nos avisa. En el caso más fácil de entender —no el más usado, pero el que deja ver el mecanismo— cada consumidor tiene un endpoint, un RPC, y SNS lo llama para inyectarle los mensajes.

Eso agrega complejidad, y los problemas del push son todos variaciones de uno solo: el receptor no disponible. Un consumidor se registra para escuchar las notificaciones de usuarios eliminados y le pasa a SNS la URL a la cual llamarlo, algo del estilo de un webhook. Supongamos que la URL vino con un error de sintaxis, o que no hay nada atrás. SNS llama y falla, vuelve a intentar y falla. La opción típica es retry N veces y después descartar: a los tres o cuatro intentos lo da por fallado. No es la forma más canónica de usar el servicio —al final de la sección vamos a ver cuál es—, pero empecemos por la obvia.

Y SNS tiene una particularidad que SQS no: contempla dos casos de uso bien distintos. Uno es app-to-app: el sistema de usuarios le notifica al de liquidación de haberes que se eliminó un usuario. El otro es app-to-person: el receptor puede ser un email, un SMS o una push notification, el aviso que aparece en la pantalla del teléfono. Un fan-out puede mezclar máquinas y personas. Es un caso de uso algo ajeno a lo que nos interesa, pero viene de fábrica, y más adelante nos va a explicar una decisión de diseño.

La API es igual de austera que la de SQS. No tiene `receive`, porque el sentido es push. Tiene un `subscribe`, que se invoca una vez al conectarse indicando el tipo de conexión y a dónde mandar los mensajes. Y del lado del productor, el `publish`, trivial: a qué tópico —o canal— y qué mensaje. Eso hace el fan-out hacia todos los suscriptores previos.

```python
sns.subscribe(TopicArn=arn, Protocol="sqs", Endpoint=cola_arn)
# Protocol: sqs, lambda, http, email, sms...

sns.publish(TopicArn=arn, Message="hola")
# fan-out a todos los suscriptores
```

Dos detalles de ese código. El primero es el `Protocol`, donde asoman los dos casos de uso: `sqs`, `lambda` y `http` son máquinas; `email` y `sms`, personas. El segundo es el valor elegido: `Protocol="sqs"` conecta SNS con una cola de SQS, un patrón muy común y exactamente donde termina esta sección.

Queda un detalle que organiza la última parte de la clase. Si nos suscribimos ahora, recibimos los mensajes a partir de este momento, no los publicados antes. Parece trivial, pero obtener mensajes del pasado es un caso de uso genuinamente necesario que SNS no ofrece: es lo que vamos a ver con Kafka, y una de las razones de ser del tercer modelo.

## Arquitectura interna de SNS

Ahora examinemos el sistema por dentro: si estuviéramos en Amazon y hubiera que implementar SNS de cero, ¿cómo se haría con lo que ya sabemos? Lo notable es que la respuesta no está lejos de la implementación real.

Sigamos un publish. Lo primero es un frontend, como en casi cualquiera de estos sistemas. Y alrededor de todo lo que viene hay que dibujar una línea grande: la frontera de SNS. De afuera SNS es una caja abstracta; vamos a abrirla.

Adentro hay, primero, una cola interna de mensajes, y esa cola es de SQS. Es lo más llamativo del diseño: Amazon usa uno de sus sistemas como primitiva para construir el otro. El mensaje que el frontend deposita ahí lleva un tópico y el mensaje propiamente dicho.

Del otro lado de esa cola hay una flota. Antes eran workers transcodificadores; aquí son notifiers. El patrón es el mismo —una cola con consumidores homogéneos compitiendo, como balanceador de carga—, y lo interesante es que ahora lo usamos para implementar un fan-out. La pieza es la misma; el efecto que construimos con ella es el opuesto.

Falta la pieza que dice a quiénes notificar: una base de datos de suscripciones, que no tiene por qué ser exótica —un Postgres alcanza—. El camino del `subscribe` es el más simple: llega a un frontend —típicamente el mismo— que agrega un registro en esa base. Del lado del publish, cuando un notifier toma un mensaje de la cola interna, hace un fetch de las suscripciones de ese tópico, obtiene la lista de destinatarios y hace el fan-out: al suscriptor uno, al dos, al tres. Hasta ahí llega su trabajo y la frontera del sistema: los suscriptores quedan afuera de la línea.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/arquitectura-interna-de-sns.png' | relative_url }}" alt="Frontend, cola SQS, notifier workers y base de suscripciones">
  <figcaption>
    <span class="figura-label">Figura</span>
    la arquitectura interna de SNS — todo dentro de un recuadro punteado verde que marca la frontera del servicio: &quot;PUBLISH&quot; → FRONTEND → cilindro &quot;SQS&quot; → una pila de rectángulos &quot;NOTIFIER WORKERS&quot; → tres cuadrados S₁ / S₂ / S₃ fuera del recuadro, con &quot;SYNC&quot; sobre las flechas de salida; del frontend baja una flecha punteada a un icono de documento rotulado &quot;TOPIC / MENSAJE&quot;; de los notifier workers sale un lazo hacia un segundo cilindro SQS rotulado &quot;LENTOS / RETRY&quot; que vuelve a entrar a los workers, y baja una flecha rotulada &quot;FETCH SUBSCRIPTIONS&quot; a un cilindro de base de datos &quot;SUBSCRIPCIONES&quot;; abajo a la izquierda, un camino aparte: &quot;SUBSCRIBE&quot; → FRONTEND → el mismo cilindro de SUBSCRIPCIONES
    <span class="figura-ref">notas pág. 5 / pizarra pág. 11</span>
  </figcaption>
</figure>

Hay una suposición en ese diseño que lo hace funcionar: que un notifier tiene capacidad para mandarle el mensaje a todos los suscriptores. Si la cantidad fuera enorme habría que pensar otra cosa; aquí pensamos en del orden de cien suscriptores como máximo, y para eso un único worker alcanza.

El ejercicio, más allá de si acertamos en los detalles, sirve para desmitificar: dentro de la caja negra de SNS hay un sistema distribuido armado con piezas que ya estudiamos —un frontend, una cola, una flota de workers y una base de datos—. El mismo ejercicio nos queda pendiente con SQS, y al abrir esa caja va a aparecer la explicación del `ReceiptHandle`.

## Suscriptores lentos y fan-out + buffer

Quedan dos temas, que son el mismo problema visto desde dos distancias. El primero: ¿qué hacemos si uno de los suscriptores está caído o no responde y los otros sí funcionaron? El notifier llamó a S₂ y a S₃ sin problema, y S₁ no contesta. Intentar un par de veces es lo mínimo, pero el worker no puede quedarse bloqueado: tiene que seguir con el próximo mensaje.

La primera opción es volver a encolar. El notifier manda el mensaje de vuelta a la cola interna, anotando que quedó pendiente ese suscriptor; otro notifier lo toma más tarde, y se forma una especie de loop. Podría funcionar y sería un buen diseño. El problema es que si los suscriptores caídos o lentos empiezan a fallar en cantidad, llenan la cola de reintentos: los mensajes lentos quedan mezclados con los rápidos y se ralentiza todo, incluidos aquellos cuyos destinatarios funcionaban perfectamente.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/volver-a-encolar.jpg' | relative_url }}" alt="Una cola con mensajes rápidos y lentos mezclados">
  <figcaption>
    <span class="figura-label">Figura</span>
    opción 1, volver a encolar — un cilindro horizontal con cuatro puntos dentro alternando verde y rojo, los mensajes rápidos y lentos mezclados en la misma cola
    <span class="figura-ref">notas pág. 5</span>
  </figcaption>
</figure>

La segunda opción es más ingeniosa: otra cola al lado, de lentos o de retries. Si hay un problema con un suscriptor, el mensaje va ahí, y de esa cola también se consume —quizás con un subconjunto de los workers— hasta que se resuelve. La cola principal, la rápida, que asume que todo funciona, no se ve perjudicada: son colas de distintas velocidades. Es un diseño posible, y con la misma honestidad hay que decir que podría funcionar o no.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/cola-de-retry.jpg' | relative_url }}" alt="Una cola principal y una cola de retry">
  <figcaption>
    <span class="figura-label">Figura</span>
    opción 2, cola dedicada de retry — dos cilindros horizontales lado a lado, el izquierdo con tres puntos verdes rotulado &quot;COLA PRINCIPAL&quot;, el derecho con tres puntos rojos rotulado &quot;COLA RETRY&quot;
    <span class="figura-ref">notas pág. 5</span>
  </figcaption>
</figure>

El segundo tema es el mismo problema visto de más lejos. Si en la punta de una de esas flechas hay directamente una aplicación nuestra, es muy probable que falle, y por eso rara vez se conecta así. La llamada es sincrónica, así que el receptor tiene que estar disponible en el momento exacto en que SNS lo llama. Si no está, SNS reintenta, quizás lo pasa a la cola de lentos, pero si al final no está disponible —la lógica trata unas tres veces— descarta el mensaje.

Para evitarlo hay un patrón —ahora es un patrón y no un sistema— que se suele llamar fan-out + buffer: no poner nuestra aplicación en la punta de la flecha sino un buffer delante. El productor hace su `publish`, SNS hace el fan-out como siempre, pero cada flecha desemboca en una cola de SQS y cada suscriptor consume de su propia cola. SQS está diseñado para alta disponibilidad, así que los mensajes se acumulan ahí sin perderse y el suscriptor los toma cuando puede. El desacople en tiempo del principio de la clase reaparece justo donde el push lo había perdido.

Y de paso se resuelve otro problema. Si un suscriptor no tiene un solo consumidor sino varios que quieren repartirse la carga —el caso más común—, la cola de SQS en el medio encaja perfectamente, porque para eso está: es un balanceador de carga. Fan-out hacia afuera, balanceo de carga hacia dentro de cada suscriptor: los dos primeros modelos combinados, uno detrás del otro.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/fan-out-mas-buffer.png' | relative_url }}" alt="SNS con una cola SQS delante de cada suscriptor">
  <figcaption>
    <span class="figura-label">Figura</span>
    el patrón fan-out + buffer — P --&quot;PUBLISH&quot;--&gt; SNS (rectángulo) → tres flechas en abanico, cada una a un cilindro &quot;SQS&quot; y de ahí a un cuadrado S₁ / S₂ / S₃
    <span class="figura-ref">notas pág. 5 / pizarra pág. 11</span>
  </figcaption>
</figure>

Este es el patrón básico con el que se combinan los dos servicios de Amazon. Y el orden en que aparecieron no es el que uno esperaría de dos piezas pensadas para encajar: la cola llegó primero, por varios años. SQS es uno de los tres servicios con los que nació AWS, y SNS apareció casi cuatro años después, cuando la cola ya era una pieza establecida. El pub/sub, en el catálogo de Amazon, vino después de la cola, igual que en la historia de los paradigmas que recorrimos al principio.

{: .nota }
> Las fechas. Amazon SQS estuvo disponible de forma general el **13 de julio de 2006**, junto con EC2 y S3, y su beta pública es todavía anterior —de noviembre de 2004—, lo que lo vuelve el primer servicio de AWS en llegar a manos de usuarios, antes que S3. La fuente es Amazon: en la retrospectiva por los veinte años del servicio escribe que «el 13 de julio de 2006 lanzamos Amazon Simple Queue Service como uno de los tres primeros servicios disponibles para los clientes, junto con Amazon EC2 y Amazon S3». Amazon SNS se lanzó, en beta, el **7 de abril de 2010**, según el comunicado de prensa de ese día. Circulan también fechas del 11 de julio de 2006 para la disponibilidad general de SQS; aquí se toma la que da Amazon.

Lo notable es que el buffer queda afuera de SNS, y eso fue una decisión de diseño, no una omisión. Google Pub/Sub lo hace al revés: implementa el patrón directamente, con la cola dentro de cada suscripción, así que uno ya tiene su buffer sin armarlo. Todo el asunto es hasta dónde llega la línea punteada de la frontera: SNS podría haber incluido la cola, y Amazon decidió dejarla del lado del usuario. Probablemente por la curiosidad de antes: como SNS también manda emails, SMS y push notifications, quisieron dar la versatilidad de que cada uno elija con qué se conecta. Google Pub/Sub, en cambio, está pensado para mensajería app-to-app, y a un sistema que solo le habla a otros sistemas le resulta natural integrar la cola, porque no hay receptor que no pueda tener una.

---
