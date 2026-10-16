---
title: "3. Mensajería directa, message brokers y SQS"
parent: "Clase 13 — Sistemas de mensajería"
nav_order: 3
---

# 3. Mensajería directa, message brokers y SQS
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Mensajería directa y ZeroMQ

El cilindro del medio es abstracto, y a la hora de construirlo hay dos caminos bien distintos para que el código se comporte como si esa cola estuviera ahí.

El primero es que la cola no exista en ninguna parte. El productor y todos los consumidores la arman entre ellos, de manera abstracta. En la realidad el productor se comunica directamente con cada consumidor, sin ningún servicio en el medio; lo que hay es una biblioteca, una capa de abstracción que le hace creer a nuestro código que en el medio hay un canal, una cola de mensajes. El dibujo del cilindro sigue siendo fiel a lo que ve el programador, aunque no a lo que ocurre en la red. A este esquema lo llamamos mensajería directa.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/mensajeria-directa.jpg' | relative_url }}" alt="Un productor con su biblioteca conectado a tres consumidores">
  <figcaption>
    <span class="figura-label">Figura</span>
    mensajería directa — un cuadrado P a la izquierda con una llave que le apunta rotulada &quot;BIBLIOTECA&quot;, y de un punto sobre su borde derecho tres flechas hacia tres cuadrados C dispuestos en abanico
    <span class="figura-ref">notas pág. 3 / pizarra pág. 4</span>
  </figcaption>
</figure>

El ejemplo típico es ZeroMQ, que también se escribe ØMQ. Sin un servicio aparte para la cola, emula el comportamiento de tener uno. Sus autores tomaron la API de sockets, que es siempre punto a punto —uno abre un socket contra otra máquina y nada más—, y a partir de ese diseño construyeron un sistema de mensajería bastante más complicado.

Vale la pena mirar un ejemplo mínimo, no por el código sino para ver esa herencia. Del lado del consumidor:

```python
# consumidor.py
import zmq

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5558")

while True:
    print(socket.recv_string())
```

Y del lado del productor:

```python
# productor.py
import zmq, time, sys

nombre = sys.argv[1]
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect("tcp://10.0.0.31:5558")
socket.connect("tcp://10.0.0.32:5558")
socket.connect("tcp://10.0.0.33:5558")

for i in range(10):
    socket.send_string(f"{nombre}: tarea {i}")
    time.sleep(0.3)
```

Lo primero que salta a la vista es el nombre del objeto: se llama `socket`, pero no es un socket, sino que representa la cola, la caja del medio del dibujo. La diferencia con un socket de verdad está en las tres líneas de `connect`: ese único objeto está conectado a muchos lugares a la vez, un consumidor por línea. Después el productor simplemente le manda mensajes al objeto, y cada consumidor levanta su propio `socket`, que se queda escuchando.

Aparece la pregunta que corresponde hacerse frente a cualquiera de estos sistemas: cuando el productor hace un `send_string`, ¿el mensaje lo reciben los tres consumidores o uno solo? La forma del código no lo dice, porque la llamada es idéntica en los dos casos. La respuesta está en el tipo de socket elegido: con un `PUSH` de un lado y un `PULL` del otro, lo recibe uno solo.

{: .nota }
> La documentación oficial de `zmq_socket` confirma esa lectura. `ZMQ_PUSH` declara como estrategia de routing de salida *round-robin*: los mensajes se reparten entre los peers conectados y cada mensaje va a uno solo. La frase del manual —«messages are round-robined to all connected downstream nodes»— se lee mal si se pasa rápido por ella, porque el «all» describe a quiénes alcanza el reparto a lo largo del tiempo y no a cuántos destinatarios llega cada mensaje. Del otro lado, `ZMQ_PULL` recibe de todos los productores conectados con encolado equitativo, *fair-queued*. El patrón que sí hace fan-out es PUB/SUB: de `ZMQ_PUB` el manual dice que «messages sent are distributed in a fan out fashion to all connected peers». La elección del tipo de socket en ZeroMQ es, entonces, el mismo par que estructura toda esta clase: PUSH/PULL es reparto y PUB/SUB es multiplicación.

## Message brokers

La otra forma de implementar la cola, la más interesante hoy, es un sistema dedicado: los nodos no se conectan entre sí, sino que existe un sistema aparte que es el sistema de mensajería. Las dos versiones son distribuidas, pero esta segunda es la que vamos a estudiar, porque es la que uno se encuentra al resolver un problema real.

