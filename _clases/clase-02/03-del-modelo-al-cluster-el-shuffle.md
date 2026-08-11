---
title: "3. Del modelo al clúster: el shuffle"
parent: "Clase 2 — MapReduce"
nav_order: 3
---

# 3. Del modelo al clúster: el shuffle
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Hasta ahora todo fue conceptual: pares, claves intermedias, un agrupamiento que ocurre en un lugar indeterminado. La pregunta que sigue es cómo se termina implementando esto sobre máquinas reales, y la respuesta pasa por corregir dos veces la imagen que nos armamos.

## Jobs lógicos y nodos físicos

En la práctica vamos a tener un clúster de muchas máquinas, y van a ser máquinas físicas. Ejecutarlo siempre de forma local carece de sentido: el propósito del sistema es repartir el cómputo entre computadoras distintas.

Empecemos con una imagen simplificada, y hay que presentarla como tal porque la vamos a corregir enseguida. Digamos que de un lado tenemos un grupo de nodos mapper, encargados de la primera parte del algoritmo: todos los inputs se distribuyen entre esos nodos y cada uno ejecuta la función map. Y del otro lado, otro grupo de nodos, los reducers, que ejecutan la segunda parte. Parte de lo que el algoritmo tiene que hacer es precisamente esa distribución: enviar los valores de un lado al otro.

Lo primero que en la realidad no funciona así es esa separación: no hay un conjunto de nodos mappers y otro de nodos reducers, sino el mismo clúster de computadoras, que primero actúa como mapper y después como reducer.

La razón queda a la vista en cuanto se piensa en los tiempos. No se pueden empezar a ejecutar los reducers hasta que no terminen todos los mappers: en MapReduce hay dos fases bien diferenciadas y no se pueden mezclar. Primero terminan todos los mappers, y después terminan todos los reducers. Con dos clústeres separados, uno iba a quedar ocioso esperando que la otra fase termine, y eso es un desperdicio de máquinas.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    los nodos mapper y los nodos reducer dibujados como dos grupos, y la corrección de que son los mismos nodos cambiando de rol; al costado, M mappers y R reducers como jobs lógicos contra N nodos físicos, con M &gt;&gt; N
    <span class="figura-ref">notas pág. 3, fig. 2 / pizarra pág. 6</span>
  </figcaption>
</figure>

La segunda corrección tiene que ver con el conteo. Conceptualmente hay que ejecutar un mapper por cada input, y ese input puede tomar dos formas: muchos archivos diferentes, o un único archivo gigante que se divide en fragmentos. A cada uno de esos fragmentos se le suele decir *split*. Los dos casos son equivalentes. Si tenemos mil archivos para procesar y cada archivo es un split, o si tenemos un solo archivo gigantesco que dividimos en mil fragmentos para distribuirlo y procesarlo de forma independiente, vamos a necesitar mil mappers: uno por cada componente de ese split.

Y ahí aparece lo interesante, porque podemos tener muchos más mappers —mappers lógicos— que nodos disponibles. Lo que va a terminar ocurriendo es que algunos maps queden a la espera: hay un map listo para ejecutarse, pero ningún nodo libre que lo tome, así que el cómputo entero va a tardar un poco más.

Hay tres cantidades en juego, independientes entre sí. Llamemos M a la cantidad de mappers, R a la de reducers y N a la de nodos físicos. Típicamente no hay ninguna relación fija entre M, R y N. De hecho es muy común que M sea bastante más grande que N, e incluso el paper lo recomienda: que haya muchos más mappers que nodos disponibles. La razón es doble: así siempre tenemos a todos los nodos ocupados, sin que ninguno quede esperando trabajo, y además nos queda redundancia.

