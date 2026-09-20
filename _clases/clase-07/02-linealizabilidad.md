---
title: "2. Linealizabilidad"
parent: "Clase 7 — Linealizabilidad y Zookeeper"
nav_order: 2
---

# 2. Linealizabilidad
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## La definición: una sola copia, puntos de ejecución y las dos condiciones

La consistencia eventual, tal como quedó planteada, admite casi cualquier comportamiento. Lo contrario tiene nombre —consistencia fuerte—, pero ese nombre significa cosas distintas según con quién se hable. Vamos a adoptar la definición concreta que se usa en los libros de sistemas distribuidos: linealizabilidad.

Es concreta porque surgió de un paper: el de Herlihy y Wing, de 1990, *Linearizability: A Correctness Condition for Concurrent Objects*, donde se definió un criterio sobre cómo puede ser la consistencia fuerte en un sistema distribuido, pensado para diseñar sistemas.

La consistencia fuerte no emerge por sí sola: uno diseña el sistema deliberadamente para que sea linealizable. Después vamos a ver cómo garantizar que Raft lo sea, en contraste con lo que acabamos de observar al leer de un follower; y vamos a ver también que Zookeeper deliberadamente no lo hace, para obtener más performance.

La definición informal —muy informal, pero nos aproxima a la otra— es que el sistema se comporta como si hubiera una sola copia de los datos. El ejemplo es una base de datos convencional, MySQL, Postgres, cualquiera: es linealizable porque no se comporta *como si* tuviera una sola copia, efectivamente la tiene. Ese comportamiento es el que quisiéramos obtener en un sistema que diseñemos nosotros. Vamos a comprobar que no es sencillo y que resulta costoso —hay un tradeoff muy marcado con la performance, porque se requieren muchas más verificaciones—, pero es posible.

Hay una clave del análisis que conviene tener presente desde el comienzo: lo que se observa son varios clientes al mismo tiempo. El sistema como un todo es linealizable o no lo es; no se trata de que lo sea desde la perspectiva de un cliente. Todo lo que hicieron y cómo interactuaron todos los clientes tiene que haber sido fuertemente consistente.

Empecemos por el caso sencillo, el de las operaciones separadas en el tiempo, las no concurrentes. Un cliente escribe uno y otro lee, y debe leer uno. Si la operación del primero comenzó y terminó antes de que el segundo iniciara la suya, la única opción posible es esa: `Wx1` primero y `Rx1` después.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    dos historias de ejecución no concurrentes, C1 con Wx1 y C2 con Rx1 empezando después de que terminó la escritura
    <span class="figura-ref">notas pág. 2, fig. 1</span>
  </figcaption>
</figure>

Lo que no sería linealizable es que allí se hubiera leído un cero: en ese caso el sistema no se comporta como una base de datos única, con el dato en un solo lugar, sin replicar. Si eso le ocurriera a una base de datos, afirmaríamos sin dudar que está rota. Y puede suceder perfectamente si leemos de un follower de Raft: si lo hacemos, no estamos tomando a Raft como un sistema linealizable. Con operaciones no concurrentes no hay duda posible: las cosas que se escribieron antes deben leerse en ese orden.

Con operaciones concurrentes la situación es más compleja, porque las operaciones en un sistema distribuido demoran un tiempo: se envían y eventualmente retornan. Si cada una fuera un punto instantáneo, el criterio sería evidente y todo se ordenaría como antes. Pero son concurrentes aquellas que se solapan, aunque sea levemente: el cliente dos comenzó a enviar su operación antes de que el cliente uno recibiera la respuesta.

Y este es el punto donde el paper define qué hacer. Las operaciones se consideran como si, dentro de ese rango entre el request y el response, se hubieran ejecutado en un punto específico. No importa cuál: importa que sea posible encontrar puntos en el tiempo donde las operaciones tengan sentido. Coloquemos una marca roja vertical dentro de cada segmento, ubicadas de manera tal que la de la escritura caiga antes que la de la lectura. Así la historia tiene sentido y el resultado es lógicamente consistente, porque la lectura está leyendo lo que la escritura escribió antes. Parecería evidente, y en efecto esto es linealizable.

Allí aparece la parte contraintuitiva. Misma situación, mismo solapamiento, con una sola diferencia: el primer cliente escribió `Wx1` y el segundo leyó cero, `Rx0`. ¿Podría esa ejecución corresponder a un sistema linealizable? La pregunta genera cautela, y con razón, porque todo indica que la respuesta debería ser negativa. La respuesta es que sí.

