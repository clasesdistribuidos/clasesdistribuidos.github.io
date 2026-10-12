---
title: "3. Watermark"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 3
---

# 3. Watermark
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Punto de corte

Abordemos ahora el problema central que quedó planteado: ¿hasta cuándo esperamos eventos viejos? Volvamos al dibujo de antes, que ya tiene todos los ingredientes. Seguimos asumiendo que son las ocho de la noche. El eje horizontal es el processing time —el tiempo real, que abreviamos PT— y sobre él van llegando los eventos, uno tras otro. Queremos agruparlos por una ventana de, por ejemplo, cinco minutos: supongamos que llega hasta las 8:05, nuevamente en tiempo real. Algunos eventos llegaron casualmente dentro de la ventana, y esos hubieran sido fáciles de cualquier forma. Pero hay otros, más a la derecha, que también tendrían que ir a esa ventana. Si sumamos uno por cada evento, uno de los que aparecen más tarde tiene event time 8:03, por ejemplo, y sin embargo nos llega un poco atrasado.

Queremos definir una línea de corte, un lugar a partir del cual tengamos la garantía de que de ese lado ya no nos va a llegar ninguno atrasado. Cuando podamos garantizarla, cerramos la ventana: contamos lo que entró, seguimos contando un poco después del borde todo lo que fue llegando, y en esa línea emitimos la cuenta total. La emitimos a otro stream, a otro sistema o a una base de datos que la va guardando, para ir armando el gráfico del que venimos hablando: un valor por ventana, y el gráfico que se extiende a medida que se cierran las ventanas.

A esa línea, por ahora, la llamamos el punto de corte; más adelante veremos que tiene un nombre bastante más metafórico y elegante. Lo que hace es aceptar hasta aquí y cerrar ventana.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el punto de corte: los eventos que van llegando sobre el eje de processing time, la ventana de las 8:00 a las 8:05, los eventos atrasados que le corresponden y la línea vertical del corte en 8:09
    <span class="figura-ref">notas pág. 4 / pizarra pág. 4</span>
  </figcaption>
</figure>

Hay algo del punto de corte que conviene examinar con cuidado, porque es la fuente de buena parte de la confusión que viene: obviamente va avanzando a medida que pasa el tiempo. Supongamos que la línea que dibujamos es el punto de corte de las 8:05 —ahí llegaron cosas hasta las 8:05— y que eso no ocurrió hasta las 8:09. A las 8:09 obtuvimos la garantía de que ya recibimos todo hasta las 8:05. Son dos horas distintas para un mismo hecho: hasta dónde llega la garantía, las 8:05, y cuándo la obtuvimos, las 8:09. Y la relación entre las dos no queda quieta: a medida que avanza el valor garantizado, el momento en que se obtiene también ocurre más tarde, así que el punto de corte se corre por los dos ejes a la vez. Es difícil de visualizar, y decirlo explícitamente sirve, porque esa distinción va a ser importante en todo lo que sigue.

## Delay fijo y watermark informado por la fuente

Para empezar a generar intuición, la idea uno es introducir la línea de corte a mano, porque sí: un delay fijo. Si sabemos que los eventos no llegan más de diez minutos atrasados, tomamos el tiempo actual, le restamos diez minutos, y decimos que ese es el punto de corte. A las 8:09, por ejemplo, afirmamos que no nos va a llegar nada de las 7:59 para atrás, porque ya pasó un tiempo razonable y consumimos todos esos eventos. Con la ventana pasa lo mismo: si va de las ocho a las 8:05, le damos diez minutos de margen y la cerramos y emitimos a las 8:15.

Puede resultar confuso porque intervienen muchos tiempos distintos: es como cambiar de huso horario. Pero es la forma fácil y trivial de hacerlo. Inclusive se podría aplicar en los sistemas de micro-batching, aunque habría que pensar cómo.

El problema es que es arbitrario: un delay elegido sin fundamento, un número que nadie garantiza, y cuanto más seguros queremos estar, más grande tiene que ser y más vamos a tener que esperar. Basta medirlo contra lo que nos propusimos: los diez minutos de margen son 600 segundos, y en la primera sección fijamos como objetivo una latencia de segundos a lo sumo. El delay fijo, con tal de estar seguros, se lleva por delante dos órdenes de magnitud del requerimiento que motivó todo el sistema. Y al revés, si lo queremos rápido, apostamos a un delay corto y resignamos seguridad. El caso extremo es el día entero, 86.400 segundos: si la ventana se cierra únicamente al final del día, procesamos todo pero postergamos la emisión hasta entonces, con lo cual decaemos a un proceso batch. Justo lo que queríamos evitar.

