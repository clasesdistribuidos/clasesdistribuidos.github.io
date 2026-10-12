---
title: "1. Procesamiento de streams"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 1
---

# 1. Procesamiento de streams
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


El tema de esta clase es el procesamiento de streams, y la manera más rápida de ubicarlo es pensarlo como una extensión natural de MapReduce. MapReduce servía para calcular sobre datos que ya están quietos en algún lado: es procesamiento por lotes. Tenemos muchos archivos, los procesamos todos juntos y eso produce muchos otros archivos. Ahora combinamos eso con lo de la clase pasada: los datos ya no son archivos esperando en un disco sino streams de datos en tiempo real, y hay que procesarlos en el momento.

El paper de esta clase es MillWheel —fácil de confundir con otro sistema de Google posterior, Windmill—, y arranca con un ejemplo que motiva todo el problema: un sistema de detección de anomalías en las búsquedas al que sus autores pusieron un nombre curioso, Zeitgeist.

Imaginemos una línea de tiempo. Son las ocho de la noche y tenemos muchos data points. Cada uno es una búsqueda que realizó un usuario, con la hora en que ocurrió. Los ejemplos del paper deben ser de la época de Britney Spears, porque el término que usan es «Britney»: uno de los data points es «alguien buscó Britney» a las 8:00. El otro término es «Carly», con un data point a las 8:02. Y después otro Britney a las 8:03. Eso es lo que hay que procesar.

Lo que se quiere es agrupar los eventos en pequeñas ventanas de tiempo —por minuto, por segundo, por diez minutos—, contar cuánta gente buscó una cosa y cuánta otra, y detectar anomalías a partir de esas cuentas. Ese es el ejemplo motivador del paper; nosotros lo vamos a ver más en general.

Y aquí aparece la gran dificultad de toda la clase. De vez en cuando nos va a llegar un evento del pasado: un Britney de las 8:01 que no apareció cuando le correspondía, sino más tarde. Si ya hicimos el cálculo para el minuto 8:01 y después llega un evento que correspondería a esa ventana, tenemos que ver cómo arreglarlo. El problema de los eventos desordenados, e inclusive muy atrasados, va a ser central. Si no existiera, todo sería muchísimo más fácil, y enseguida vamos a ver hasta qué punto. Con él, en cambio, hace falta maquinaria, y el paper la construye con mecanismos muy interesantes.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/linea-de-tiempo-zeitgeist.png' | relative_url }}" alt="Línea de tiempo con las búsquedas de Zeitgeist y un evento atrasado">
  <figcaption>
    <span class="figura-label">Figura</span>
    la línea de tiempo de las búsquedas de Zeitgeist, con los data points de Britney y Carly y el evento atrasado que llega fuera de orden
    <span class="figura-ref">notas pág. 1 / pizarra pág. 1</span>
  </figcaption>
</figure>

## Características de los problemas de streaming

Con el ejemplo en la mano, caractericemos el problema. Lo primero son datasets muy grandes, típicamente generados por actividad del usuario: navegar, cliquear, mirar videos de YouTube y hacer engagement con la plataforma —un play, un abandono a los diez segundos, un like, un comentario, una suscripción—. No tanto los eventos asincrónicos de un servicio que le notifica a otro, que son más esporádicos; esos también se pueden procesar con esta maquinaria, pero la idea son volúmenes muy grandes.

Casi siempre, además, están asociados a tiempo real. No es estrictamente necesario, pero prácticamente todos los problemas que vamos a resolver tienen esa forma: el evento ocurrió a tal hora y queremos agrupar todo lo que pasó a esa hora.

Son también, frecuentemente, *unbounded*, en el sentido de que no terminan nunca. Las búsquedas de Google nunca terminan. Con MapReduce, a lo sumo iríamos procesando un día entero, y después el siguiente; pero no es un dataset fijo, sino que se produce nueva data constantemente.

Llegan, posiblemente, desordenados, que es exactamente lo que vimos con el Britney de las 8:01.

Y posiblemente sean heterogéneos. Muchas veces no vamos a agrupar simplemente el stream de búsquedas, sino que vamos a tener que combinarlo con otro stream en tiempo real, y ahí el problema se complica mucho: datos de distintos lugares que hay que ir juntando de alguna forma. Con todas estas condiciones encimadas, el problema es mucho más difícil que lo que sabemos resolver con MapReduce, o con Spark, que trató de dar una vuelta para atacarlo pero al que Google terminó superando.

{: .nota }
> El paper hace ese mismo planteo en su sección de trabajo relacionado. Reconoce la unificación de streaming y batch que propone Spark Streaming, pero sostiene que MillWheel resuelve una clase más general de problemas y que el micro-batching no es viable sin restringir al usuario a operadores predefinidos, porque depende de los RDDs y esos solo admiten operadores capaces de hacer rollback. El orden es el que sugiere la clase: el paper de Spark Streaming es de 2012 y el de MillWheel de 2013.

Contra ese problema, ¿qué queremos? Ante todo, procesamiento en tiempo real. Si acumulamos los eventos de un día y los procesamos durante la noche, sin apuro, el problema no es tan difícil; lo que queremos es armar el gráfico de las búsquedas en tiempo real, actualizándose con una latencia de segundos a lo sumo. El procesamiento por lotes lo podríamos usar, pero por definición no es lo que buscamos: queremos ver cómo cambian las cosas en el momento.

Queremos también el replay, poder procesar el mismo stream varias veces. Es más bien un objetivo opcional, que depende de la fuente: hay fuentes que guardan los eventos y permiten releerlos, y Kafka es una de ellas, así que con un Kafka el replay lo tenemos casi gratis.

