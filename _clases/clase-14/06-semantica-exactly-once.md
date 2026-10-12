---
title: "6. Semántica exactly-once"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 6
---

# 6. Semántica exactly-once
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Lo que viene es la semántica exactly-once, otra garantía que el sistema nos da y que no habíamos mencionado: cada registro se ejecuta una sola vez. De todo el paper, esta es la parte más interesante; los watermarks también lo son, sin duda, pero este mecanismo es de lo mejor.

Sirve justamente para hacer la cuenta, contar cuántas Britneys buscó la gente: el problema que arrastramos desde el principio y que nos llevó a construir la maquinaria de las ventanas. Si vienen registros duplicados, o se duplican internamente por los retries —y va a haber retries—, el sistema garantiza que se cuentan y se procesan una única vez.

## Semánticas de entrega en RPC

Esto cierra el círculo con la primera clase de la materia. Allá dijimos que en un RPC dos máquinas se conectan entre sí, y que sobre ese envío hay tres semánticas posibles respecto de cuántas veces llega un mensaje: at-most-once, at-least-once y exactly-once. Lo que las separa es una sola decisión de implementación: hacer retry o no.

At-most-once es sin retry. El otro extremo recibe el registro a lo sumo una vez, y para garantizarlo basta con no reintentar. El registro puede perderse en el camino sin contradicción: a lo sumo una vez también puede ser cero. En general a nadie le gusta mucho esa idea; se suele preferir alguna de las otras dos.

At-least-once es con retry. La promesa es «te lo voy a mandar por lo menos una vez, hasta que me respondas con un ACK». Si el otro no respondía, se lo volvíamos a mandar, insistiendo hasta que respondiera que lo había recibido. Garantizamos que llegó por lo menos una vez, aunque puede haber llegado quinientas. Eso resulta más satisfactorio porque sabemos que el mensaje llegó, pero no sirve para un conteo: si el emisor mandó cinco veces el mismo registro, lo contamos cuatro veces de más, y el valor de esa ventana queda inflado sin que nada de eso haya ocurrido en la realidad.

Lo que queríamos era la tercera, exactly-once: lo mandamos una vez, el otro confirma, y el problema queda resuelto. Pero dijimos que eso es imposible, en teoría y en la práctica, y también que se pueden obtener aproximaciones. Este sistema obtiene una tan buena que en la práctica termina siendo exactly-once. Primero vemos cómo lo hace, y después cómo lo llama Kleppmann —autor de *Designing Data-Intensive Applications*—, que le da un nombre interesante. Lo que construyen es un pequeño protocolo, más que de transacciones, de atomicidad.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/semanticas-de-entrega.png' | relative_url }}" alt="Dos máquinas y las tres semánticas de entrega">
  <figcaption>
    <span class="figura-label">Figura</span>
    las dos máquinas conectadas por el envío de un registro, con la anotación de que la diferencia entre las tres semánticas está en hacer retry o no hacerlo
    <span class="figura-ref">notas pág. 7 / pizarra pág. 11</span>
  </figcaption>
</figure>

Retomemos cómo se podía lograr un exactly-once según aquella clase. Si el servicio era idempotente, hacíamos retry y no importaba cuántas veces llegara el mensaje: el efecto era el mismo. Si no lo era —el ejemplo más claro es un contador—, teníamos que sintetizar un ID de idempotencia: un número random largo, un UUID, cualquier cosa así alcanza. Marcamos el mensaje con ese ID y se lo mandamos al otro.

## Chequeo de idempotencia y update atómico

En un diagrama de tiempos, con una línea por participante, el mecanismo arranca con un `send` de A a B con el récord y ese ID. El récord es lo que armamos en el modelo de programación, con clave, data y timestamp; a este nivel la clave ya no importa tanto, porque miramos otra capa del sistema. Y ese ID no es la clave: es el ID de idempotencia.

B, para no procesar el récord más de una vez, se fija si ya vio ese ID: si lo vio lo descarta, si no lo procesa. Y lo chequea contra el store, el mismo backing store donde guardamos el estado: además de todo lo demás, ahí también guardamos los IDs. Pero el orden es lo que hace funcionar todo: primero no lo guardamos, primero lo chequeamos con un `check`. El chequeo va antes que cualquier otra cosa, inclusive antes de tocar el código del usuario, porque de eso depende que un registro repetido no llegue nunca a ejecutarse.

