---
title: "2. Por qué existe MapReduce"
parent: "Clase 2 — MapReduce"
nav_order: 2
---

# 2. Por qué existe MapReduce
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Con la cronología en la mano ya podemos hacer la pregunta que sigue: ¿qué es lo que resolvía MapReduce? Varios de los papers de esa era resuelven el problema de guardar datos; este resuelve otro, que es el del cómputo. Dicho de la manera más directa posible, lo que queremos hacer con MapReduce es dividir un proceso de cómputo entre muchas CPUs.

## El origen: transformación y agregación

El origen es lo que explica la forma que MapReduce terminó teniendo. Uno de sus dos creadores es Jeff Dean, que hoy es una figura muy visible y una referencia central de la inteligencia artificial, pero que ya en esa época era importante.

Dean publicó hace poco, en febrero, una entrada en la que relata el origen de MapReduce: por qué se inventó. Y lo que dice ahí coincide con lo que ya se sabía por otras fuentes. Lo que tenían que hacer, cuenta, era reconstruir el pipeline que indexaba la web. El contexto concreto es lo que le da peso al problema: esto era principio de los 2000, no disponían de máquinas especialmente potentes, y querían indexar la web nuevamente, entera, con las máquinas que había en ese momento.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la publicación de Jeff Dean contando el origen de MapReduce, con su traducción al español al lado
    <span class="figura-ref">pizarra pág. 3</span>
  </figcaption>
</figure>

Y ahí aparece la idea más brillante, que es justamente la que hoy damos por sentada: la separación entre transformar y agregar nos resulta natural porque la aprendimos ya formulada, pero a alguien se le tuvo que ocurrir por primera vez. Se dieron cuenta de que muchos de esos algoritmos que tenían que implementar tenían todos la misma forma. Matemáticamente hablando, si se quiere, siempre era una transformación y una agregación. Y los algoritmos más complicados muchas veces se podían armar como una cadena de eso mismo: transformación, agregación, transformación, agregación. Un MapReduce podía ser el input de otro —la salida de uno como entrada del siguiente—, y con esa cadena se construían muchísimos algoritmos. A las transformaciones las llamaron mappers, y a las agregaciones, reducers.

{: .nota }
> El paper es explícito sobre este origen, y además pone los números que confirman ese encadenamiento. Su sección 7.1 cuenta que el sistema de indexación de la búsqueda web de producción de Google fue completamente reescrito para usar MapReduce, y que ese sistema consiste en una secuencia de **entre 5 y 10 operaciones de MapReduce** encadenadas, en unas **3.800 líneas de C++**. O sea que el caso que motivó el diseño no es solo el ejemplo de una charla: es el primer usuario del sistema, y tiene exactamente la forma de cadena que describe el razonamiento.

La parte difícil de todo eso era otra: cómo se distribuía. Ese patrón en sí no nos dice nada al respecto. Reconocer que un algoritmo tiene la forma de una transformación seguida de una agregación no dice una palabra sobre cómo repartir ese trabajo entre muchas máquinas. Y aquí está el reparto de tareas que hace MapReduce, que es la idea central: si los programadores hacían la parte sencilla —entre comillas—, que es identificar esa estructura dentro de los problemas que tenían, la parte difícil la podía hacer un sistema que la distribuyera automáticamente. Porque esa parte difícil era muy difícil, o por lo menos requería expertos en sistemas distribuidos.

Y no tenían tantos expertos en sistemas distribuidos. Tenían, por un lado, a quienes desarrollaban los algoritmos, y por otro, a los expertos. MapReduce era una forma de conectar a los dos grupos: unos escriben el mapper y el reducer, y el sistema, que hicieron los expertos una sola vez, se ocupa del resto.

Esa distribución es transparente, pero solo hasta cierto punto. El sistema es distribuido y la distribución queda prácticamente escondida, sí. Pero no es posible tomar cualquier algoritmo, ponerlo en MapReduce y que funcione. Quien haya usado MapReduce alguna vez tuvo que pensar en términos de mappers y de reducers, y eso es lo que se adaptó al sistema: hubo que adaptarse a lo que el sistema puede absorber. De ahí que la transparencia aquí sea parcial.

El paper de todo esto explica directamente cómo funciona MapReduce, y lo escribieron ese mismo Jeff Dean y Sanjay Ghemawat. Son una dupla conocida, y hay sobre ellos un artículo del New Yorker titulado "la amistad que hizo grande a Google", ilustrado con una caricatura de ambos; la referencia completa está en la nota al pie, y el acceso puede requerir suscripción. No tiene relación directa con la materia, pero es interesante como retrato de dos ingenieros trabajando en las eras iniciales de los sistemas distribuidos, en un modo de trabajo muy diferente del actual, y más aún en el contexto de la inteligencia artificial.

{: .nota }
> El artículo es *The Friendship That Made Google Huge*, de James Somers, publicado en The New Yorker el 10 de diciembre de 2018. El subtítulo describe justamente lo que lo hace un retrato singular: programando juntos en la misma computadora, Dean y Ghemawat cambiaron el rumbo de la empresa y de internet. El paper de la clase es Jeffrey Dean y Sanjay Ghemawat,* MapReduce: Simplified Data Processing on Large Clusters*, OSDI 2004.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la caricatura del New Yorker de Jeff Dean y Sanjay Ghemawat que ilustra el artículo sobre la dupla
    <span class="figura-ref">pizarra pág. 3</span>
  </figcaption>