Y queremos que el sistema sea distribuido, que es de lo que se trata la materia. ¿Por qué? Para que sea escalable y tolerante a fallas, y eso engancha con la primera característica: si fueran eventos sueltos, una máquina los procesaría y funcionaría. Ese stream de búsquedas vamos a tener que dividirlo en partes para procesarlo entre muchas máquinas, y ese va a ser el desafío.

El problema del paper es uno entre muchos con la misma forma. Otro es graficar visualizaciones de YouTube en tiempo real y, en base a eso, emitir datos de facturación al sistema que les paga a los youtubers. Otro es analizar en tiempo real los clics en anuncios. Otro es el monitoreo de fraude: detectar que un usuario hizo varias operaciones raras en una ventana corta y que eso dispare algún sistema. Y el más interesante, que quedaría por tratar en profundidad, es alimentar en tiempo real modelos de inteligencia artificial que vayan aprendiendo. El ejemplo de Google tiene un modelo así: el paper no aclara de qué tipo es —si es una red neuronal o qué—, pero dice que aprende de los patrones de las búsquedas.

{: .nota }
> El paper efectivamente nunca dice de qué tipo es el modelo. Lo describe solo como un modelo histórico por consulta, construido para que los cambios esperados de tráfico —el ejemplo que dan es el de «television listings» al caer la tarde— no disparen falsos positivos, y aclara que las predicciones se generan a partir de semanas de datos y que el modelo se actualiza sobre la marcha. Zeitgeist alimenta el servicio Hot Trends de Google. Akidau et al., «MillWheel: Fault-Tolerant Stream Processing at Internet Scale», VLDB 2013, §1 y §2.

## Procesamiento por lotes y micro-batching

Ese stream se puede procesar con las herramientas que ya tenemos, aunque solo hasta un punto. Lo conocido es MapReduce, y conceptualmente también Spark, que para lo que nos interesa aquí es lo mismo. Los dos son procesamiento por lotes, con una virtud y un defecto. La virtud es que escalan: más máquinas resuelven un dataset más grande. El defecto es que no son tiempo real, porque levantar un job de MapReduce es pesadísimo y porque necesita tener todos los datos prearmados antes de empezar.

Hay algo que sí podríamos hacer, y es lo que hizo Spark Streaming: tomar el lote del día entero y dividirlo en fragmentos muy pequeños. A eso se le llama *micro-batching*. Volvamos al dibujo de los data points sobre la línea de tiempo, que podemos poner a distinta altura solo para ilustrar —la dimensión vertical no representa nada—. En vez de procesar el lote del día por la noche, lanzamos muchos jobs pequeños de Spark, uno por segundo, por ejemplo. Cada uno captura data points durante un segundo, los procesa y los emite a donde corresponda, constantemente. Con MapReduce eso sería enormemente ineficiente, y la cuenta lo confirma: lotes de un segundo son 60 × 60 × 24, es decir 86.400 jobs por día, contra el único job del lote nocturno. Levantar un job de MapReduce esa cantidad de veces resulta inviable, y en eso reside la frontera entre los dos: Spark, con muchas estructuras en memoria y un arranque muchísimo más rápido, sí lo puede hacer con una performance aceptable.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/micro-batching.png' | relative_url }}" alt="Micro-batching: lotes de un segundo sobre la línea de tiempo">
  <figcaption>
    <span class="figura-label">Figura</span>
    el micro-batching, con los cortes verticales de un segundo sobre la línea de tiempo y la flecha del evento atrasado que apunta a un lote ya cerrado
    <span class="figura-ref">notas pág. 2 / pizarra pág. 2</span>
  </figcaption>
</figure>

El principal problema es que estamos partiendo por tiempo real. Supongamos que son las ocho y hacemos lotes de un minuto. ¿Qué hacemos si nos llega un evento de las 8:05 que tendríamos que haber contado en un lote que ya iniciamos, cerramos y emitimos? Las cosas fuera de orden, y especialmente las atrasadas, son un gran problema en el micro-batching. Por ahora las salidas son pobres: si ya emitimos un valor para esa ventana, a lo sumo podemos emitir una corrección, o directamente ignorar ese data point. Spark Streaming es básicamente un sistema por lotes que hace lotes muy pequeños y ejecuta muchos seguidos, pero no es exactamente lo que queremos. Buscamos formas mejores de tratar los eventos atrasados, y en eso consiste la gran innovación de Google con este paper.

## Esquema general de un sistema de streaming

El paper de esta clase está pensado de cero para streams de entrada, no como un sistema por lotes dividido en fragmentos. Antes de abrir cada componente, dibujemos en abstracto qué vamos a lograr.

Del lado de la entrada hay un stream, que podría ser Kafka. Más que el stream mandarle cosas al sistema de procesamiento, es el sistema el que lee de ahí. Con lo que lee puede emitir otros eventos hacia otro stream, por ejemplo otro Kafka, o puede llamar por RPC a otro sistema y generar acciones allá: si detecta fraude, puede disparar algo en el momento en que lo detecta. Y sobre la caja del medio, que por ahora está cerrada, caben dos aclaraciones: adentro puede tener muchas particiones, y tiene que tolerar que las fuentes ya vengan particionadas.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/sistema-de-streaming.png' | relative_url }}" alt="Sistema de streaming entre un Kafka de entrada y sus salidas">
  <figcaption>
    <span class="figura-label">Figura</span>
    el sistema de streaming en abstracto: el stream particionado de entrada, la caja de procesamiento, la salida a otro stream y la salida por RPC
    <span class="figura-ref">notas pág. 2 / pizarra pág. 2</span>
  </figcaption>
</figure>

---
