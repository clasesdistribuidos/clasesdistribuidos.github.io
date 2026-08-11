---
title: "4. El mapper y el reducer por dentro"
parent: "Clase 2 — MapReduce"
nav_order: 4
---

# 4. El mapper y el reducer por dentro
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Ya sabemos cómo se divide el universo de claves entre los reducers. Falta abrir los nodos y observar qué ocurre adentro: qué archivos escribe un mapper, qué archivos lee un reducer, y qué tiene que hacer cada uno con ellos.

## `M1_R1`, el sort que se vuelve merge

Miremos entonces un mapper por dentro, con la diferencia marcada desde el principio: no la función map, sino el mapper —el nodo cuando está funcionando como mapper—. Seguimos con el ejemplo anterior, donde R vale 2.

Lo que hay ahí es un recorrido. Entra un input. Ese input se le pasa a la función map que escribió el programador, y esa función emite una secuencia de claves y valores. Esa secuencia pasa por la función de hash y el módulo, todo lo que acabamos de ver. Y de ahí se generan localmente dos archivos, porque a esta altura el mapper ya está guardando en su disco local: un archivo y otro archivo.

Llamemos mapper 1 a este nodo, asignémosle ese identificador. Entonces al primero de esos archivos lo llamamos `M1_R1` y al segundo `M1_R2`. Lo que quiere decir esa nomenclatura se deduce con facilidad: `M1_R1` es lo que el mapper 1 está preparando para enviarle a R1, y `M1_R2` es lo que está preparando para enviarle a R2. Eventualmente cada uno va a terminar yendo a su destino: el primero al reducer 1, el segundo al reducer 2.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el mapper 1 por dentro con R=2 — el input entra a la función map, la tira de pares pasa por el hash y el módulo, y se escriben en disco local los dos archivos M1_R1 y M1_R2, con flechas punteadas hacia el reducer 1 y el reducer 2
    <span class="figura-ref">notas pág. 4, fig. 3 / pizarra pág. 8</span>
  </figcaption>
</figure>

Pasemos ahora a la perspectiva del reducer, y tomemos el reducer 1. Vale preguntarse cuántos archivos va a recibir. La respuesta es tantos como mappers haya, y en nuestro ejemplo son tres: va a recibir el `M1_R1`, el `M2_R1` y el `M3_R1`. Todo lo que era para R1 se le envía por ahí.

Lo que ese reducer tiene que hacer con esos tres archivos es agrupar todas las claves. Porque lo que va a ocurrir —no necesariamente, pero es el caso común— es que va a tener instancias de la misma clave en los tres. El razonamiento se ve mejor con una palabra concreta: la palabra "hola", que es muy común, va a aparecer en documentos que se le enviaron al mapper 1, va a aparecer en documentos que se le enviaron al mapper 2 y va a aparecer en documentos que se le enviaron al mapper 3. Los tres emitieron pares con esa clave, y los tres los pusieron en su archivo para R1.

Si lo que queremos es que queden juntas todas las instancias de una misma clave, lo que hay que hacer es un **sort**. Un sort de todos los archivos que el reducer está recibiendo, juntos, como si fueran uno solo. Y eso ordenado es lo que se le termina enviando a la función reduce, con cierta mediación de la implementación en el medio, de manera tal que reduce recibe la clave y ya recibe una lista con los valores. Y ni siquiera es una lista: generalmente es un iterador, por cuestiones de memoria. El reduce, a su vez, produce un output, un archivo.

{: .nota }
> El paper confirma las tres cosas y agrega dos. Sobre el iterador, dice textualmente que los valores intermedios se le pasan a la función reduce del usuario mediante un iterador, y que eso es lo que permite manejar listas de valores demasiado grandes para caber en memoria — o sea que la razón es exactamente la que da la clase. Sobre el sort, el paper da además la razón complementaria: hace falta porque a una misma tarea de reduce le caen típicamente **muchas claves distintas**, no solo muchas apariciones de una. Y agrega el caso extremo que la clase no menciona: si la cantidad de datos intermedios no cabe en memoria, se usa un **sort externo**. La segunda cosa que agrega es una consecuencia valiosa del sort, en §4.2: MapReduce **garantiza** que dentro de una partición los pares se procesan en orden creciente de clave, lo que hace que el archivo de salida de cada reducer quede ordenado. Eso importa cuando el formato de salida tiene que soportar búsquedas eficientes por clave, o simplemente cuando a quien consume el resultado le conviene tenerlo ordenado.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el reducer 1 por dentro — los tres archivos M1_R1, M2_R1 y M3_R1 entrando a un sort, de ahí al reducer y de ahí al output
    <span class="figura-ref">notas pág. 5, fig. 1 / pizarra pág. 8</span>
  </figcaption>
</figure>

El sort está ahí para que ocurra algo muy concreto, y se ve mejor en un ejemplo pequeño. Supongamos que lo que llega es (a,1), (b,1), (a,1), (c,1) y (b,1), en ese orden mezclado. Si lo ordenamos por la clave, nos queda (a,1), (a,1), (b,1), (b,1) y después (c,1). Al hacer el sort quedaron todas agrupadas. Y una vez que están agrupadas es muy sencillo, con un mecanismo simple de la implementación, lograr que en lugar de aparecer muchas veces la clave a con un uno cada vez, aparezca una sola vez la clave a y todos los unos juntos. Esa es la interfaz que ve el programador, y es lo que ocurrió al hacer el sort.