A esos intermediarios se los llama brokers, o *message brokers*: es el nombre técnico de la caja del medio. Uno o varios productores le mandan las cosas al broker, y el broker se las manda a los que las quieren recibir, a todos o a uno solo según el modelo de integración.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/message-broker.png' | relative_url }}" alt="Dos productores y tres consumidores alrededor de un broker">
  <figcaption>
    <span class="figura-label">Figura</span>
    message broker — dos cuadrados P a la izquierda con flechas convergentes hacia un cuadrado central B, y de B salen tres flechas hacia tres cuadrados C apilados verticalmente
    <span class="figura-ref">notas pág. 3 / pizarra pág. 6</span>
  </figcaption>
</figure>

Los nombres de la familia son pocos. SQS y SNS son los dos de Amazon, nuestros ejemplos de los dos primeros modelos. Google Cloud tiene Pub/Sub. Esos tres son servicios de nube: se usan, no se instalan. Para levantar un sistema propio, los dos nombres clásicos son RabbitMQ y ActiveMQ; la sigla «MQ» suele marcar un sistema de mensajería dedicado que hay que instalar y operar por cuenta propia.

¿Qué son esencialmente todos estos sistemas? Un tipo de base de datos, con particularidades bien marcadas. La primera es que generalmente borran los mensajes al entregarlos, lo contrario de aquello para lo que está pensada una base de datos: aquí los datos se guardan para poder soltarlos. La segunda es que no son relacionales; si «base de datos» arrastra esa asociación, conviene desarmarla: el término más genérico es sistemas de storage. La tercera es que los mensajes son efímeros, al menos en los dos primeros modelos: duran muy poco y en cuanto se entregan —al consumidor que los tomó, o a todos los que los querían— se eliminan. La cuarta es que no tienen índices, o no sofisticados, porque nadie consulta esos datos por otro criterio que sacar lo que haya. Y la última se sigue de las anteriores: no están diseñados para gran volumen de storage, sino para tener pocos mensajes almacenados, como un buffer intermedio donde la vida de cada mensaje es corta.

Clásicamente esto era software que había que instalar. Hoy todos los proveedores de nube ofrecen un servicio que hace básicamente lo mismo, que en la terminología vieja sería un message-oriented middleware, aunque ya nadie lo llame así y aunque se consuma como servicio de nube y no como proceso en un servidor propio.

¿Estos sistemas imponen un modelo o dejan elegir? Con RabbitMQ o ActiveMQ, ¿podemos decidir si mandarle lo mismo a todos los consumidores —estilo publisher-subscriber— o si el primero que toma el mensaje se lo queda —estilo producer-consumer—? Lo razonable es esperar que esos dos tengan la versatilidad para ambos modos según cómo se los configure. De ZeroMQ podemos afirmarlo: se llama MQ pero es distinto del resto, porque es una biblioteca que va dentro del programa y no un sistema aparte, y según cómo se lo configure hace una cosa u otra. Amazon eligió el camino opuesto: dos sistemas separados, SQS por un lado y SNS por el otro. El de Google está más mezclado y se puede usar de una forma o de la otra.

## API de SQS

Vamos al caso de estudio, SQS, y a su API: los RPCs que habría que usar en la vida real. La primera S es de *Simple Queue Service*, y el nombre no exagera.

Tiene tres operaciones: mandar, recibir y borrar mensajes —y cada operación, endpoint o API es, hay que imaginarlo, un RPC—. Eso es todo. La única que suena rara es el borrado, porque en otros sistemas no se llama `delete` sino `acknowledge`, que describe mejor lo que uno hace; en SQS la inventaron así.

Los parámetros tampoco tienen misterio. Para mandar hay que indicar lo que Amazon llama la *URL de la cola*, que en realidad es su nombre: un usuario puede crear muchas colas para distintos propósitos, y ese identificador dice a cuál se manda el mensaje. Cumple el papel del nombre de una variable. Para recibir, lo mismo: se pasa el nombre de la cola y, si hay mensajes, el servicio los devuelve —en general un grupo y no uno solo—. Si no hay, en el caso más básico devuelve cero y hay que volver a preguntar unos treinta segundos después. Se puede configurar para que la llamada quede bloqueada esperando y no haya que estar preguntando «¿hay mensaje?» constantemente, pero vamos a mirar la versión más simple, para enfatizar lo poco que hay que saber.