Obviamente no es exactamente así: está optimizado, y el sistema cachea cosas para no consultar al store por cada registro. El paper menciona algunas optimizaciones y usa un mecanismo llamado bloom filters, que no tenemos tiempo de ver.

{: .nota }
> Vale precisar en qué dirección ayuda ese filtro, porque no es exactamente un caché. El paper mantiene un bloom filter de las huellas de los récords conocidos para tener un camino rápido en el caso de los récords que **con seguridad nunca vio**; cuando el filtro no acierta, hay que ir a leer el backing store igual para determinar si es un duplicado. Los IDs de las entregas pasadas después se recolectan: se limpian una vez que el sistema puede garantizar que todos los emisores internos terminaron de reintentar —típicamente a los pocos minutos de haber sido producidos—, y para los inyectores que suelen entregar datos tarde esa recolección se demora un margen del orden de unas pocas horas. Akidau et al., VLDB 2013, §6.1.1.

Si el ID estaba en el store, ya procesamos ese registro, así que se descarta y termina todo. El caso interesante es el registro que vemos por primera vez. Ahí se llama a `process_record`, nuestra función: es donde el sistema termina llamando efectivamente al código del usuario.

Y `process_record` claramente tiene efectos colaterales. Vuelve la distinción entre funciones puras y funciones con efectos colaterales. Esta no es pura, y es más fácil verlo con la versión de las variables globales: actualiza una variable global y, a veces, inclusive por los timers, produce récords. Hace las dos cosas. Los timers, por su parte, se procesan más o menos por el mismo camino.

Aquí está la pieza clave del mecanismo. Todo el estado que `process_record` va guardando y todos los récords que emite no salen en el momento: los va acumulando en un buffer en memoria, recordando las operaciones pendientes. Cuando el procesamiento termina, toma todas esas operaciones y trata de mandárselas al store con un `update`.

Ese update es donde se materializan todos los cambios que estuvieron en memoria, y lleva varias cosas. El estado mutable que explícitamente modificamos —los contadores del ejemplo—. Las producciones, los registros que este paso tiene que emitir: todavía no salieron, y antes de emitirlos los guardamos en el storage persistente, con lo cual hacemos efectivamente un checkpoint de lo que tenemos que hacer, sin emitir nada aún. Los timers nuevos, si el procesamiento calendarizó cosas. Y por último el ID de idempotencia con el que arrancó todo. Todo eso se guarda de una, atómicamente, en el storage persistente.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/protocolo-exactly-once.png' | relative_url }}" alt="Diagrama de secuencia del protocolo exactly-once">
  <figcaption>
    <span class="figura-label">Figura</span>
    el diagrama de secuencia del protocolo: A genera el ID único y hace el send con el récord, B chequea el ID contra el backing store, ejecuta process_record en memoria, hace el update atómico con el estado mutable, las producciones, los timers y el ID, manda el ACK a A, y solo después le manda las producciones a C
    <span class="figura-ref">notas pág. 7 / pizarra pág. 11</span>
  </figcaption>
</figure>

La clave es que todo el estado y todos los efectos colaterales se guardan junto con el ID. Si el ID estaba en el store, ese registro ya se ejecutó y ya tenemos guardado todo su output, así que no lo necesitamos más. Si no estaba, y el proceso se ejecutó pero falló antes del update, no pasa nada, porque esa ejecución no tuvo efectos: todo ocurrió en memoria. Se guarda todo junto —el check de idempotencia y todos los outputs— o no se guarda nada.

De manera que, aunque decimos exactly-once, la parte de procesar se podría ejecutar varias veces. Pero si nunca llegamos a guardar el estado mutable, no pasa nada, y la podemos ejecutar todas las veces que haga falta. Con los zombies de la sección anterior puede pasar justamente eso: un nodo ejecuta varias veces lo mismo, pero como falla al guardar el estado, no rompe nada. Las dos partes están muy relacionadas y conviene pensarlas juntas.

Solo cuando tenemos la garantía de que el estado mutable se guardó, y de que no somos un zombie, le mandamos un ACK al emisor diciéndole que el registro está a salvo. Y después del ACK, si había producciones pendientes, se las mandamos con un `send` a otro nodo, que llamaremos C. Ese pequeño protocolo garantiza la atomicidad: se procesa el récord una única vez y no se cuenta de más. Conviene retener el nombre que le pone el paper, porque nombra la pieza que lo hace funcionar —guardar el checkpoint de las producciones antes de emitirlas—: *strong productions*.

