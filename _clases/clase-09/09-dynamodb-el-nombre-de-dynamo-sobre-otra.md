---
title: "9. DynamoDB: el nombre de Dynamo sobre otra arquitectura"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 9
---

# 9. DynamoDB: el nombre de Dynamo sobre otra arquitectura

La historia explica buena parte de lo que sigue. Las bases no relacionales se habían puesto de moda, y Amazon quiso hacer una en la nube. No fue la primera: DynamoDB surge de SimpleDB, un sistema que ya no existe. Y ese es el punto importante, antes que ningún otro: DynamoDB no desciende de Dynamo.

¿Por qué se llama así, entonces? Por marketing. El paper de Dynamo tuvo enorme repercusión en 2007: se lo discutía en blogs y en Twitter, junto con los de MapReduce y Google File System; eran los tres papers de moda. Capitalizando esa publicidad, a la siguiente versión de SimpleDB la llamaron DynamoDB, para vender más. Eso es todo lo que hay detrás del nombre.

Cuando veamos la arquitectura vamos a comprobar que no tiene prácticamente nada que ver con la que estudiamos. Conserva la idea general de Dynamo, y nada más; conviene no confundirlos.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-09/genealogia-de-dynamodb.png' | relative_url }}" alt="SimpleDB lleva a DynamoDB; la flecha desde Dynamo, tachada">
  <figcaption>
    <span class="figura-label">Figura</span>
    la genealogía de DynamoDB — SimpleDB da lugar a DynamoDB, y la flecha que vendría de Dynamo aparece tachada con una cruz: del paper de 2007 viene el nombre, no la arquitectura
    <span class="figura-ref">pizarra pág. 6</span>
  </figcaption>
</figure>

La primera diferencia está en la abstracción que se ofrece. Dynamo no tenía tablas: era simplemente un key-value store. DynamoDB incorpora la tabla, la que cualquiera conoce, con sus columnas. Lo importante es que tiene una clave, y esa clave determina cómo se shardea todo.

La figura 1 del paper muestra la evolución del servicio: se parte del paper de Dynamo, varios años después sale DynamoDB, y con el tiempo se le incorporan nuevas funcionalidades. De todas ellas vamos a estudiar una en particular: las transacciones. Primero veremos cómo las implementa DynamoDB, y después, en la última clase de bases de datos distribuidas, cómo las implementa Spanner. Son dos formas completamente diferentes.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-09/dynamodb-linea-de-tiempo.png' | relative_url }}" alt="Línea de tiempo de DynamoDB, de 2007 a 2021">
  <figcaption>
    <span class="figura-label">Figura</span>
    figura 1 del paper de DynamoDB — la línea de tiempo del servicio, desde el paper de Dynamo hasta DynamoDB y las funcionalidades que se le fueron agregando
    <span class="figura-ref">del paper, referenciada en notas pág. 6</span>
  </figcaption>
</figure>

Vamos al modelo de datos. Las tablas tienen items, que vendrían a ser las filas, aunque como pueden tener JSON adentro la idea de fila no es del todo buena. Cada item tiene atributos, que serían las columnas y son lo que menos nos interesa, y una primary key. El paper describe dos variantes: una partition key sola, o una partition key con una sort key. La segunda no la vamos a ver en detalle porque excede el alcance de la clase; con la lectura del paper se comprende sin dificultad. Lo interesante es la primera.

La partition key importa porque es la que se usa para shardear, terreno que ya conocemos de sobra: la partition key pasa por una función de hash, y de ahí sale un hash.

Y aquí aparece la diferencia que importa: no hay ningún anillo. Hay un espacio de direcciones del hash de 2¹²⁸ − 1 posiciones, desde el 0 hasta el último valor. Son unas 3,4 × 10³⁸ direcciones, muchas más que las claves que va a tener jamás cualquier tabla, y esa desproporción le permite al sistema partir el espacio donde quiera y con la granularidad que quiera: siempre quedan direcciones libres a los dos lados de cualquier corte. El hash de una clave cae en algún lugar de ese espacio. Dónde empieza y termina cada partición es arbitrario: no es aleatorio, sino que lo elige el sistema según varias consideraciones. Tendería a ser uniforme, aunque no necesariamente: una región muy accedida se puede volver a subdividir. Así el espacio queda partido en las particiones uno, dos, tres, cuatro y cinco.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-09/hash-de-la-partition-key.png' | relative_url }}" alt="El hash de la partition key sobre el espacio de 0 a 2^128 − 1">
  <figcaption>
    <span class="figura-label">Figura</span>
    el hash de la partition key sobre el espacio de direcciones — la partition key entra a una función de hash, y el hash cae en un punto del eje que va de 0 a 2¹²⁸ − 1; el eje está partido en cinco particiones de tamaños distintos y arbitrarios, y al costado la advertencia de que no se usa consistent hashing
    <span class="figura-ref">notas pág. 6 / pizarra pág. 6</span>
  </figcaption>
</figure>

Hasta aquí nada raro. Pero lo importante es que no usa consistent hashing, que era lo fundamental del otro paper. Ni siquiera lo hicieron. Y eso deja una pregunta abierta: si nadie puede calcular con una función conocida por todos dónde cayó cada partición, ¿quién sabe dónde está cada una?

---