Al enviarse, un mensaje trae un ID y un MD5 —un hash del cuerpo—, ninguno muy importante. Al recibirlo vienen tres campos: el ID, el body y un `ReceiptHandle`. Este último es el único que merece atención, y no porque haga falta para el modelo conceptual sino al revés: es una consecuencia de cómo está implementado SQS por dentro. Es un valor que el servicio devuelve al entregar el mensaje y que hay que pasarle de vuelta al borrarlo. No hay ninguna razón evidente para que exista: con el ID del mensaje y el nombre de la cola parecería alcanzar para señalar cuál eliminar. Queda anotado como un misterio; la respuesta aparece cuando veamos cómo se construye un broker desde cero, y se explica por cómo SQS reparte los mensajes entre sus máquinas.

```python
sqs.send_message(QueueUrl=url, MessageBody="tarea 1")
# devuelve: MessageId, MD5OfMessageBody

sqs.receive_message(QueueUrl=url)
# cada mensaje trae: MessageId, ReceiptHandle, Body

sqs.delete_message(QueueUrl=url, ReceiptHandle=recibo)
# recibo = ReceiptHandle devuelto por receive_message
```

## Visibility timeout

Veamos cómo se espera que se use el modelo: parece obvio, pero de cerca surgen un par de preguntas.

Del lado derecho de la cola hay muchos consumidores haciendo `receive` constantemente, cada treinta segundos o bloqueados, según la configuración. Todos compiten por los mensajes. Cuando un productor manda un mensaje, el servicio se lo entrega al consumidor que hace su `receive` y no a los demás. Eso sirve para que los consumidores no procesen varias veces el mismo mensaje, y es exactamente lo que diferencia a este modelo de los otros dos. Lo que se consigue con esa exclusividad es un efecto de balanceo de carga: los mensajes se reparten entre los consumidores disponibles sin que nadie decida cuál va a cuál.

{: .nota }
> El encuadre como balanceo de carga es de Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017 —el libro que en clase se identifica por el jabalí de la tapa—, en la subsección «Multiple consumers» (pp. 444-445). Ahí nombra los dos patrones y los contrasta en su figura 11-1: *load balancing*, donde «each message is delivered to *one* of the consumers», y *fan-out*, donde «each message is delivered to *all* of the consumers». Es exactamente la distinción entre el modelo de esta sección y el de publisher-subscriber.

Ahora la pregunta que aparece de inmediato, el gran tema de todo el curso: ¿qué pasa si un consumidor toma un mensaje, lo empieza a procesar y falla? No queremos que el mensaje, por haber sido consumido, haya desaparecido de la cola sin que nadie lo procese. Los sistemas lo resuelven con variaciones de la misma idea, y la de SQS se llama *visibility timeout*.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-13/visibility-timeout.png' | relative_url }}" alt="La cola con un mensaje tomado y su visibility timer">
  <figcaption>
    <span class="figura-label">Figura</span>
    el visibility timeout — dos cuadrados P a la izquierda con flechas hacia un cilindro horizontal (la cola) que contiene un mensaje &quot;m₁&quot;; del cilindro sale una flecha hacia arriba a otro &quot;m₁&quot; y de ahí a un cuadrado tachado con una X roja (el consumidor que falló); dos cuadrados C a la derecha apuntan con flechas hacia el cilindro (el pull); del cilindro baja una flecha a un círculo rotulado &quot;VISIBILITY TIMER 60 SEGUNDOS&quot;; al costado, la anotación &quot;EFECTO BALANCEO DE CARGA&quot;
    <span class="figura-ref">notas pág. 3 / pizarra pág. 7</span>
  </figcaption>
</figure>

Cuando un consumidor obtiene un mensaje —m₁—, el servicio no lo borra: el mensaje sigue en la cola. Lo que hace es arrancarle un timer, el visibility timer, por ejemplo de sesenta segundos. Mientras corre, los demás consumidores no ven ese mensaje, justamente para que varios no lo tomen a la vez. Si el consumidor que lo tomó falla, el timer expira, el mensaje vuelve a ser visible y el próximo `receive` lo va a recibir.

De ahí se lee el uso correcto cuando nada falla: el consumidor lee el mensaje, lo procesa y, recién al terminar, invoca la tercera operación, el borrado. Recibir, procesar, borrar. Si falló en el medio y nunca llamó al borrado, el timer expira y otro consumidor toma el mensaje automáticamente. Es el mecanismo de tolerancia a fallas más simple de la materia: alcanza con un timer para que el trabajo perdido reaparezca. Cómo se implementa ese timer en un sistema distribuido es otra historia, que vamos a mirar más adelante.

