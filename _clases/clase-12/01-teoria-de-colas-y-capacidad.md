---
title: "1. Teoría de colas y capacidad"
parent: "Clase 12 — Memcache en Facebook"
nav_order: 1
---

# 1. Teoría de colas y capacidad
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Cuello de botella y modelo de colas

Hay un recurso que aparece siempre que se quiere escalar una base de datos, y que se suele combinar con todo lo que fuimos viendo: agregarle cachés. Vamos a ver primero por qué se justifica agregarlos, y después lo más interesante, lo que la gente suele tomar a la ligera y a lo que casi nunca le presta atención: la consistencia de los cachés.

Partimos de un dibujo que ya hicimos la vez pasada, el de Facebook. Facebook era inicialmente una aplicación web de las antiguas: dentro tenía un servidor HTTP —Apache o nginx, indistintamente—, el cliente se conectaba ahí, y ese servidor se conectaba internamente con una base de datos relacional, que en esa época bien podía ser MySQL; Postgres todavía no estaba tan difundido. Es la primera iteración que uno haría: una única máquina, con todo dentro.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    servidor web de una sola máquina — un cliente con una flecha HTTP hacia un recuadro que contiene Apache y, debajo, la base relacional
    <span class="figura-ref">notas pág. 1 / pizarra pág. 1</span>
  </figcaption>
</figure>

El primer paso para escalar esto, que vimos en las primeras clases, es escalar el servidor web. Ya no hay un solo cliente sino muchos, y adelante de todo se pone un load balancer. Los load balancers suelen ser máquinas de Cisco, con hardware dedicado y de costo elevado, pero conceptualmente son un componente de red común: podría ser una máquina con Linux y muchas placas de red para conectar los equipos hacia donde balancea; no hay nada más complejo que eso. Se pone adelante de varios servidores que, más que réplicas, son servidores stateless: no tienen estado, y por eso, si falla uno, se lo reemplaza por otro sin que nadie se entere. Todos ellos se conectan con la base de datos relacional.

Ya habíamos dicho que esa base, por ser relacional, es más difícil de escalar que la capa del medio. A la capa del medio se le agregan máquinas y funciona; con la relacional no, porque tiene discos rígidos, y ahí hay que usar las técnicas de las clases anteriores. La versión fácil es seguir con una única base; a lo sumo, con una réplica, un primary y un secondary, de la que se puede leer de uno o del otro. Pero eso ya va más allá de lo básico, así que dejemos una sola base.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el escalado — cliente, load balancer, tres servidores HTTP stateless y una única base de datos relacional
    <span class="figura-ref">notas pág. 1 / pizarra pág. 1</span>
  </figcaption>
</figure>

Ahora el cuello de botella se corrió de lugar: por más servidores HTTP que pongamos adelante, todos terminan accediendo a la misma base, que termina siendo el cuello de botella. Ahí es donde vamos a poner cachés. No para acelerar el acceso, sino para darle más potencia, entre comillas, a la base de datos. Las comillas están a propósito, y en breve vamos a ver a qué nos referimos.

Antes conviene ver cómo se modela matemáticamente la capacidad de estos componentes para recibir requests. Lo que sigue es una breve introducción a la teoría de colas, simplificada, con solo lo necesario para esta clase; quien curse Simulación la va a ver con mucha más profundidad. La idea es quedarnos con un par de ideas básicas que nos den intuición sobre cómo se sobrecargan los servidores, porque un servidor que recibe requests es básicamente un sistema de colas.

¿Qué significa eso? Modelar un sistema al que le llegan entradas —requests, para mantener nuestro lenguaje— y del que salen responses. Los requests pueden ser pedidos a la base y los responses el resultado de la query. Al sistema lo dibujamos como un círculo abstracto a propósito, porque dentro puede haber cualquier componente. Puede ser todo el conjunto que acabamos de dibujar: entonces los requests llegan de los clientes y las respuestas vuelven a ellos. O podemos estudiar solo la base de datos: entonces los requests son los que le llegan a ella y las respuestas las que devuelve. La misma herramienta sirve para las dos lecturas, y esa es la ventaja de dejar el círculo sin contenido.

Hay tres parámetros con los que vamos a jugar, y adelantamos adónde queremos llegar: entender qué pasa cuando le ponemos al sistema un caché mucho más rápido, y cómo lo mejora. El primero es λ(t), la tasa de entradas, en requests por segundo; si se quiere, la derivada de los requests. El segundo es δ(t), la tasa de salidas. Y el tercero, la clave de todo porque es el que nos dice cuánta capacidad le queda al sistema para seguir atendiendo gente, es N(t): la cantidad de clientes dentro del sistema.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el sistema como caja negra — un círculo rotulado &quot;sistema&quot;, flecha entrante de requests con λ(t), flecha saliente de responses con δ(t), y N(t) dentro
    <span class="figura-ref">notas pág. 1 / pizarra pág. 1</span>
  </figcaption>
