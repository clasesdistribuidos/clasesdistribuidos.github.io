---
title: "8. Dual writes y contextos de ejecución durables"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 8
---

# 8. Dual writes y contextos de ejecución durables

El problema tiene nombre, y es muy conocido por quienes lo sufrieron en producción: **dual writes**. Un
*contexto de ejecución sin estado durable*, que escribe en múltiples sistemas que no comparten una
transacción, no puede garantizar que todas las escrituras ocurran. Cada parte de la definición importa.
Un contexto de ejecución es un pedazo de CPU corriendo un pedazo de código; que no tenga estado durable
significa que si muere en cualquier punto, al volver no sabe dónde había quedado: no hay memoria, no
hay disco, no hay nada. Y los sistemas no comparten una transacción: no hay nada atómico que los una en
un todo o nada.

La mayoría de los sistemas distribuidos que usamos en producción no tienen transacciones distribuidas
entre sí, y las que existen son lentas y no escalan para la mayoría de los casos, porque todos los
participantes tienen que ponerse de acuerdo. Los microservicios multiplican el problema: cada llamada a
otra API es un sistema que no comparte transacción con nosotros. Una API que al ser llamada hace cuatro
`POST` a distintos servicios y se rompe en el medio deja a dos con el valor y a dos sin él. No va a
pasar en la primera demo frente a producto; va a pasar a la semana, con carga real, y aparecerán
usuarios que ven un dato y no el otro, sin ninguna explicación.

Suele decirse que estos sistemas son "eventualmente consistentes". No lo son. La consistencia eventual
promete que, una vez que dejan de entrar escrituras y un nodo recibe todas las que ocurrieron, llega al
mismo estado que los demás, y lo hace solo. Un sistema que pierde escrituras porque se rompe en el medio
no converge nunca: es **inconsistente**, y en muy poco tiempo. Lo único que queda es algún proceso de
reparación que intente arreglarlo con información que tampoco está completa.

¿Qué contextos de ejecución son durables? No lo son un handler de un endpoint HTTP (si la API se
reinicia, se perdió lo que estaba haciendo), un hilo en background (si la aplicación se reinicia, el
hilo desaparece) ni un suscriptor de pub/sub en el que, si no estamos escuchando cuando se emite un
mensaje, lo perdemos. Guardar el progreso en memoria tampoco sirve, ni siquiera en el disco local de una
máquina que puede desaparecer: si tenemos dos instancias de la API detrás de un balanceador y una muere
para siempre, lo que tenía se fue con ella. En todos estos casos, si hay un error no podemos asegurar
que se vuelva a intentar. Sí son durables el consumidor de una cola o de un stream (SQS, RabbitMQ,
Kafka): si la cola confirmó y persistió el mensaje y fallamos al procesarlo, nos lo vuelve a entregar.
También un motor de *workflow orchestration* (Temporal, AWS Step Functions), que persiste cada paso y,
si algo se rompe en el medio, retoma donde quedó o nos avisa por otro mecanismo. Y consumir el WAL de la
base, como hace B: si se cae un rato, el LSN guarda su posición y retoma desde ahí. En los contextos
durables, ante un error podemos volver a intentar, aunque tal vez procesemos algunos mensajes de nuevo.

Para no tener dual writes, entonces, no podemos escribir en más de un sistema desde un contexto no
durable. El único sistema con atomicidad a mano es la transacción de la base. Una primera forma de
aprovecharla es guardar, dentro de la misma transacción de la compra, un registro con todo lo necesario
para enviar la notificación, en una tabla de tareas pendientes. Como la transacción es todo o nada, el
lugar dentro de ella no importa. Después, otro proceso recorre esa tabla: toma una tarea, envía la
notificación y la marca como enviada. Si falla entre el envío y la marca, reintenta, así que la entrega
es *at-least-once*, y hay que acotar los reintentos para no enviar la misma notificación para siempre.

La idea es correcta pero implementar ese poller es complejo, y las sutilezas son fáciles de pasar por
alto. Tiene que consultar la base con bastante frecuencia, y probablemente de a lotes. En producción no
corre una sola instancia de cada cosa: si un nodo deja de reportar que está vivo y el autoescalado
levanta otro, puede haber dos procesando la misma tabla a la vez, y hay que coordinarlos con locks o
flags en la base. Si además se necesita respetar el orden de envío o no enviar duplicados, se complica
más. Hay implementaciones que, después de cierta cantidad de reintentos, descartan la tarea sin avisar,
u otras que no preservan el orden cuando uno suponía que sí.

Esta idea tiene nombre: ***outbox pattern***. Es un concepto interesante, aunque fuera del alcance de la
materia: evitar los dual writes usando una tabla como *outbox*, escrita en la misma transacción que la
operación, para que ambas sean atómicas. Después, un poller extrae esa información o, mejor, un
consumidor por CDC (*change data capture*) que lee los cambios desde el log de la base. Esa segunda
forma es la que construimos a continuación, con una ventaja: ni siquiera necesitamos una tabla extra,
porque la compra ya está en el WAL.

---