</figure>

## El modelo de programación y la clave intermedia

El paper explica el modelo de programación con todo detalle, así que no hace falta reproducirlo entero: alcanzan algunas ideas básicas. El objetivo del modelo es que quien programa se dedique a pensar una función map y una función reduce para el cálculo que quiera hacer, y que MapReduce maneje automáticamente la distribución.

El ejemplo del paper es el que quizás ya conozcamos, porque es el "hola mundo" de MapReduce y el más simple que existe: contar palabras. Tenemos un corpus de documentos grandes y queremos ver cuántas veces aparece cada palabra en él.

La función map tiene que tomar cada documento y, por cada ocurrencia de cada palabra que encuentra, emitir un par: la palabra y un uno. Después el reducer —el agregador, si se lo quiere llamar por lo que hace— agrupa todas las ocurrencias de esa palabra y suma todos esos unos. Lo que queda acumulado ahí es el resultado. Escrito como lo escribe el paper:

```
map(String key, String value):
  // key: document name
  // value: document contents
  for each word w in value:
    EmitIntermediate(w, "1");

reduce(String key, Iterator values):
  // key: a word
  // values: a list of counts
  int result = 0;
  for each v in values:
    result += ParseInt(v);
  Emit(AsString(result));
```

La función map recibe una clave y un valor, que aquí son el nombre del documento y su contenido; recorre las palabras de ese contenido y, por cada una, llama a `EmitIntermediate` con la palabra y el uno como texto. La función reduce recibe una clave, que es una palabra, y un iterador sobre la lista de conteos; inicializa un acumulador en cero, convierte cada valor a entero, lo suma, y emite el total. Ninguna de las dos menciona máquinas ni redes.

Y ahí está el concepto más importante de todo esto: ese primer valor del par que emite el mapper. Eso es lo que podemos llamar una **clave intermedia**, y es lo que MapReduce va a usar para agrupar los datos entre sí.

En este ejemplo la entrada ya son archivos, y cada archivo alimenta a uno de los mappers. Digamos tres, y llamémoslos input 1, input 2 e input 3: cada uno, conceptualmente (más adelante vamos a ver en detalle cómo lo hace en la realidad), entra en un mapper, que no es más que la función map directamente, y cada uno emite una secuencia de pares.

Hagámoslo con letras en lugar de palabras, que es más breve de escribir. El primer input emite (a,1) y (b,1). En un caso real serían miles de pares, uno por cada palabra del documento; supongamos que tenía solo esas dos. En el input del segundo mapper estaba únicamente la palabra b, así que emite (b,1) una sola vez. Y en el tercer documento vuelve a aparecer la a, la b no aparece, y en cambio aparece la c: emite (a,1) y (c,1). Así nos queda una mezcla de palabras.

Lo que tiene que hacer el reducer —y esta es la parte más interesante del algoritmo— es reunir todas las a de todos los mappers y enviárselas a una función reduce; agrupar todas las b y enviarlas a otro reduce; y agrupar todas las c y enviarlas a un tercero, aunque la c aparezca una sola vez. Los resultados: a vale 2, b vale 2 y c vale 1.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el flujo del modelo — tres inputs, cada uno a un mapper, las tiras de pares intermedios (a,1)(b,1) / (b,1) / (a,1)(c,1), y el agrupamiento por clave intermedia hacia los reduces, con los resultados (a,2) (b,2) (c,1)
    <span class="figura-ref">notas pág. 3, fig. 1 / pizarra pág. 6</span>
  </figcaption>
</figure>

Ese agrupamiento se hace por la clave intermedia, y la clave intermedia es siempre el primer valor del par ordenado que se emite en cada caso.

De ahí se puede inferir algo sobre la otra clave, la de entrada, que las implementaciones que hayamos usado alguna vez seguramente simplifican. Si bien el mapper recibe una clave y un valor, esa clave de entrada no es tan importante: no se usa para mucho. En el conteo de palabras es el nombre del documento, y el cálculo no la utiliza en ningún momento. La clave que importa es la otra, la que el mapper emite. Esa es la clave intermedia.

El paper además especifica los tipos, donde cada letra representa un tipo:

```
map    (k1, v1)        → list(k2, v2)
reduce (k2, list(v2))  → list(v2)
```

Lo que esas dos líneas nos dicen es que map recibe una clave y un valor de ciertos tipos, k1 y v1, y emite una lista de claves y valores de otros dos tipos, k2 y v2. Y que esos k2 y v2 son exactamente los tipos que recibe el reducer: la misma clave, y una lista ya agrupada de los valores que emitió el map. La salida de reduce es a su vez una lista de valores de ese mismo tipo v2.

{: .nota }
> El paper agrega en §2.2 una precisión que explica por qué la firma de reduce termina en `list(v2)` y no en un tercer par de tipos: las claves y los valores de entrada vienen de un dominio distinto que los de salida, pero las claves y los valores **intermedios** son del mismo dominio que los de salida. De ahí también sale la respuesta a algo que llama la atención al leer el código: `EmitIntermediate(w, "1")` emite el uno **como cadena**, entre comillas, y por eso reduce tiene que hacer `ParseInt(v)` antes de sumar y `AsString(result)` antes de emitir. No es un descuido del ejemplo: la implementación en C++ de MapReduce pasa cadenas hacia y desde las funciones que escribe el usuario, y deja la conversión de tipos del lado del código del usuario.

---