{: .nota }
> La recomendación está en la sección 3.5 del paper, *Task Granularity*, y ahí los dos motivos aparecen enunciados con precisión: que cada worker haga muchas tareas distintas mejora el **balanceo de carga dinámico** —que es lo de tener a todos ocupados— y además **acelera la recuperación ante la caída de un worker**, porque las muchas tareas de map que ese worker había completado se pueden repartir entre todas las demás máquinas en vez de recaer sobre una. El paper también da la cota práctica que la clase no menciona: el master tiene que tomar del orden de M+R decisiones de scheduling y mantener del orden de M×R estado en memoria, a razón de aproximadamente **un byte por cada par de tarea map y tarea reduce**. Con los mil mappers del ejemplo y, digamos, mil reducers, eso es del orden de un megabyte de estado en el master — una cantidad despreciable, y de ahí que la granularidad fina resulte tan barata.
>
> Los números concretos con los que trabajaban dan la escala de cuánto quiere decir "mucho más grande". El paper dice que suelen ejecutar computaciones con **M = 200.000 y R = 5.000 sobre 2.000 máquinas worker**: son **cien tareas de map por máquina**. Y explica cómo eligen cada uno: M se elige para que cada tarea individual quede en unos 16 a 64 MB de input —el mismo rango que los splits de la sección 3.1— porque así la optimización de localidad que vamos a ver en la sección 5 rinde al máximo; y R se elige como un múltiplo pequeño de la cantidad de máquinas que se espera usar. R además queda acotado por otra razón: el output de cada tarea de reduce termina en un archivo separado, así que R es la cantidad de archivos de salida.

Lo que contamos con M y con R, entonces, son jobs lógicos: unidades de trabajo que eventualmente van a llegar y se van a ejecutar en alguno de esos nodos físicos. Quién se encarga de asignarlos a nodos físicos para que terminen ejecutándose es una pregunta que vamos a contestar más adelante, con la arquitectura del sistema.

Aparece una pregunta natural: si un nodo va lento, ¿se le puede reasignar el trabajo? Adelantemos la respuesta, aunque después volvamos sobre ella. Puede ocurrir que un mismo job se ejecute en varios nodos al mismo tiempo, por redundancia. Si existe un coordinador —y vamos a ver que existe— y detecta que un nodo está demasiado lento y no progresa, puede enviarle el mismo job a otro nodo de forma preventiva, para que lo empiece en paralelo. Termine primero uno o el otro, no representa un problema: al final vamos a tener dos versiones iguales del mismo trabajo. Por qué eso no compromete el resultado se entiende cuando llegamos a la tolerancia a fallas, que está pensada precisamente para esto.

## El reparto: hash(k) % R

Entre esas dos fases hay una fase intermedia, y tiene nombre propio: se la llama *shuffle*. La traducción que conviene tener presente es "el reparto", porque eso es literalmente lo que hace.

Vayamos a un ejemplo concreto, uno con tres mappers y dos reducers. Tres mappers implican, para empezar, tres jobs de map. Podemos imaginarlos dibujados uno al lado del otro, como si se hubieran ejecutado todos al mismo tiempo, aunque en realidad se ejecutaron en momentos distintos: lo que importa no es cuándo comenzó cada uno, sino que los tres terminan de ejecutarse. Y del otro lado tenemos dos reducers, que vamos a llamar R1 y R2.

Lo que va a terminar ocurriendo es esto. Las claves que el mapper 1 va generando las va a tener que enviar, cada una, o a R1 o a R2: va a elegir cuáles envía a uno y cuáles al otro. Y lo que ocurre siempre —salvo con un input demasiado pequeño, uno que no genere más de una o dos claves; con un dataset normal, siempre— es que de cada mapper van a salir claves para los dos reducers. Enseguida vamos a ver por qué salen para los dos, pero la imagen es esta: M1 les envía a los dos, M2 les envía a los dos, y M3 también les envía a los dos. Ese conjunto de flechas cruzadas es el shuffle.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    tres mappers mandándole cada uno a los dos reducers, con las flechas de cada mapper en un color distinto, y la llave que rotula el conjunto como el shuffle
    <span class="figura-ref">notas pág. 4, fig. 1 / pizarra pág. 7</span>
  </figcaption>
</figure>

Lo que esa fase está haciendo se ve mejor si lo dibujamos de otra manera. Supongamos que el universo entero de claves intermedias es K1, K2, K3, K4, K5 y K6. Vale preguntarse qué son esas claves en el ejemplo de contar palabras, qué valores adoptan K1 y K2: cada una de ellas es una de las palabras del diccionario, y el universo de claves es el universo de las palabras que aparecen entre todos los documentos. Cada una va a aparecer muchas veces: muchas veces K1, muchas veces K2, muchas veces K3.

