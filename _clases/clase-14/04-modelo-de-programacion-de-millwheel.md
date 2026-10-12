---
title: "4. Modelo de programación de MillWheel"
parent: "Clase 14 — Procesamiento de streams"
nav_order: 4
---

# 4. Modelo de programación de MillWheel
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Analogía con MapReduce

Hasta ahora vimos el watermark en su versión gráfica, que no siempre cierra del todo. Verlo en código suele ser más fácil, porque ahí se ve mejor cómo se usa para cerrar la ventana. El plan es ese: primero el modelo de programación, después cómo se implementa. Conviene aclararlo desde el inicio: estos conceptos requieren esfuerzo, así que si algo no queda claro la primera vez, es perfectamente razonable volver sobre esa parte.

El modelo de MillWheel es el equivalente de lo que estudiamos con MapReduce, cuando aprendimos a hacer mappers y reducers y nos preguntamos cómo estaba implementado eso por debajo. La comparación no es decorativa: la idea es la misma. MapReduce se inventó porque la parte difícil de estos sistemas era distribuirlos. Frente a eso abstrajeron dos primitivas muy reutilizables, map y reduce, se las dieron a los programadores para implementarlas, y la infraestructura de MapReduce se encargaba de todo el resto.

Aquí hicieron exactamente lo mismo. MillWheel nos provee un par de funciones que tenemos que implementar y un par de cosas más, no muchísimo más. Por un lado nos resuelve el escalado, el retry de los errores y la reasignación del trabajo cuando un nodo se cae, que es la mitad de la promesa; por el otro nos resuelve las ventanas, notificándonos los watermarks y cuándo abrir y cerrar ventanas, que es la otra mitad, la que veníamos construyendo trabajosamente.

## Grafo de cómputos

La primera figura del paper tiene la idea fundamental, y no es tan simple como un mapper y un reducer. Lo que hay es un DAG, un grafo dirigido acíclico, donde el dato fluye por distintos cómputos. Cada etapa del grafo es lo que el paper llama cómputo —*computation*—. En Zeitgeist, el stream de búsquedas entra a un cómputo que cuenta las búsquedas por ventana, que alimenta a otro que calcula el modelo y a otro que detecta picos y caídas, y la salida final va al sistema externo que notifica las anomalías.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el grafo dirigido acíclico de cómputos de Zeitgeist: el stream de búsquedas entrando al Window Counter, que alimenta al Model Calculator y al Spike/Dip Detector, y la salida al sistema externo de notificación de anomalías
    <span class="figura-ref">figura 1 del paper de MillWheel</span>
  </figcaption>
</figure>

Cada flecha del grafo es conceptualmente un stream, no un Kafka: streams en sentido abstracto. De hecho, más adelante vamos a ver que se implementan con RPCs entre las etapas. Y cada cómputo es, en abstracto, un código que se particiona y se ejecuta en muchas máquinas; por eso en el dibujo del paper aparecen varias cajas superpuestas por cómputo. El stream entra por una etapa, se puede bifurcar, se puede volver a unir, puede emitir por varios lugares: es superflexible, y vamos a volver varias veces sobre esta figura.

## ProcessRecord y ProcessTimer

La API está en la figura 7 del paper, y es el equivalente del mapper y el reducer. No todas sus funciones juegan el mismo papel:

```cpp
class Computation {
  // Hooks called by the system.
  void ProcessRecord(Record data);
  void ProcessTimer(Timer timer);

  // Accessors for other abstractions.
  void SetTimer(string tag, int64 time);
  void ProduceRecord(Record data, string stream);
  StateType MutablePersistentState();
};
```

Al principio importan las dos primeras, porque son las que implementamos nosotros. El parecido con map y reduce se agota en que son dos. `ProcessRecord` es la principal: se ejecuta una vez por cada récord —cada evento, que en este paper se llama récord— que recibimos. Al procesarlo podemos llamar a otro sistema, emitir otros récords y setear timers, que es lo que vamos a ver en el ejemplo: al procesar récords podemos decidir iniciar una ventana nueva donde acumular. `ProcessTimer` es la que el sistema llama para avisarnos que se disparó una ventana: ocurrió eso que dibujamos antes, el watermark cruzó el timer que habíamos programado, y tenemos que hacer algo.

