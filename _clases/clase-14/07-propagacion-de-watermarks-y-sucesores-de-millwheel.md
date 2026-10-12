---
title: "7. Propagación de watermarks y sucesores de MillWheel"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 7
---

# 7. Propagación de watermarks y sucesores de MillWheel
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Queda una última pieza para cerrar el sistema: cómo resuelve MillWheel los watermarks por dentro. No es la parte más ingeniosa —el mecanismo es más bien directo—, pero hay un par de cosas a considerar con cuidado. La primera: ¿quién genera los watermarks? Hay componentes que consumen de Kafka, llamados inyectores, que son la fuente primaria de watermarks de todo el sistema. Una vez que el watermark entró por ahí, se va propagando por el grafo.

## Propagación por el grafo de cómputos

Imaginemos un grafo fácil, de tres etapas: A le manda a B, y B le manda a C. En abstracto no son nodos sino cómputos, cada uno corriendo posiblemente en varias máquinas.

Típicamente, cuanto más cerca de la fuente está una etapa, más adelantado va su watermark. Si el de A va por las 8:30 —A ya recibió todo hasta las 8:30—, se esperaría que los otros vayan más atrasados: B por las 8:20 y C por las 8:10. Hay un delay de propagación, y no es un accidente de esta configuración: no podría ser de otra manera. B no puede estar más adelantado que A, porque el que le manda cosas es A, y B no puede haber visto cosas más nuevas que las que vio A.

El watermark se va propagando y cada etapa le agrega un poco de delay propio. A le manda sus cosas a B; B las tiene en un buffer y tarda un poco en procesarlas, y de ahí sale el extra. Los diez minutos entre las 8:30 y las 8:20 son exactamente eso: cosas que B está procesando y todavía no le mandó a C.

Con lo cual el watermark sirve también para algo que no tiene que ver con ventanas: ver qué tan atrasada está cada etapa, o si una está muy lenta respecto de las demás. Si A va por las 8:30 y B por las 8:00, llama la atención inmediatamente: B está saturado, y hay que hacer algo para que acelere y se acerque a lo que le entra desde A.

De esto se desprende una regla intuitiva: el watermark de A es mayor o igual que el de B, y el de B mayor o igual que el de C. La desigualdad se sostiene a lo largo del pipeline, porque ninguna etapa puede estar más adelantada que su fuente. Y la fórmula para calcular cada valor es un mínimo entre dos cosas: el watermark de B es el mínimo entre el watermark de su fuente —A— y el trabajo propio más viejo de B, lo que tiene en buffer o pendiente. Es un mínimo por lo que ya vimos: B no puede estar más adelantado que A, pero sí más atrasado, y lo que lo atrasa es su trabajo sin terminar. El paper lo dice de manera más abstracta, hablando del trabajo *más viejo*. Esa es la razón por la cual las etapas se van atrasando: cuanto más largo el pipeline, más delay mete cada una. Con los números que midió el paper —1,8 segundos de atraso en la primera etapa y menos de 200 milisegundos por cada etapa siguiente—, un pipeline de diez etapas terminaría alrededor de 3,6 segundos detrás del tiempo real: el doble que una sola etapa, con nueve etapas más encima.

{: .nota }
> La definición del paper es recursiva y coincide exactamente con la fórmula. Dado un cómputo A, define el *oldest work* de A como el timestamp del récord sin terminar más viejo que tiene A —en vuelo, almacenado o pendiente de entrega—, y define el low watermark de A como el mínimo entre ese oldest work y los low watermarks de todos los cómputos que le mandan datos a A. Vale agregar el caso de borde, que el paper aclara y que ayuda a ver por qué los inyectores son el origen de todo: si un cómputo no tiene streams de entrada, su low watermark y su oldest work son el mismo valor. Akidau et al., VLDB 2013, §4.5.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/pipeline-de-watermarks.png' | relative_url }}" alt="Pipeline de tres etapas con sus watermarks">
  <figcaption>
    <span class="figura-label">Figura</span>
    el pipeline de tres etapas con su watermark: A por las 8:30, B por las 8:20 y C por las 8:10, y la desigualdad entre los tres
    <span class="figura-ref">notas pág. 8 / pizarra pág. 11</span>
  </figcaption>
</figure>

## Autoridad de watermarks