Lo importante es una sola cosa: que todas las veces que aparece K1 vayan al mismo reducer, para que ese reducer pueda contarlas a todas.

Entonces lo que queremos es tomar ese universo de claves y dividirlo, de manera que nos queden dos conjuntos: uno con K1, K5 y K6, que es el que va a ir a R1, y otro con K2, K3 y K4, que es el que va a ir a R2.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el universo de claves intermedias K1 a K6 partido por la función de shuffle determinista en dos conjuntos, R1 = {K1, K5, K6} y R2 = {K2, K3, K4}
    <span class="figura-ref">notas pág. 4, fig. 2 / pizarra pág. 7</span>
  </figcaption>
</figure>

Hasta aquí resulta evidente: es todo ese universo, y algunas claves van para un lado y otras para el otro. Lo que no es evidente es quién decide. Quienes deciden son los mappers, y todos los mappers tienen que tomar la misma decisión, siempre. Si la clave K1 aparece en M1, en M2 y en M3, los tres tienen que decidir que K1 va al grupo de arriba, a R1. Con palabras concretas: si la palabra "hola" va a R1, los tres mappers tienen que enviarla a R1; y si la palabra "mundo" va al conjunto de abajo, los tres tienen que decidir lo mismo. Porque si se mezclan, el agrupamiento pierde todo sentido y el algoritmo no funciona.

¿Y con qué criterio se decide? En las implementaciones se puede elegir la función, pero no hay tantas alternativas y siempre se termina haciendo más o menos lo mismo, que es parecido a cómo funciona una hash table. Lo que necesitamos es una función de shuffle **determinista**, y ese es el punto central.

La función es la siguiente. Tomamos la clave intermedia y la pasamos por una función de hash. Los ejemplos conocidos son MD5 y SHA: se les entrega una entrada cualquiera y devuelven un número muy grande que parece aleatorio. No es aleatorio, precisamente porque es determinista, y siempre que se le da la misma entrada devuelve el mismo número. La propiedad que tiene que tener es que, sin conocer la entrada, no se pueda anticipar qué número va a salir: lo que sale está uniformemente distribuido.

A ese número se le aplica módulo, y módulo R, la cantidad de reducers que tenemos. En nuestro ejemplo, con dos reducers, eso da cero o uno. Hay entonces un ajuste de numeración que conviene hacer explícito, porque es una fuente real de confusión: a los reducers los venimos llamando R1 y R2, pero el módulo R devuelve valores que van de 0 a R−1, así que hay que leer el 0 como R1 y el 1 como R2.

Con eso, todos los mappers pueden decidir a qué lugar enviar cada clave. Cuando comienza el algoritmo, todos tienen que estar de acuerdo en hacer exactamente esto mismo, porque de lo contrario no funciona.

Cabe preguntarse si el shuffle es simplemente una función de hash o si hay algo más. No hay nada más: es una función de hash y un módulo. Es exactamente lo mismo que usa una hash table para decidir a qué bucket termina yendo cada clave, y esos dos conjuntos en los que dividimos el universo son los buckets.

{: .nota }
> El paper coincide en las dos mitades de esto. En §3.1 dice que las invocaciones de reduce se distribuyen partiendo el espacio de claves intermedias en R pedazos con una función de partición, y da `hash(key) mod R` precisamente como ejemplo —el "por ejemplo" es del paper—, aclarando que tanto R como la función las especifica el usuario. Y en §4.1 confirma que `hash(key) mod R` es la función que viene por defecto y que tiende a producir particiones razonablemente balanceadas. Pero ahí mismo da el caso donde conviene otra, que es el contraejemplo de que "siempre se termina haciendo lo mismo": cuando las claves de salida son URLs y se quiere que todas las entradas de un mismo host caigan en el mismo archivo de salida, se usa `hash(Hostname(urlkey)) mod R`. O sea que se hashea no la clave entera sino la parte de la clave por la que se quiere agrupar. La libertad de elegir la función está justamente para eso.

---