El paper trae el ejemplo en C++, un lenguaje que se usaba muchísimo hace unas décadas, después perdió terreno y últimamente vuelve un poco, aunque hoy no es de los más familiares; aquí aparece traducido a Python. Lo vemos en dos pasos: primero una versión con variables globales, que no está en el paper y sirve para ver la forma, y después la del paper, que resuelve el problema que la primera deja abierto. Del ejemplo vemos la primera mitad, la que cuenta búsquedas y las asigna a ventanas.

```python
class Windower:
    def process_record(self, record):
        bucket = window_id(record.timestamp)
        tag = (record.key, bucket)
        window_counts[tag] = window_counts.get(tag, 0) + 1
        set_timer(tag, window_boundary(record.timestamp))

    def process_timer(self, timer):
        key, bucket = timer.tag
        count = window_counts.get(timer.tag, 0)
        record = Record(key, count, timer.timestamp)
        produce_record(record, "windows")
```

El argumento de la primera función es el récord, que tiene varias cosas adentro. Una clave, que en este ejemplo es la búsqueda. Data, que aquí no importa demasiado; podría ser cualquier otra cosa. Y un timestamp. La clave, la data y el timestamp siempre tienen que estar. El timestamp generalmente es el event time, y es lo que usamos para agrupar.

A partir del timestamp vemos en qué bucket poner el récord: eso hace la primera línea. Si el timestamp fuera 8:03:01, el window ID podría ser el de las 8:00:00 en punto; si fuera 8:06:01, el de las 8:05:00. No es nada sofisticado: una especie de división entera del timestamp. La idea es que tenemos muchos acumuladores que se abren y cierran a medida que ocurren las cosas, y `window_id` decide a cuál le corresponde el récord. Y `window_id` no es del sistema: es una función nuestra.

La línea siguiente inventa un identificador que el ejemplo llama tag, combinando la clave con el bucket: por ejemplo, el par Britney y las 8:00:00. Es exactamente lo que queremos identificar: una búsqueda determinada dentro de una ventana determinada.

Y ahí viene la parte que vamos a tener que modificar. Este primer ejemplo usa variables globales para contar, y eso rápidamente no funciona: en un sistema distribuido, una variable global en la memoria de mi máquina no existe en la de otra. Cada nodo tendría su propio diccionario con su cuenta parcial, sin ver lo que cuentan los demás. Pero sirve para ver la idea. `window_counts` es un diccionario de Python: cada clave es el tag —el par búsqueda y ventana— y cada valor el contador. Se lo lee con un `get` con default, se lo incrementa en uno y se lo vuelve a guardar. Hasta aquí se trata de Python elemental.

Lo interesante es la última línea: seteamos un timer, y no importa setear varias veces el mismo, porque el sistema lo soporta. Lo que le pedimos al sistema es que nos llame: esa llamada va a invocar a `process_timer` cuando ocurra el `window_boundary`. Le pasamos el tag, para saber después de qué acumulador hablamos, y el borde de la ventana. Con ventanas de cinco minutos, para un récord de las 8:03 el borde son las 8:05. `window_boundary` también es nuestra: indica, para este tag, que se nos avise cuando el watermark pase por las 8:05, cuando el sistema garantice que ya no vendrá nada más viejo.

Cuando eso ocurre se invoca la segunda función con información del timer, que trae el tag: Britney y las 8:00. Tomamos el contador, extraemos la clave, y con la clave, la cuenta y el timestamp del timer generamos un nuevo récord y lo producimos hacia adelante.

Esta segunda función es incluso más fácil de leer que la primera. En las dos aparecen dos funciones que no son nuestras. El sistema nos provee `set_timer`, que calendariza para que nos llamen, y `produce_record`, que manda un registro a la siguiente etapa del grafo. Cómo se conectan las etapas no lo vemos aquí —está en el paper—, pero hay una configuración, y un `produce_record` puede ir a distintos lugares; si hay varias salidas se especifica el nombre del stream de destino, que en este ejemplo es `windows`.

## Estado persistente

De las funciones que nos da el sistema ya vimos `SetTimer` y `ProduceRecord`; falta una, justamente la que resuelve el problema que quedó planteado. Como esto está distribuido, no podemos usar variables globales como `window_counts`. El sistema nos provee una especie de variable global que en realidad no lo es: `MutablePersistentState`.

