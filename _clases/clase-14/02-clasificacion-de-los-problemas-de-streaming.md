---
title: "2. Clasificación de los problemas de streaming"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 2
---

# 2. Clasificación de los problemas de streaming
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Antes de abrir la caja del medio, conviene clasificar los tipos de problemas que estos sistemas resuelven. La clasificación no está en el paper: es una manera de ordenar el terreno. De un lado los problemas fáciles, del otro los difíciles, y los separa un solo criterio.

## Procesamiento por elemento y join stream-table

Los problemas fáciles son los que se procesan por elemento, sin agrupar nada. Hay básicamente dos categorías.

La primera son los filtros: de un stream de eventos dejamos pasar algunos y otros no. Es fácil de implementar, e inclusive de distribuir. Si el Kafka de entrada tiene muchas particiones, cada nodo puede leer una e ir decidiendo, con una función booleana, si deja pasar el elemento. No tiene que recurrir a ningún otro lugar: con el elemento en la mano ya lo puede filtrar.

La otra son las transformaciones —un *transform*, o matemáticamente un *map*—. Llega un elemento, lo transformamos y emitimos uno o más elementos. La transformación puede ser más o menos difícil, pero la forma es siempre la misma: llega un registro, le calculamos algo, emitimos otro.

Lo único que vuelve fáciles a estas dos cosas es que no hay que agrupar distintos elementos del stream: procesamos elemento por elemento. Nada de lo que se decide sobre un elemento depende de otro, y por eso el trabajo se reparte tan cómodamente entre tantos nodos como particiones tenga la entrada.

Hay un caso de transformación que se suele llamar enriquecer el stream: combinarlo con información que está en una base de datos. Al sistema le llega un registro que puede ser simplemente un user ID, y lo que queremos emitir por el stream de salida es ese mismo user ID acompañado del nombre, la dirección o cualquier otro dato. Esos datos están en una base de datos, cualquiera sea el motor: Postgres, MySQL, la que haya. El sistema de streaming, por cada registro que llega, accede a la base, lee y emite.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    enriquecer un stream: el stream de user IDs entrando a la etapa que consulta la base de datos, y el stream de salida con el nombre y la dirección agregados
    <span class="figura-ref">notas pág. 2 / pizarra pág. 3</span>
  </figcaption>
</figure>

Eso también es fácil, con un matiz a retener: toda la dificultad es la performance. Para no saturar la base con consultas, el sistema va a tener que agrupar muchas queries y mandarlas en lote, en vez de que le lleguen de a una desde todos lados a la vez, o apoyarse en muchísimos cachés. Pero sigue operando registro por registro.

Y resulta muy útil como pieza de un pipeline más grande. Si otra etapa necesita esos datos de la base, podemos intercalar una etapa que enriquece el stream y se lo manda a otro stream para que haga otro tipo de análisis. La etapa que consulta la base es una sola, y el análisis posterior ya encuentra los datos adicionales dentro del propio evento.

Conceptualmente, lo que hicimos es un join *stream + table*, en una versión relajada del concepto, porque el stream no termina nunca y la tabla es más o menos fija. La analogía transmite bien la idea, y el problema sigue siendo relativamente fácil.

## Agregados temporales, event time y processing time

Ahora el problema se vuelve más difícil: los problemas difíciles son los agregados temporales. Con mentalidad de base de datos, el equivalente sería un *group by window*, donde la window es una ventana temporal: agrupamos las cosas por el timestamp que traen consigo.

Ejemplos concretos son los clics por segundo, o el gráfico de cómo evoluciona una palabra en las búsquedas. Empezamos la clase por el problema difícil porque los anteriores se pueden resolver sin demasiada ayuda: un filter o un transform no es tan complicado, inclusive en tiempo real. Este otro, en cambio, requirió pensarlo mejor.

La clave es una distinción que ya asomó: hay dos tiempos distintos. Pongamos un eje horizontal con el tiempo en que los eventos se procesaron, y un punto por cada evento: eso es el processing time. Y cada evento, como decíamos al principio, traía la query y una hora —las ocho en punto, por ejemplo—. A esa hora la llamamos event time.

El processing time es el tiempo de reloj en el que recibimos el evento y lo procesamos: el tiempo inevitable, el que avanza solo. El event time es el momento en que el evento se originó; es más bien una metadata que viene con el mensaje. Generalmente lo define el que genera el evento: le pone el sello de cuándo ocurrió y lo manda por el stream.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    los eventos dispersos sobre el eje de processing time, con uno de ellos etiquetado con su event time
    <span class="figura-ref">notas pág. 3 / pizarra pág. 3</span>
  </figcaption>
</figure>

Prácticamente siempre que agrupemos por ventana vamos a estar pensando, implícitamente, en el event time. Agrupar por processing time da información rota, porque depende de qué tan a tiempo nos lleguen los eventos. Lo que queremos es juntar todo lo que se originó entre las ocho y las ocho y un minuto: seguimos haciendo un group by window, pero sobre el event time.