Y aquí aparece una optimización, porque todo esto se simplifica muchísimo si el sort ya viene hecho. Si cada mapper ordenó por la clave el resultado parcial que después va a reunir el reducer, entonces el trabajo del reducer se transforma simplemente en un **merge**: toma esos archivos, que ya sabe que vienen ordenados, y hace un merge de todos los valores para generar el output. Es una optimización muy deseable, y estos sistemas la suelen tener.

Se puede incluso ir un paso más allá. El mapper no está obligado a emitir un único archivo por reducer: puede tener un buffer en memoria donde va acumulando pares, ordenarlos cuando se llena, emitir un archivo con eso, y así ir generando varios. Todos van al reducer, que hace el merge entre más entradas: es exactamente el mismo trabajo.

## Reducers abstractos y los M×R archivos

Aquí cabe una objeción, y conviene plantearla en toda su fuerza. Si cada mapper sabe de por sí a qué reducer le va a hablar, ¿no los estamos acoplando demasiado? Le estamos indicando al mapper con qué reducer debe comunicarse, y le estamos dando la responsabilidad de decidir qué claves le envía a cada uno. ¿No debería el mapper ser un poco más agnóstico? Le llegan sus datos, hace lo que tenga que hacer, escribe su archivo, y ahí termina su trabajo; y después habrá otro nodo —el coordinador, presumiblemente, o quien fuera— que se encargue del resto, del agrupamiento y del sort.

La respuesta empieza por precisar qué es lo que el mapper efectivamente sabe. La cantidad de mappers y la cantidad de reducers son parámetros de la ejecución del MapReduce. Cuando se inicia un job, además de dar la función map y la función reduce, se indica cuántos mappers se van a usar —cuántos inputs va a haber— y cuántos reducers se quieren usar.

Lo que no se indica en ninguna parte es la ubicación física de esos reducers. Es lo que veníamos anticipando: los reducers son jobs abstractos. Con cinco reducers, lo único que se sabe es que van a existir el reducer 0, el 1, el 2, el 3 y el 4. Eso, y nada más que eso, es lo que saben los mappers: cuando dividen su salida, dividen entre esos números.

El resto lo hace el coordinador. Cuando un mapper termina, le avisa al coordinador. Y cuando el coordinador ve que todos terminaron, elige un nodo cualquiera y le asigna el papel de reducer 3, digamos, indicándole de qué mappers debe tomar los datos de salida. Ese reducer va entonces a esos mappers y obtiene los datos.

Ahí está la respuesta a la objeción. No hay acoplamiento directo entre los nodos mappers y los nodos reducers. Al mapper se le indica solamente cuántos R hay, y con eso separa internamente sus outputs, o los deja preparados para que alguien los recoja; quien pone en correspondencia esos jobs con nodos físicos es el coordinador, que está en el medio de los dos. Y hay algo de fondo que ahora se vuelve nítido: el nodo no es intrínsecamente un mapper ni un reducer. El nodo es un nodo.

{: .nota }
> El paper dice esto mismo con una palabra que vale la pena retener, y agrega el mecanismo exacto. En §3.2 llama al master **el conducto** por el cual la ubicación de las regiones de archivo intermedias se propaga desde las tareas de map hacia las tareas de reduce: por cada tarea de map completada, el master guarda las ubicaciones y los tamaños de las R regiones intermedias que esa tarea produjo, y esa información la va recibiendo a medida que las tareas de map terminan. El detalle que la clase no da es que el master no espera a que se le pregunte: **empuja esa información de forma incremental** a los workers que ya tienen tareas de reduce en curso. Y hay un cierre elegante del recorrido de la clase en cómo el reducer levanta los datos: según §3.1, el worker de reduce, una vez notificado de las ubicaciones, usa **remote procedure calls** para leer los archivos de los discos locales de los workers de map. O sea que el mecanismo de la era 2 es el que está haciendo el trabajo aquí abajo.

El intercambio completo, expresado como un diálogo entre ambos, es este. El nodo le pregunta al coordinador si hay trabajo para él, y el coordinador le responde que sí: será un mapper, ese es su input y debe generar dos salidas. Ese nodo ejecuta entonces la función map, genera sus dos archivos y en principio los deja donde están. Después le informa al coordinador que ya terminó, que es el mapper 1 y que su resultado está listo. Cuando el coordinador ve que todos los mappers terminaron, toma un nodo y le asigna el papel de reducer 1, indicándole qué archivos debe ir a buscar —el `M1_R1`, el `M2_R1`, y así, cada uno en el lugar donde quedó—. E incluso, si ese reducer falla, le asignará ese mismo papel a otro nodo y le indicará todos los datos que debe consumir. Todo esto es ya la arquitectura del sistema, que es justamente lo que sigue.

Queda una última consecuencia, y es de las que vale la pena calcular mentalmente. Si la cantidad de mappers y la de reducers son parámetros del sistema, decir que vamos a tener M mappers y R reducers equivale a decir que vamos a tener **M×R** archivos intermedios. Como mínimo: un mapper puede producir más de un archivo por reducer, como acabamos de ver con el buffer en memoria, pero dejemos esa complicación de lado. Las dos cantidades se multiplican entre sí, así que con los mil mappers del ejemplo de más arriba y otros mil reducers eso da **un millón de archivos intermedios** para un solo job. Y lo que MapReduce resuelve como sistema distribuido —su gran aporte— es exactamente eso: el reparto entre esos mappers y esos reducers.

---