</figure>

Hay una sutileza. El sistema es abstracto, y también lo es qué significa estar dentro. Pueden ser requests que se procesan en paralelo: llegan, se procesan y se devuelven. O puede ser algo secuencial, con una cola dentro. Teoría de colas no dice necesariamente que tenga que haber una cola FIFO; podemos tener una cola de la que se toman elementos que después se procesan en paralelo. Para nuestro análisis, N(t) es la cantidad de gente que entró y está siendo procesada, o esperando serlo, y que eventualmente va a salir. Que no importe cuál de esas formas sea es lo elegante de la teoría: buscamos relaciones entre esas tres variables que no dependen de cómo esté armado el sistema por dentro.

Hay una observación intuitiva que resulta muy razonable. Si entran cosas más rápido de lo que salen, se van a acumular dentro. Si el sistema fuera una cola, la veríamos llenarse: cada elemento que llega se apila detrás de todos los que ya estaban. Y eso se traduce en algo muy concreto: esa gente va a tener que esperar cada vez más.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el sistema que se llena — un círculo con una cola dentro y elementos acumulándose a la derecha cuando entran más de los que salen
    <span class="figura-ref">notas pág. 2 / pizarra pág. 2</span>
  </figcaption>
</figure>

Formalmente, la derivada de la cantidad de gente dentro es la diferencia entre las dos tasas: `dN(t)/dt = λ(t) − δ(t)`. Para simplificar vamos a estudiar el caso estable, en el que entra la misma cantidad de gente que sale. Si `λ = δ`, esa derivada vale cero y `N` es constante. Es una simplificación grande, pero nos va a servir para varias cosas.

Lo importante es esto: si se desbalancea la capacidad del sistema para largar gente hacia afuera —en definitiva, su capacidad para despachar pedidos—, las cosas se empiezan a acumular, que es justo lo que no queremos. Y esa capacidad es lo que queremos calcular.

## Ley de Little

La fórmula grande de este asunto, la que nos va a servir para justificar el caché, se llama ley de Little. Relaciona tres cantidades y es muy simple: hasta obvia, si uno se detiene a pensarla. Hay demostraciones matemáticas, pero no las vamos a ver; nos alcanza con entender qué dice y saber usarla.

Las tres cantidades son promedios en el tiempo. Los requests no entran a un rate constante, sino que fluctúan; pero a lo largo del tiempo, el promedio de clientes dentro del sistema es lo que llamamos `L`. La segunda es λ, la misma de antes: la tasa de arribos. La tercera es `W`, que no habíamos nombrado: el tiempo que cada request pasa dentro del sistema, cuánto tarda en procesarse. La ley dice que se relacionan de la manera más simple imaginable: `L = λW`.

Un ejemplo fácil muestra que funciona. Pensemos en un café, un Starbucks, dibujado como una casa, y queremos calcular cuántas sillas poner dentro. Tenemos dos datos: la tasa de arribo, 45 personas por hora; y el tiempo de permanencia, 25 minutos por persona, contando todo lo que hace entre que llega, hace la cola, pide el café, se sienta y se lo toma. Lo que no sabemos es cuánta gente hay en promedio dentro, que es exactamente la `L`. Esa es la capacidad que tiene que tener el local.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el café — una flecha λ entrando a una casa, con λ = 45 personas/hora, W = 25 min y la incógnita L
    <span class="figura-ref">notas pág. 2 / pizarra pág. 2</span>
  </figcaption>
</figure>

La cuenta sale directa de la fórmula, pasando los minutos a horas para que cierren las unidades: `45 p/h × 25/60 h = 18,75 personas`. Con unas 25 sillas estaríamos bien. Así se ve la potencia de la ley: estas relaciones cuestan razonarlas de entrada, pero analizadas con un poco de detenimiento resultan muy lógicas. Lo que hicimos fue relacionar las tres cantidades, y con eso vamos a pensar varios ejemplos más.