`MutablePersistentState` es un array de bytes que podemos escribir y volver a leer. El paper no es muy claro sobre cómo se hace exactamente; supuestamente nos devuelve un objeto, y cuando lo modificamos se escribe automáticamente. Lo que sí propone es envolver esos bytes en una clase propia. `WindowState`, por ejemplo, deserializa los bytes y permite interpretarlos como un objeto en vez de un array crudo. `WindowState` es nuestra, no de MillWheel, y adentro tiene lo necesario para actualizar la cuenta de los buckets. El ejemplo queda así:

```python
class Windower:
    def process_record(self, record):
        state = WindowState(mutable_persistent_state())
        state.update_bucket_count(record.timestamp)
        window = window_id(record.timestamp)
        set_timer(window, window_boundary(record.timestamp))

    def process_timer(self, timer):
        state = WindowState(mutable_persistent_state())
        count = state.window_count(timer.tag)
        record = Record(key(), count, timer.timestamp)
        produce_record(record, "windows")
```

{: .nota }
> Quien vaya al paper a buscar las dos versiones va a encontrar solo una. En la figura 9 —que es de donde sale este ejemplo, y está en C++— el `Windower` ya viene escrito con `WindowState state(MutablePersistentState())`; la versión con el diccionario global no está ahí, es un paso intermedio para mostrar por qué el estado persistente hace falta. Sobre la duda de cómo se escribe y se vuelve a leer ese estado, el paper da la respuesta en otro lado y confirma la intuición: la serialización por clave la maneja el framework, el usuario solo provee las rutinas de serialización y deserialización —con Protocol Buffers, por ejemplo—, y todas las modificaciones por clave se envuelven en una única operación atómica que se materializa al cerrar el hook. Akidau et al., VLDB 2013, §4.4, §5.1, §6.2 y figura 9.

Otra figura del paper muestra cómo encaja nuestro código dentro del sistema. Se compilaba un binario que tenía adentro todos los cómputos —y enseguida vamos a ver que cada nodo puede realizar cualquiera—. Nosotros implementábamos el user code, que interactuaba con el sistema de dos maneras: el sistema nos llamaba por `ProcessRecord` y `ProcessTimer`, y había APIs para guardar cosas en el persistent state. Más adelante volvemos sobre qué es exactamente ese persistent state; básicamente usa por debajo Spanner, Bigtable o algo así, pero está abstraído porque tiene particularidades propias.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la arquitectura del sistema: el binario de MillWheel, el user code con ProcessRecord y ProcessTimer, las tres APIs de estado, timers y producciones, y el estado persistente por debajo
    <span class="figura-ref">figura 8 del paper de MillWheel</span>
  </figcaption>
</figure>

La interfaz de MillWheel es, entonces, dos lugares desde los cuales el sistema nos llama —callbacks, en un lenguaje más al estilo JavaScript—, y tres APIs para interactuar con el sistema, las de la mitad de abajo de la figura 7: persistir estado, crear timers y producir registros. Interesantemente, `produce_record` guarda el registro en el estado persistente: no lo emite directamente por RPC al cómputo siguiente, sino que lo guarda allí por un breve lapso. Por qué, lo vemos más adelante.

El modelo entra en una frase, y suele entenderse así la primera vez: desde `process_record`, que se llama cada vez que entra un récord, hacemos cosas y decimos «tengo un timer para cuando pase el watermark»; y `process_timer` es lo que hacemos cuando sabemos que se cerró la ventana y nos quedó ese evento dentro de la ventana delimitada por el watermark. Exactamente eso. Nos pueden pasar dos cosas, y solo dos: en el ejemplo de contar, cada vez que llega un registro lo contamos, y cada vez que cierra una ventana emitimos su resultado. A la primera función la dispara que llegue un récord; a la segunda, que haya que cerrar una ventana.

El concepto de ventana no está en MillWheel, aunque es de las cosas que más fácilmente se le atribuyen. La abstracción de ventana la generó el paper de Dataflow, que quedó afuera por razones de tiempo y muestra muchísimos tipos de ventanas: fijas, que se mueven, que se solapan, por sesión del usuario. MillWheel nos da el assembler de eso, la primitiva de bajo nivel: seteamos un timer y cuando llega el watermark nos avisa, sin saber para qué lo queríamos. De aquí en adelante el tema se vuelve más complejo, porque vienen los detalles de implementación.

---