Falta la otra mitad: cómo se calcula ese valor dentro de una etapa. Es intuitivo. Hagamos zoom e imaginemos que A son dos máquinas y B, para simplificar, una sola. Los dos nodos de A le mandan cosas a B; uno tiene el rango de claves de la A a la M y el otro de la M a la Z. Cada uno tiene su propio watermark, porque tiene sus propias fuentes y su propio trabajo pendiente, calculado con la misma cuenta. Supongamos que uno va por el 100 y el otro por el 200.

Vuelve la idea de las particiones de Kafka: con varios streams, hay que tomar el más lento. El watermark de toda la etapa A es el más chico: 100. Y ese es el valor que B considera como watermark de su fuente.

En teoría, ese mínimo lo podría calcular B directamente. Los de MillWheel tomaron otra decisión. No es que el watermark viaje hacia B junto con los mensajes, que también se podría haber hecho: metieron un tercero en el medio, la autoridad de watermarks. Es un sistema aparte, con una lógica parecida a la de los epochs, para que un zombie no mande información vieja.

¿Por qué así? Por lo que se puede reconstruir, lo armaron como un sistema global porque los rangos son muy dinámicos y cambian. Con la autoridad en el medio se evita que B reciba información de una partición que se dividió en dos, y se evita implementar toda la complejidad de los epochs en cada cómputo. Todos los nodos le informan sus watermarks a la autoridad, y ella le informa el watermark a cada uno de los otros nodos.

Internamente, la autoridad mantiene una tabla: el cómputo A tiene dos particiones, de la A a la M y de la M a la Z; una va por el 100 y la otra por el 200; el watermark de A es 100. Ese 100 se lo manda a todos los nodos suscriptos, los que quieren saber por dónde va A. La dificultad viene de que cada uno de esos nodos puede tener un valor distinto.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/autoridad-de-watermarks.png' | relative_url }}" alt="La autoridad de watermarks calculando el mínimo de A">
  <figcaption>
    <span class="figura-label">Figura</span>
    la autoridad de watermarks: los dos nodos del cómputo A con sus rangos de la A a la M y de la M a la Z y sus watermarks 100 y 200, la autoridad que calcula el mínimo, y el watermark de A igual a 100 que le llega a B
    <span class="figura-ref">notas pág. 8 / pizarra pág. 12</span>
  </figcaption>
</figure>

Es cuestionable si una autoridad central es la mejor forma, o si los nodos podrían informarle el watermark a B directamente para que lo calcule. Pero B tampoco es un solo B, sino muchos, y alguno puede enterarse de que se partieron las particiones y otro no. Allí está la clave: el reparto del trabajo no es una cosa o la otra, sino las dos a la vez, dividido a propósito. La autoridad agrega lo que reporta cada proceso y difunde un valor por cómputo —el 100 del ejemplo—, pero el mínimo entre los distintos cómputos que le mandan datos a uno lo calcula el nodo que consume. La razón es de consistencia: los valores de la autoridad tienen que ser siempre al menos tan conservadores como los de los nodos, y haciendo que cada nodo calcule el mínimo de sus propias entradas se garantiza que el watermark de la autoridad nunca se adelante al de los nodos.

{: .nota }
> Dos detalles más del mecanismo, para completarlo. Lo que la autoridad arma con lo que le reportan los procesos es un mapa de intervalos de claves por cómputo, y si algún intervalo falta conserva para él el último valor conocido en vez de dejar un hueco. Y lleva un *sequencer* en cada actualización de low watermark —el mismo recurso que el epoch de la sección anterior—, de modo que solo el dueño actual de un intervalo de claves pueda actualizarlo. La autoridad puede además shardearse entre varias máquinas: empíricamente escala a 500.000 intervalos de claves sin pérdida de performance. Akidau et al., VLDB 2013, §7.2.

## Watermark como métrica, Dataflow y Apache Beam

Lo último sobre los watermarks es la figura 15 del paper: un pipeline parecido al del ejemplo, con etapas 1, 2 y 3 en lugar de A, B y C, y el watermark de cada una. El delay es la diferencia entre el tiempo real y el watermark: cuanto más alejados del eje, más lento va el nodo. Se ve que cuanto más nos alejamos de la fuente, más lento procesamos, y la diferencia entre cada pico es lo que aporta cada nodo a la lentitud del sistema total.