Puede haber ocurrido lo siguiente. El cliente dos envió la lectura y la recibió tarde, pero ese tramo puede haber sido absorbido por un delay de la red, y la lectura concreta sobre una de las réplicas se ejecutó antes que la escritura. Entonces el orden es primero `Rx0` y después `Wx1`, con las marcas invertidas, y el orden lógico también tiene sentido: primero leímos un valor anterior y después actualizamos al nuevo. Contrariamente a lo que uno imaginaría, esto también es linealizable, y esa es la intuición del asunto: los dos órdenes son legales.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    operaciones concurrentes en dos casos apilados — arriba C1 con Wx1 y C2 con Rx1 solapados, cada uno con su marca roja vertical y la de la escritura antes que la de la lectura; abajo el mismo solapamiento con C2 leyendo Rx0 y las marcas al revés; al costado los dos órdenes Wx1 → Rx1 y Rx0 → Wx1, ambos legales
    <span class="figura-ref">notas pág. 2, fig. 2</span>
  </figcaption>
</figure>

De allí surge una idea más general: hasta que las operaciones no responden, los sistemas suelen encontrarse en un estado ambiguo, en el que pueden responder una cosa o la otra. Ya lo habíamos observado de otra manera: la garantía firme aparece cuando el cliente que envió la escritura recibió la confirmación de que terminó. Ahora estamos formalizando esa idea siguiendo el paper.

Con eso podemos enunciar la definición, que tiene dos condiciones. La primera es que el orden de las operaciones respeta el tiempo real. Somos nosotros quienes definimos dónde van las marcas rojas, y ese va a ser el orden; si no resulta adecuado, podemos probar invirtiendo la marca, y vamos a comprobar que en muchos casos no es posible. Y eso no alcanza. La segunda condición, la más importante, es que el orden sea válido lógicamente: a partir de esa secuencia, si escribimos algo, después no debemos leer un valor anterior. Y, nuevamente, se trata de una visión global: si un cliente cualquiera escribe algo, otro cliente tiene que leer eso.

Con las dos condiciones planteadas, el ejemplo evidente de algo no linealizable es el que ya habíamos mencionado: un cliente escribe `Wx1` y el otro lee `Rx0`, sin solapamiento. Necesariamente una ocurrió primero, de modo que sobre el orden no tenemos opción: no hay marcas que desplazar. La condición uno se cumple; la dos no tiene sentido, y allí está la falla. En rojo: no es legal leer valores anteriores.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el contraejemplo — Wx1 y debajo Rx0 sin solapamiento, con el chequeo de las dos condiciones al pie: la primera se cumple porque Wx1 ocurrió necesariamente antes que Rx0, la segunda falla porque Rx0 no es legal después de Wx1
    <span class="figura-ref">notas pág. 2, fig. 3</span>
  </figcaption>
</figure>

Y si la escritura sucede primero y le sigue la lectura, ¿no está obligada esa lectura a leer la información nueva? Sí, y por eso ese sistema no es consistente: si nos lo presentaron como consistente, tenemos fundamentos sólidos para objetarlo. Pero en un sistema como el de la sección anterior, donde la advertencia se plantea desde el comienzo, eso simplemente significa que no es linealizable: que su consistencia es eventual y no fuerte. Puede ocurrir y lo admitimos, porque estamos leyendo de un follower desactualizado. La premisa es esa: si nos encontramos con esta situación, no estamos frente a un sistema con consistencia fuerte.

Vamos a usar la palabra linealizable, que es la formal, con un mapeo mental directo: linealizable equivale a consistencia fuerte, en el sentido de que todas las operaciones deben estar ordenadas. Y lo notable de los sistemas distribuidos es que muchas veces admitimos un sistema que no cumple esa condición porque igualmente resulta útil: vamos a ver que Zookeeper es útil sin esa propiedad.

---

## Cuatro historias: ¿linealizable o no?

En los cuatro ejemplos que siguen vamos a ubicar esas marcas rojas en distintos lugares para determinar si es posible que el sistema sea fuertemente consistente. No son originales: figuran en los videos del MIT. Rehacerlos resulta útil igualmente, porque después de recorrerlos el criterio de las marcas rojas deja de ser una definición y se convierte en un procedimiento.

En los diagramas, cada línea representa un cliente. Y hay algo fácil de olvidar: lo que observamos es una visión global e hipotética, difícil de obtener de un sistema real. Si pudiéramos ver el sistema entero y lo que reciben todos los clientes al mismo tiempo —o si todos tuvieran un log y después se unificaran en uno solo—, entonces sí podría armarse un gráfico como estos y verificar si la ejecución fue consistente. Los diagramas son la herramienta de análisis, no algo observable desde adentro.

El primer ejemplo: un cliente envía `Wx1` y después `Wx2`; otro cliente lee y obtiene `Rx2`. Lo particular es que esa lectura queda levemente solapada con la escritura de `x = 2`, y vista así resulta extraña. Pero hay un orden posible. La primera escritura puede materializarse en cualquier momento de su segmento; no introduce diferencia. La clave está en la otra: `Wx2` debe ocurrir antes que la lectura, y puede, porque ambas se solapan. De izquierda a derecha, las tres marcas quedan `Wx1`, `Wx2`, `Rx2`.