El problema principal, sin el cual nada de esto sería tan terrible, es el out-of-order: que los eventos lleguen desordenados. Hay dos niveles. El desorden liso y llano: los eventos no llegan en secuencia monótona ascendente, y cuánto se desordenan depende de la fuente y de la velocidad a la que los procesamos. La subcategoría verdaderamente difícil es cuando llegan atrasados: a los diez minutos nos llega un evento tarde. Y eso se vuelve un problema de verdad cuando cae en una ventana que conceptualmente ya cerramos.

Ahí podemos hacer dos cosas, y solo dos: ignorarlos, o corregir la ventana emitiendo nuevamente un valor para ella. La elección depende de la implementación; el paper es lo suficientemente flexible como para permitir cualquiera de las dos. Son alternativas un poco redundantes, porque valen para cualquier problema en general: o se lo ignora o se lo corrige. Lo interesante es que el framework no nos fuerza a ninguna. Lo que sí hace todo MillWheel es minimizar al máximo la cantidad de eventos que llegan tan tarde como para caer en una ventana ya cerrada, y ese va a ser el punto central. Es un best effort: perfecto no lo vamos a lograr prácticamente nunca. Y vamos a ver que el framework resuelve además muchos otros problemas que tampoco son tan fáciles.

{: .nota }
> Conviene precisar en qué sentido el sistema minimiza el desorden, porque el paper es explícito. MillWheel no intenta reducir cuántos eventos llegan fuera de orden —al contrario, dice que los streams desordenados son la norma y que su mecanismo obvia todo requerimiento de monotonía estricta en las entradas—; lo que mantiene chico es la proporción de eventos que llegan *detrás* del punto de corte, y para esos el paper confirma las dos salidas de la clase con sus propios casos: Zeitgeist los descarta, y otros pipelines corrigen retroactivamente sus agregados. Cuánto se pierde por descartar está medido: alrededor del 0,001% de los registros. Akidau et al., VLDB 2013, §2, §4.5 y §5.2.

¿Cómo sería el out-of-order si procesáramos por lotes? En ese caso, el desorden no presenta ninguna dificultad. Volvamos a Britney. Si hacemos un agregado por minuto procesando el día entero, de las cero a las 23:59, no estamos obligados a cerrar ninguna ventana hasta terminar el lote. Generamos una ventana por minuto y metemos cada data point en su bucket. Es un ejercicio típico de un curso introductorio de algoritmos: un archivo con muchos data points, un hashmap, y contar cuántas cosas ocurrieron en el minuto uno, en el dos, y así. Si se procesa todo de una, no hay problema.

En stream processing, en cambio, el problema es justamente tomar la decisión. Si armamos una ventana de las ocho a las 8:01 y acaba de llegar un elemento, tenemos que poder decidir si fue el último de esa ventana: afirmar que ese es el punto de corte, que de ahí para adelante nunca nos va a llegar nada más para esa ventana. Solo entonces tenemos la certeza casi absoluta de que podemos cerrarla. Ese es el problema a resolver, y es difícil.

## Join stream-stream

Queda un tipo de join más, el difícil: stream-stream. Antes era un stream con una tabla; ahora es un stream con otro stream. Conceptualmente no es muy diferente. Tenemos un stream con muchos data points y otro, de otro color, con otros data points; cada uno es un Kafka, un canal de datos. Nuestro stream processing consume de los dos, arma ventanas de tiempo y después realiza el join. Solo cuando puede cerrar una ventana —cuando tiene la certeza de que no le va a venir ningún evento más viejo—, cierra la de uno, cierra la del otro, hace un join en memoria y emite un data point.

El ejemplo: uno de los streams es de push notifications, esos breves mensajes que aparecen en el teléfono, del tipo «alguien te está siguiendo en LinkedIn», después de los cuales el usuario se mete a la página. Queremos correlacionar las push notifications que mandamos con los accesos a la página, para ver si el mensaje convence al usuario de hacer clic. El otro stream es el de accesos a la app.

No hay forma fácil de correlacionarlos por afuera: el acceso a la página no trae data de la push notification que lo originó, así que hay que correlacionar por tiempo. En el primer stream tenemos el user ID del destinatario y un push ID, el identificador de la notificación; en el otro, el user ID y el path del sitio al que accede. El join emite el user ID, el push ID y el path.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el join stream-stream: el stream de push notifications y el de accesos a la app entrando a la misma etapa, y el registro correlacionado que sale
    <span class="figura-ref">notas pág. 3 / pizarra pág. 4</span>
  </figcaption>
</figure>

La correlación es por tiempo: hay que armar ventanas y ver, por ejemplo, si dentro de los cinco minutos de recibir la notificación el usuario accedió a la página. El ejemplo es de fabricación propia y algo inventado —quizás en la realidad haya forma de correlacionar las dos puntas directamente—, pero muestra la forma del problema. Y eso no es nada fácil. Por lotes es manejable; en tiempo real, hace falta un mecanismo nuevo para hacer el join entre streams.

---