La idea dos es la buena, y es la que propone Google en este paper —probablemente venía de otros lugares, pero es el que la puso—: que la fuente, el emisor de los eventos, nos informe ese punto de corte. Y ahora sí le ponen nombre: watermark, marca de agua. La metáfora es la del agua contra un muelle que suben y bajan, donde siempre queda la marca, que siempre va subiendo. El watermark tiene esa característica: siempre avanza, y siempre nos dice «ya envié todo hasta este punto; hay garantía de que no llegará nada anterior». Eso es lo que podemos usar para cerrar ventana.

{: .nota }
> La sospecha de que la idea venía de otros lugares es correcta, y el paper la despeja él mismo en su sección de trabajo relacionado. Su mecanismo, que llama siempre *low watermark* y no simplemente watermark, es análogo a las *punctuations* de Tucker et al. (2003) y a los *heartbeats* de Johnson et al. (2005) usados en sistemas como Gigascope; y el concepto de low watermark, junto con la decisión de calcularlo en un agregador global en vez de operador por operador, viene del sistema OOP de Li et al. (VLDB 2008), al que el paper cita como el lugar donde estos low watermarks ya están definidos. Lo que aporta MillWheel es la implementación a escala, no la idea. Akidau et al., VLDB 2013, §9.

## Watermark de un log particionado: exacto y heurístico

Para bajar a algo concreto qué sería que la fuente nos informe el watermark, sirve el caso de Kafka. Imaginemos un Kafka con tres particiones y un único procesador que tiene que consumir de las tres. En la clase pasada dijimos que típicamente se asigna un procesador por partición, y eso sigue siendo cierto; pero si hay que agregar todo, de todas las particiones, el asunto cambia. Si la clave que usamos para mandar un evento a una partición no es la clave por la que queremos agregar —por ejemplo, porque queremos la suma total de todos los eventos—, este procesador va a tener que consumir de todas.

Dentro de cada partición, cada evento tiene un timestamp, y Kafka puede garantizarnos que es ascendente dentro de la partición. Puede, y no siempre: la garantía vale cuando el sello lo pone Kafka al escribir el mensaje, y de esa condición depende todo lo que sigue. Usemos números pequeños: en una partición obtenemos un 9 y después un 11. Kafka garantiza que serán siempre ascendentes porque los metió una única máquina que les fue poniendo el sello ascendente. Partición por partición, entonces, el timestamp del mensaje mismo ya es la garantía de que no vendrá nada más atrasado. Si recibí un mensaje con timestamp 10 y leo otro de esa misma partición, no va a venir un 9: puede venir el 11, el 12 o el 400, pero nada anterior.

Pero consumimos de tres, y el procesador va por distintos lugares en cada una: las posiciones no tienen por qué coincidir. Si de una partición consumí el evento con timestamp 12 y ya lo agregué a una ventana, ¿tengo la garantía de que no me llegará nada más viejo? No, porque en otra partición puede haber un mensaje con un 9. Hay que combinar la información de las tres para saber el watermark global del stream.

La regla queda en dos niveles. Por partición: si ya vi el timestamp T₁, todos los siguientes serán mayores, porque cada partición es monótona ascendente; el watermark de la partición es el timestamp del último mensaje visto. Pero para el stream como un todo —las tres particiones juntas— hay que tomar el mínimo: el watermark del stream es el mínimo de los timestamps de cada partición. Siempre la más lenta es la que garantiza el watermark de todo el stream, y ese es el que le importa al que agrega. Con nuestros números: si una partición ya vio el 12 pero otra va por el 9, el watermark del stream es 9, porque la que va por 9 todavía nos puede entregar un 10, y si cerramos por encima de eso estaríamos cerrando una ventana que todavía tiene eventos por llegar.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el watermark de un log particionado: las tres particiones de Kafka con el último timestamp visto en cada una y el mínimo que resulta ser el watermark del stream
    <span class="figura-ref">notas pág. 4 / pizarra pág. 4</span>
  </figcaption>
</figure>

Esta idea se va a repetir: con muchas fuentes, el watermark en general es el de la más lenta, porque haber visto una fuente más rápida no garantiza que la más lenta no me dé algo más viejo. Esa forma de razonar va a volver.

De aquí se desprenden dos tipos de watermark, porque no siempre vamos a tener un sistema tan ordenado como Kafka. El watermark exacto es el que se calcula sin estimar nada, porque sale de las garantías del propio sistema de mensajería: el ejemplo es Kafka, y precisamente con el timestamp que asigna Kafka al recibir un evento en una partición, tomando el mínimo de todas las particiones. El otro es el watermark heurístico, el estimado, que muchas veces es una mezcla de estimación con algún tiempo. Supongamos que tenemos Kafka, pero lo que nos interesa no es su sello sino el tiempo que generan los productores de los mensajes. Esos productores probablemente estén desincronizados entre sí; pero si se sincronizan contra un servidor de tiempos del data center, lo estarán por a lo sumo un par de milisegundos, a lo sumo un segundo. Entonces tomamos el watermark de Kafka y le sumamos un delta, un segundo, por ejemplo. Eso ya es heurístico: no hay una garantía tan exacta, pero lo podemos armar. Y la mayoría de los watermarks terminan siendo así, sin la precisión con la que veníamos trabajando.

