---
title: "7. Las cuatro propiedades de un servicio cloud"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 7
---

# 7. Las cuatro propiedades de un servicio cloud
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## Fully managed

Detrás de cada uno de estos servicios hay un equipo que lo desarrolla y lo mantiene, pero desde afuera uno no lo opera. El paper de DynamoDB tiene un nombre para eso: el servicio es *fully managed*, completamente operado por la empresa.

Cuando a uno le toca usar DynamoDB —y es probable que en algún momento de la carrera le toque— la experiencia es esta: se crea una tabla, la tabla aparece y se la empieza a usar. No hay que preocuparse por el aprovisionamiento. La nube es un término muy poético, pero las cosas no están en ninguna nube: hay servidores físicos. Cuando uno crea una tabla, alguien del otro lado tiene que elegir un servidor físico, con su procesador y su disco, y la tabla se crea en el disco de esa máquina. Todo eso es transparente: nada de eso lo elige ni lo ve el que creó la tabla.

El escalado también lo manejan ellos. La actualización del software depende del sistema, pero en la mayoría uno no se tiene que preocupar por actualizar el sistema operativo de lo que corre su tabla. Después viene la tolerancia a fallas, y aquí hay algo casi paradójico: si la maneja Amazon, parece que esta clase no tuviera sentido, porque llevamos dos meses hablando de tolerancia a fallas y, si uno usa Dynamo, se olvida del tema. Aunque hay un matiz: si uno quiere trabajar en Amazon, tiene que aprender cómo funciona y todas las técnicas que la implementan, que también se usan a pequeña escala. Con la replicación pasa lo mismo. Y la lista es más larga: estos son apenas algunos ejemplos de lo que un servicio fully managed resuelve por el cliente.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el cliente contra la API de DynamoDB — el cliente a la izquierda, la flecha rotulada API, la caja del servicio a la derecha, y al costado la lista de lo que el cliente ya no hace: aprovisionamiento, escalado, actualización del software, tolerancia a fallas, replicación
    <span class="figura-ref">notas pág. 5</span>
  </figcaption>
</figure>

Eso es fully managed. Todos los problemas en los que pusimos tanta cabeza, Amazon cobra por resolverlos: dispone de personal que, cuando algo falla, se levanta en mitad de la noche, se conecta por SSH y lo repara. Es una de las propiedades más seductoras para las empresas, porque la parte más difícil de un sistema distribuido se delega en otra empresa. Y eso facilitó mucho el desarrollo web a gran escala: internet creció de forma explosiva cuando hubo empresas grandes dedicadas a resolver los problemas difíciles y empresas muy pequeñas que simplemente usaban esos servicios.

## Multi-tenant: todos los inquilinos en el mismo edificio

Para que eso tenga sentido, primero tienen que cerrar los números. No sería viable que por cada cliente nuevo de Amazon alguien tuviera que instalar una máquina física en el rack y ponerla en funcionamiento.

De ahí la segunda propiedad: estos sistemas son *multi-tenant*, y *tenant* quiere decir inquilino. Sobre un único sistema —un único DynamoDB, por ejemplo— viven todos los usuarios mezclados. Cada uno está aislado del otro, pero comparten la misma infraestructura, y eso permite aplicar economía de escala. Sería muy costoso que cada cliente tuviera su propio DynamoDB. Lo que hace falta entonces son mecanismos para que un usuario que usa mucho una parte del sistema no interfiera con otro; en la jerga, el *noisy neighbor*, el vecino ruidoso.

No siempre fue así. Antes de Amazon, cuando esto ni siquiera se llamaba nube, hubo proveedores que funcionaban al revés: por cada cliente nuevo creaban una instancia nueva de Postgres, y cada uno terminaba con su propia base corriendo aparte.

Y la pregunta no desapareció con ellos. Quienes no están familiarizados con los sistemas modernos suelen preguntar si cada cliente de una empresa tiene su propia base de datos o si es todo una única base. La respuesta es que están todos en una única base. El costo operacional y económico de infraestructura propia por cliente, cuando uno quiere miles o millones de clientes, sería prohibitivo.

Multi-tenant es eso: los clientes comparten el sistema, abstraído de manera que ninguno lo note. En los sistemas cloud es prácticamente un principio fundamental.

## Una API con SLA

Después vienen detalles más finos. La API tiene un SLA estricto, y eso es parte de lo que venden: garantía de disponibilidad y de latencia. Cuán laxo sea depende de la empresa. Amazon mide la disponibilidad en cantidad de nueves: el 99,99% del año el sistema tiene que estar levantado, y el 0,01% restante es el margen de caída tolerado. El año tiene 525.600 minutos, así que ese margen son 53 minutos: si el servicio estuvo caído menos que eso en el año, el contrato se cumplió. Si se pasan, devuelven un porcentaje del dinero según el tiempo excedido. Así de estrictos son con el SLA.

No venden solamente el servicio, sino también, como parte del contrato, la garantía de que va a funcionar. Todos los proveedores grandes tienen garantías de este tipo.

## Escala "ilimitada", elasticidad y serverless

Lo otro muy prometedor para las empresas, especialmente las startups, es la escala ilimitada. No es realmente ilimitada: lo es en el sentido de que si la instancia de DynamoDB resulta insuficiente, podemos ampliarla, en principio sin límite. También se la llama elasticidad. Son términos de marketing y algo confusos. Lo que importa es que todo el aprovisionamiento está abstraído del lado del servicio: el cliente ya no elige cuántos nodos tiene su DynamoDB, simplemente solicita más capacidad y el sistema se adapta.

Al costado hay un término que se escucha mucho y que en algún momento veremos con más detalle: *serverless*. No quiere decir que no haya un servidor. Se aplica más bien al cómputo. Cuando uno compra cómputo —máquinas virtuales, containers, servidores dedicados—, cada producto expone distinta visibilidad sobre las máquinas físicas. En el producto de máquinas virtuales de Amazon, uno crea una máquina, la ve y puede acceder a ella. En otro producto, serverless, que se llama Lambda, uno manda un código y ese código se ejecuta en algún lugar. Lo que se configura es cuánta memoria tiene la función —el procesador escala junto con la memoria— y cuántas copias pueden correr a la vez; cuántas instancias hacen falta en cada momento lo decide Amazon sola. Esos requests también se ejecutan en servidores, pero los administra Amazon y uno no los ve: por eso serverless. Es una cuestión administrativa. La capacidad está mucho más abstraída, y la unidad deja de ser la máquina: en las máquinas virtuales se cuentan máquinas, en Lambda ejecuciones simultáneas toleradas. Es otro término de moda, ligado directamente a esa escala supuestamente ilimitada.

---