## Effectively-once

Kleppmann llama a esto *effectively-once*, y el nombre es una definición: effectively-once es at-least-once más idempotencia. La idempotencia la aporta el chequeo contra el store: si el ID ya está, no se ejecuta nuevamente. Así todo termina siendo idempotente, aunque `process_record` no lo sea en absoluto. Si lo ejecutáramos y se guardara el output cada vez, el resultado sería incorrecto. Pero el procedimiento completo, el check de arriba con el update de abajo, es idempotente como un todo.

{: .nota }
> El término está en el capítulo 11 de *Designing Data-Intensive Applications*, en la sección sobre tolerancia a fallas, y la frase es «This principle is known as exactly-once semantics, although effectively-once would be a more descriptive term». Pero Kleppmann no se lo adjudica: cita como fuente a **Viktor Klang**, que lo acuñó en Twitter el 20 de octubre de 2016 con esta formulación —«I'm coining the phrase "effectively-once" for message processing with at-least-once + idempotent operations»—, que es palabra por palabra la ecuación que la clase escribe en el pizarrón. Vale notar también dónde lo introduce el libro: no hablando de streams sino de procesamiento por lotes, porque el reintento transparente de MapReduce es el caso más limpio de la idea —los récords pueden procesarse varias veces, pero el efecto visible en la salida es como si se hubieran procesado una sola—. Y el libro enumera lo que hay que suponer para apoyarse en la idempotencia: que al reiniciar se reproduzcan los mismos mensajes en el mismo orden, que el procesamiento sea determinístico, que ningún otro nodo actualice concurrentemente el mismo valor, y que puede hacer falta *fencing* para que no interfiera un nodo que se cree muerto pero está vivo. Esas dos últimas condiciones son exactamente el problema de los zombies y el epoch de la sección anterior.

La otra mitad, el at-least-once, cierra el mecanismo por el lado del emisor. Ya sabemos que mandar dos veces el mismo récord no modifica el estado dos veces; ¿qué pasa si falla el envío? Es responsabilidad del que manda esperar el ACK e intentar nuevamente. Si una máquina hace un `send` y nunca recibe el ACK, cada cierto tiempo reenvía el récord, y que lo mande varias veces no tiene consecuencias. Mandar muchas veces, y un mecanismo para garantizar la idempotencia del envío. No es exactly-once en sentido estricto, porque eso es imposible, y de ahí lo bueno del otro nombre: el efecto neto es que las cosas se cuentan y se procesan una única vez.

Y si este nodo a su vez hace retries —si C no está disponible y se le manda el mismo registro varias veces—, C funciona exactamente igual: chequea idempotencia y lo procesa una única vez. El mecanismo se repite en cada envío, y así el grafo entero queda cubierto eslabón por eslabón.

Este procedimiento tiene un costo, y el paper lo mide (Akidau et al., VLDB 2013, §8.1). Con el checkpoint de producciones y el exactly-once deshabilitados, la latencia mediana de entrega de un récord es de 3,6 milisegundos y el percentil 95 de 30; con las dos garantías habilitadas, la mediana salta a 33,7 milisegundos y el percentil 95 a 93,8. La mediana se multiplica por más de nueve: el check contra el store, el buffer y el update atómico se pagan en un orden de magnitud de latencia, y ese número hay que tenerlo a mano cuando el conteo no necesita ser exacto al récord.

Hay otra optimización en el paper que no vamos a desarrollar porque se va del tema: las *weak productions*. Parece consistir en que no hace falta guardar el estado si el cómputo ya era idempotente desde antes. Por ahora la dejamos de lado.

{: .nota }
> Son la contracara de las strong productions que ya nombramos: en las weak productions las entregas hacia abajo se transmiten de manera optimista, antes de persistir el estado. El paper explica el costo de esa relajación, que no es gratis: los tiempos de finalización de etapas consecutivas quedan acoplados esperando los ACK de aguas abajo, y con eso la latencia de punta a punta empeora con la profundidad del pipeline. Con un 1% de probabilidad de que una máquina falle en un minuto dado, un pipeline de profundidad 5 tiene casi un 5% de chance de estar esperando al menos una falla por minuto; MillWheel lo compensa haciendo checkpoint de un porcentaje chico de las producciones rezagadas. Akidau et al., VLDB 2013, §6.1.2 y §6.1.3, y figura 11.

---