{: .nota }
> La distinción entre los dos casos de Kafka es exactamente la que separa sus dos tipos de timestamp, configurables por tópico con `log.message.timestamp.type`. Con `LogAppendTime` el sello lo pone el broker al escribir el mensaje en su log, y por eso es monótono creciente dentro de la partición: ese es el caso del watermark exacto. Con `CreateTime`, que es el valor por omisión, el sello lo pone el productor y la API acepta cualquier valor, así que los timestamps pueden venir desordenados dentro de la partición: ese es el caso que obliga a la heurística. Vale aclarar también que el watermark heurístico del propio MillWheel es otro mecanismo distinto del de este ejemplo: la autoridad central puede descartar los valores extremos y ofrecer, por ejemplo, un low watermark del 99%, que corresponde al avance del 99% de los timestamps del sistema, para pipelines a los que les interesa más la velocidad que la exactitud. Akidau et al., VLDB 2013, §7.2.

## Gráfico de event time contra processing time

Hay un tipo de gráfico difícil de entender al principio pero que remarca algo importante; lo usa mucho otro paper que iba a estar en esta clase y quedó afuera, el del modelo de Dataflow, sucesor directo de MillWheel. En el eje horizontal va el event time y en el vertical el processing time.

{: .nota }
> La referencia completa es Akidau et al., «The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing», VLDB 2015. De ahí salen también los nombres *watermark perfecto* y *watermark heurístico* que usamos aquí. Y una precisión sobre los ejes: el horizontal mide la completitud en event time, es decir hasta qué momento se observaron todos los datos, y el vertical el avance del processing time, el reloj de pared tal como lo ve el sistema mientras ejecuta.

Es difícil porque hay que imaginar que el tiempo real transcurre hacia arriba: cada corte horizontal es una foto de lo que pasaba en un instante. Y cada evento viene marcado con su event time, que se lee en el eje horizontal.

Si dibujamos la diagonal a 45 grados, los eventos que caen ahí son los de timing perfecto: ocurrió a las ocho y lo procesamos a las ocho, ocurrió a las 8:05 y lo procesamos a las 8:05. Esa línea es la referencia del caso teórico. No consideramos una máquina con el reloj mal que nos mande eventos del futuro; técnicamente podría pasar, pero lo dejamos afuera. Siempre llegan cosas del pasado, así que toda una mitad del gráfico, la de un lado de la diagonal, se descarta. Con un corte horizontal es más fácil: si son las ocho, nos llegan cosas de las 7:50, de las 7:55, y nada del futuro.

Esa línea nos dice que los eventos llegan a la izquierda de la diagonal. Y en algún momento tenemos la garantía del watermark, que es como un tope: la fuente nos dice que no puede llegar nada con event time anterior al watermark, y ya dijimos que no puede llegar nada del futuro. Los eventos quedan acotados en la franja del medio. El watermark, a medida que el tiempo avanza hacia arriba, se va moviendo, y podemos dibujar su avance como una curva ascendente pero irregular. En teoría los eventos van apareciendo entre la diagonal y la curva del watermark, como puntos entre esas dos líneas. Alguno rezagado puede caer del otro lado, pero deberían ser los menos: si el sistema funciona bien, y sobre todo si el watermark es exacto, la gran mayoría cae entre las dos líneas. Es un gráfico poco habitual y conviene analizarlo con detenimiento, familiarizándose con los dos ejes, con el watermark y con cómo avanza.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el gráfico de event time contra processing time, con la diagonal del timing perfecto y la curva ascendente e irregular del watermark
    <span class="figura-ref">notas pág. 5 / pizarra pág. 5</span>
  </figcaption>
</figure>

Y aquí está la clave de todo: el watermark es lo que usamos para cerrar la ventana. Para atrapar todos los eventos de una ventana, dibujamos nuevamente event time contra processing time, la diagonal de referencia y el watermark que nos van informando. El punto en que el watermark vale lo que el borde de la ventana —cuando vale 8:05, y acaba de ocurrir— es el punto en que el sistema nos dice que ya podemos cerrarla. Todos los eventos atrapados en el medio son los que calculamos y emitimos. Con un poco de reflexión se ve que es exactamente así.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el mismo gráfico usado para cerrar la ventana: el watermark cruzando el borde de las 8:05 y los eventos que quedan atrapados entre la curva y la diagonal
    <span class="figura-ref">notas pág. 5 / pizarra pág. 5</span>
  </figcaption>
</figure>

---