Aparece el problema del consumidor lento. Si procesar el mensaje tarda más de sesenta segundos, el timer expira mientras el consumidor sigue trabajando, otro lee el mismo mensaje y el trabajo se hace dos veces. Hay dos cosas para hacer. La primera es que estos sistemas suelen tener una operación para extender el visibility timeout —en SQS, `ChangeMessageVisibility`—, una forma de decir «estoy vivo y todavía lo estoy procesando», una especie de heartbeat sobre el mensaje. La segunda es aceptar que, aun así, las cosas pueden fallar por errores de concurrencia.

En este punto estos sistemas son explícitos y reiterativos: la documentación de SQS enfatiza todo el tiempo que puede haber duplicados. Toda esta clase de sistemas admite entregar el mismo mensaje más de una vez, y la obligación cae del lado del consumidor: tiene que ser idempotente, escrito asumiendo que le pueden llegar duplicados. Cuando veamos SQS por dentro vamos a encontrar un caso todavía más incómodo: una falla interna del servicio puede resetear el timeout y a los cinco segundos entregarle el mismo mensaje a otro consumidor, con los dos procesándolo en paralelo. Ese problema es del usuario, y la documentación lo aclara; otro ejemplo de un sistema que traslada el problema difícil a quien lo usa.

{: .nota }
> Lo anterior vale para las colas *standard* de SQS, que son las que usamos en toda la clase: AWS documenta textualmente que «standard queues provide at-least-once delivery» y advierte que se pueden recibir copias duplicadas de un mensaje, razón por la cual las aplicaciones tienen que ser idempotentes. Desde noviembre de 2016 existen además las *FIFO queues*, que ofrecen lo que AWS llama *exactly-once processing*, con deduplicación del lado del productor en una ventana de cinco minutos. El matiz merece precisión: AWS lo llama exactly-once *processing* y no *delivery*, y el mecanismo no vuelve atómicos el efecto de negocio y el `DeleteMessage`, así que un consumidor de una cola FIFO todavía puede volver a ejecutar el mismo código si el visibility timeout expira antes de que llegue a confirmar.

Con eso se puede leer el código de las dos puntas. El del productor es trivial: manda mensajes y se olvida. El del consumidor necesita un bucle:

```python
# consumidor.py
while True:
    resp = sqs.receive_message(QueueUrl=url)
    mensajes = resp.get("Messages", [])
    if not mensajes:
        continue
    msg = mensajes[0]
    procesar(msg)          # tu lógica
    sqs.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
```

Llama siempre a la operación de recibir. Cuando recibe, le llegan los mensajes disponibles —hasta un tope, que en SQS son diez por llamada—. Si no hay, el bucle sigue dando vueltas; en un programa real habría que poner un `sleep` para no consumir CPU de manera desmedida. Si hay, lo procesa —qué significa procesar depende del caso: leerlo, agregarlo a una base de datos, entre otras posibilidades— y después lo borra. Recibir y, al terminar, confirmar: esas son las dos cosas que el consumidor tiene que hacer.

SQS es un ejemplo bastante típico. Si la operación no se llama `delete` se llamará `acknowledge` o de otra forma, pero la estructura es siempre la misma: recibir un mensaje y después decirle al broker «este mensaje ya fue procesado y puede eliminarse», para que no se lo dé a ningún otro consumidor.

Queda una pregunta, porque es el error de diseño más frecuente con este modelo: ¿qué pasa si hay varios consumidores con lógicas distintas que tienen que manejar el mismo mensaje? ¿Corresponde borrarlo al terminar? La respuesta es que ese no es un buen caso de uso. En una cola todos los consumidores tienen que estar en igualdad de condiciones, porque cuando uno consume el mensaje desaparece para los demás. Supongamos que el mensaje notifica que un usuario se dio de baja y que todos los microservicios tienen que borrarlo de sus datos. SQS puro no sirve: el primero que consume el mensaje borra al usuario de su lado y el resto del mundo nunca se entera. Para lógicas de negocio distintas hay formas mejores, y las vamos a ver. El ejemplo que viene ahora es el opuesto, y por eso deja clara la utilidad de la cola: consumidores homogéneos, todos haciendo exactamente lo mismo, con la cola como balanceador de carga de trabajos.

---