Cada cantidad tiene un correlato directo en el sistema que nos interesa. La cantidad de clientes en el sistema la relacionamos típicamente con la cantidad máxima de conexiones que podemos soportar: si tenemos un pool de conexiones, esas conexiones son las sillas del café. La tasa de arribos es lo mismo de antes, pero aquí le decimos throughput: requests por segundo. Y el tiempo de procesar cada query, si miramos una base de datos, o cada request si miramos otra cosa, es la `W`. Combinándolas podemos calcular, con una multiplicación y un despeje, cuánto tiene que ser la velocidad promedio de la query o el tamaño del thread pool. Y hay una asimetría importante: la tasa de arribos es el único parámetro que no controlamos. Si sabemos que vamos a tener tantos requests por segundo, no queda otra que tocar las otras dos variables.

Un segundo ejemplo, más parecido a lo nuestro: un consultorio médico, con seis pacientes dentro en promedio y diez por hora llegando. Esos seis son los que esperan y los que se atienden combinados en un solo número; en un momento vamos a ver por qué. Y como estamos en equilibrio, si llegan diez por hora salen diez por hora. Ahora la pregunta va al revés: nos dan la cantidad de personas dentro y no sabemos cuánto tarda cada una. Es lo que cualquiera se pregunta al ir al médico: cuánto voy a tardar. Despejamos: `W = L/λ`, y la cuenta es `6/10 = 0,6 horas`, unos 36 minutos. Lo que importa es la relación entre las variables y cómo se determinan entre sí. Comparado con lo que se aprende en física, esto es muy sencillo.

Ahora lo verdaderamente interesante, que ya anticipamos: no importa la estructura interna del consultorio —cuántos médicos hay, si hay cola o no, cuántos pacientes se atienden en paralelo—. Para verlo alcanza con probar arquitecturas distintas con los mismos números. Una forma posible es una cola de cinco personas y después un consultorio con un solo médico. Con diez pacientes por hora y seis personas en total dentro, cinco esperando y una siendo atendida, la cuenta da 36 minutos para cada uno.

Pero podría ser un sistema completamente distinto: seis consultorios en paralelo, cada uno con su médico, y ninguna cola. Los pacientes llegan y se atienden enseguida. Con diez pacientes por hora y seis personas en el sistema, ahora en paralelo, la ley de Little da exactamente lo mismo: 36 minutos. Lo que cambia por completo es la interpretación. Aquí cada médico dedica 36 minutos a su paciente: una atención muy detenida. En el sistema anterior el médico atendía bastante más rápido, porque esos 36 minutos se repartían entre la fila de espera y la consulta propiamente dicha.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    las dos variantes del hospital — a la izquierda una cola de cinco pacientes seguida de un único consultorio; a la derecha seis consultorios en paralelo sin cola; ambas con 36 minutos
    <span class="figura-ref">notas pág. 3 / pizarra pág. 3</span>
  </figcaption>
</figure>

Lo que buscamos es la intuición, no la teoría matemática. Para afirmarla falta una tercera versión, más parecida a cómo funcionan de verdad los sistemas: dos consultorios y adelante una fila de cuatro personas. Los parámetros globales siguen siendo los mismos, a propósito, para que se note que el resultado no depende de cómo esté acomodado el sistema por dentro. Ahora hay una combinación de dos sistemas: el de la cola y el de los médicos, conectados entre sí, con la particularidad de que la λ que sale de uno es la que entra al otro. Esa λ es un parámetro común a los dos.

Si en algún momento los médicos se enlentecen, la λ que sale de ellos es más chica que la que entra, y la cola crece. Si se aceleran, la cola se reduce. Nuestro caso es el de una mañana en la que vinieron muchísimos pacientes, pasó eso, y después quedó todo estable, pero con una cola fija adelante.

Con esa descomposición podemos calcular varias cosas. La `L` completa es seis. De esas seis, dos están en los consultorios, porque son dos: `Lm = 2`. En la cola quedan `Lc = 4`. Y la λ vale diez en todo el recorrido: entran diez por hora, salen diez de la cola, entran diez a los médicos y salen diez del hospital. Aplicando la ley a cada subsistema: `Wc = 4/10 = 0,4 horas` de espera en la cola y `Wm = 2/10 = 0,2 horas` siendo atendido.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la descomposición en dos subsistemas en serie — λ = 10 p/h entrando a una cola de cuatro, después dos consultorios, y λ saliendo; con Lc, Wc, Lm y Wm rotulados
    <span class="figura-ref">notas pág. 3 / pizarra pág. 3</span>
  </figcaption>
</figure>

Los detalles de esta cuenta no importan tanto. La idea con la que hay que quedarse es que no importa la estructura interna del sistema, porque la ley permite verlo desde afuera. Volviendo a nuestro problema, eso significa que no vamos a tener que saber cómo funciona la base de datos por dentro. Solo tenemos que saber cuánto tarda un request; y que si lo aceleramos, obtenemos más throughput.

---