El procedimiento mental es el mismo que vamos a emplear siempre: recorrer el tiempo de izquierda a derecha, ubicar las marcas rojas a medida que aparecen, y después examinar la secuencia y verificar si tiene orden lógico. Aquí lo tiene, y puede enunciarse casi en voz alta: escribimos uno, lo sobrescribimos con dos, y leímos dos. Es linealizable, y lo único que hubo que hacer fue asignar los puntos de ejecución.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    historia del ejemplo 1 — arriba Wx1 y Wx2 consecutivos, abajo Rx2 solapado con Wx2, los tres con su marca roja, y el orden resultante Wx1 → Wx2 → Rx2
    <span class="figura-ref">notas pág. 2, fig. 4</span>
  </figcaption>
</figure>

El segundo ejemplo tiene tres clientes. El primero escribió `Wx1` y después `Wx2`; un segundo leyó `Rx2` y un tercero leyó `Rx1`. Están dispuestos así deliberadamente, de manera simétrica, para que resulte llamativo: dos clientes casi al mismo tiempo leyeron valores distintos, en un sistema de consistencia fuerte. ¿Sería posible? Conviene intentar resolverlo antes de continuar. La respuesta es afirmativa, y el orden que lo justifica es el siguiente: la primera escritura se materializa en algún punto de su segmento, después la lectura del cliente que leyó uno, después la segunda escritura, y por último la lectura del que leyó dos. Nos queda `Wx1`, `Rx1`, `Wx2`, `Rx2`, y funciona: cada lectura devolvió el último valor escrito antes de su propia marca.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    historia del ejemplo 2, tres clientes — arriba Wx1 y Wx2, abajo un Rx2 largo cruzando las dos escrituras y más abajo un Rx1 más corto, todos con su marca roja, y al costado el orden Wx1 → Rx1 → Wx2 → Rx2
    <span class="figura-ref">notas pág. 3, fig. 1</span>
  </figcaption>
</figure>

Vamos a complicarlo un poco. El tercer ejemplo es parecido: arriba las mismas dos escrituras; abajo una lectura que obtuvo el dos, comenzando durante la primera escritura, y después otra que obtuvo `Rx1`. ¿Es linealizable? Aquí también la primera escritura puede ubicarse en cualquier lugar. La clave está en la otra: `Wx2` debe ocurrir siempre antes que `Rx2`. En el peor de los casos las ubicamos lo más próximas posible, para dejar el máximo de espacio libre a la derecha. Y entonces `Rx1` necesariamente viene después, todo lo cerca que se quiera pero después. Allí está el problema: la secuencia queda `Wx1`, `Wx2`, `Rx2` y solo al final `Rx1`, y no existe otra forma de acomodar las marcas. Esta historia no es linealizable.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    historia del ejemplo 3 — arriba Wx1 y Wx2, abajo Rx2 empezando durante Wx1 y después Rx1, sin marcas rojas posibles: no es linealizable
    <span class="figura-ref">notas pág. 3, fig. 2</span>
  </figcaption>
</figure>

El cuarto y último ejemplo tiene dos partes. Arriba `Wx1` y después, algo desplazado, `Wx2`, solapadas entre sí; abajo `Rx2` y después `Rx1`. Es deliberadamente contraintuitivo. ¿Es linealizable? También lo es. La forma de advertirlo es reordenar mentalmente: ubicando las dos marcas de arriba en un lugar y las dos de abajo en otro, se escribe `x = 2`, se lee `x = 2`, se escribe `x = 1` y se lee `x = 1`. Perfectamente válido.

Conviene admitir que el ejemplo es engañoso, y el equívoco está en los números elegidos: ¿por qué denominar `x = 2` a lo que en el resultado final aparece primero? Eso confunde, aunque la historia se transforme igualmente. Pero manteniendo la parte superior y modificando la inferior aparece la segunda parte del ejemplo: las mismas dos escrituras solapadas, y abajo las dos lecturas cruzadas, `Rx1` primero y `Rx2` después. El primer caso es linealizable y el segundo no. Cuesta un poco advertirlo, aunque la intuición debería ser suficiente: no hay forma de haber leído `Rx2`, después `Rx1`, y que además el cliente de arriba pueda volver a leer `Rx1`. Con las lecturas cruzadas, las marcas de los dos clientes inferiores se vuelven incompatibles, y eso invalida el esquema.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    ejemplo 4 en dos partes — arriba Wx0 y después Wx1 y Wx2 solapados entre sí, con Rx2 y Rx1 debajo y marcas verdes en todas: sí es linealizable; separado por una línea de puntos, los mismos writes con los reads cruzados, Rx1 y después Rx2, sin marcas posibles: no lo es
    <span class="figura-ref">notas pág. 3, fig. 3</span>
  </figcaption>
</figure>

En el curso del MIT presentan una demostración más matemática: si uno encuentra un orden que constituye un grafo y ese grafo tiene un ciclo, entonces no es linealizable. Es un criterio compacto y sirve para demostrarlo con rigor, pero no vamos a profundizar en él, porque excede el enfoque de la materia.

---