{: .nota }
> Esa figura tiene números, y conviene tenerlos porque dan la escala del fenómeno. El experimento corrió un pipeline de tres etapas sobre 200 CPUs, consultando el low watermark de cada cómputo una vez por segundo. El de la primera etapa quedó **1,8 segundos** detrás del tiempo real, y a partir de ahí cada etapa agregó **menos de 200 ms**: los promedios son 1.795, 1.954 y 2.081 milisegundos. Es decir que el grueso del atraso lo aporta la fuente, no la profundidad del pipeline —el salto de la primera etapa es nueve veces mayor que lo que suma cada etapa siguiente—, y el paper aclara que reducir ese lag era un área de desarrollo activa. Akidau et al., VLDB 2013, §8.2.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/low-watermark-lag.png' | relative_url }}" alt="Lag del low watermark en tres etapas, figura 15 del paper">
  <figcaption>
    <span class="figura-label">Figura</span>
    el delay de propagación del watermark medido en un pipeline de tres etapas
    <span class="figura-ref">figura 15 del paper de MillWheel</span>
  </figcaption>
</figure>

El watermark no sirve solamente para las ventanas: también es una métrica de la eficiencia del pipeline. Si una etapa está por un lado y todas las demás mucho más lejos, esa etapa funciona muy lento y hay que optimizarla para acercarla a las otras. Tiene esa doble función: cerrar ventanas y medir la eficiencia del pipeline, algo de lo que prácticamente no hablamos. Esta última parte es quizás la más confusa de la clase; si algo hay que retener, es que el watermark sirve además para ver qué tan rápido o lento funciona todo.

Queda mencionar qué pasó después. MillWheel evolucionó a Windmill, y de ahí al sistema que Google Cloud ofrece hoy para ejecutar estas cosas: uno implementa el `process_record` y el `process_timer` —en realidad no exactamente, y enseguida vemos por qué—, lo sube a Google Cloud, y ellos lo ejecutan como servicio. Eso se llama Dataflow.

Dataflow agregó dos cosas. El paper de Dataflow agrega un modelo de programación de más alto nivel. El ejemplo que mostramos es interesante, pero —y esto responde la pregunta que quedó pendiente con el modelo de programación— resulta poco natural pensar todo en términos de `process_record` y `process_timer` cuando los casos de uso son tan distintos. Ese modelo de programación evolucionó y se implementó como proyecto open source: Apache Beam, lo más interesante de todo esto para investigar por cuenta propia. Uno programa con Beam, eso se «compila» a las mismas funciones que vimos, se sube a la nube de Google, y lo ejecutan sobre esta versión de Windmill, una especie de MillWheel que no tiene un ejecutable sólido sino ejecutables a los que se les inyecta el código de uno. Esa imagen es bastante fiel a cómo funciona hoy. Windmill está por debajo del Streaming Engine de Dataflow, que saca la ejecución de las máquinas del usuario y la lleva al backend de Google, partida en dos. Nuestro código corre en un worker que no guarda nada propio: aplica las transformaciones y arma ahí las ventanas, y el estado y los timers se los pide a Windmill, que es el que los guarda y garantiza el procesamiento consistente. Las ventanas, otra vez, quedan arriba de la primitiva.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-14/genealogia-de-millwheel.png' | relative_url }}" alt="De MillWheel a Windmill, Dataflow y Apache Beam">
  <figcaption>
    <span class="figura-label">Figura</span>
    la genealogía del sistema: MillWheel dando lugar a Windmill, a Dataflow y a Apache Beam, con Flink y Spark Streaming al costado como alternativas de ejecución
    <span class="figura-ref">pizarra pág. 12</span>
  </figcaption>
</figure>

Y Beam terminó siendo una especie de estándar: el mismo programa puede ejecutarse sobre el Dataflow de Google, sobre Flink —quizás el más interesante de todos, y el que más vale investigar— o sobre Spark Streaming. Hoy ya nadie programa directamente el `process_record` y el `process_timer`, aunque no siempre fue así: mientras MillWheel fue un sistema interno, los equipos de Google sí programaban contra esa API, y el paper cuenta para qué la usaban: joins de streams para Ads, la facturación —que depende justamente del exactly-once—, detección de anomalías, monitoreo de la red y hasta el procesamiento de imágenes de Street View.

Lo que cambió es que hoy se programa un nivel más arriba, y eso es lo que hay que retener: el modelo de programación se estandarizó y se desprendió del motor que lo ejecuta. Las primitivas de MillWheel siguen ahí abajo, garantizando el exactly-once con el check y el update atómico, pero quedaron del lado de la infraestructura, igual que los mappers y reducers quedaron debajo de lo que vino después de MapReduce. Arriba queda la descripción del cómputo, indiferente a quién lo corra.
