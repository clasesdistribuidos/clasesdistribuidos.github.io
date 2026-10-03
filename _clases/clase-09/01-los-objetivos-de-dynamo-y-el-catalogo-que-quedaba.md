---
title: "1. Los objetivos de Dynamo y el catálogo que quedaba por cubrir"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 1
---

# 1. Los objetivos de Dynamo y el catálogo que quedaba por cubrir

En el paper de Dynamo hay una tabla, la tabla uno, que resume todas las técnicas de sistemas distribuidos que usa el sistema. Se parece mucho a nuestro propio programa: son casi las mismas técnicas que nos interesan, algunas mucho más que otras.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-09/tecnicas-de-dynamo.jpg' | relative_url }}" alt="Tabla 1 del paper de Dynamo: problemas, técnicas y ventajas">
  <figcaption>
    <span class="figura-label">Figura</span>
    Table 1 del paper de Dynamo — las cinco técnicas (consistent hashing, relojes vectoriales, sloppy quorum con hinted handoff, anti-entropy con Merkle trees, gossip) con el problema que resuelve cada una y su ventaja
    <span class="figura-ref">pizarra pág. 1, recorte del paper</span>
  </figcaption>
</figure>

Parte de esa tabla ya está cubierta. Casi toda la clase pasada hablamos de la alta disponibilidad basada en relojes vectoriales, y vimos algo de consistent hashing, aunque eso ya se sabía de antes y no fuimos muy a fondo. Quedan las otras, que vamos a ver más por arriba: no son tan fundamentales, pero hacen falta para que el paper quede completo.

El objetivo de Dynamo era un SLA de 99,9% con una latencia menor a 300 milisegundos. SLA quiere decir Service Level Agreement, y nombra lo que uno trata de obtener del sistema; en este caso, en términos de latencia. El 99,9% de los requests se tienen que resolver en menos de 300 milisegundos. No hay que tomarlo a la ligera: no es un promedio, es prácticamente la totalidad de los requests. De cada mil, solamente uno tiene permiso para pasarse. A los de Dynamo les interesaba la cola de la distribución: que todos los requests se resolvieran rápido y solo ese pequeño porcentaje fallara. Por eso distribuirlo tanto, y por eso el anillo con replicación y sharding. Y todo eso con fallas constantes: en un sistema con miles de nodos, siempre hay componentes fallando de forma aleatoria.

El otro objetivo era ser *always writable*, a costa de la consistencia. Se admitía leer datos inconsistentes —no linealizables, no fuertemente consistentes— y eso estaba bien. Lo importante era que la escritura quedara durable y persistida en varias réplicas.

Eso lo lograba principalmente con tres ideas, de las cuales vamos a recordar dos. La primera es la consistencia eventual. Dynamo fue el primer sistema que puso de moda que una base de datos pudiera tener consistencia eventual; antes, una base de datos tenía que ofrecer las garantías fuertes de siempre —linealizabilidad, serializabilidad— y devolver siempre la última versión escrita. La segunda es la replicación con sloppy quorum: un quórum perezoso, o mejor dicho desordenado, que es probablemente la traducción correcta. Qué significa exactamente es lo que vamos a ver ahora.

{: .nota }
> El término "consistencia eventual" es anterior a Dynamo: lo acuñó Doug Terry en el paper del sistema Bayou, en 1995. Lo que Dynamo puso de moda fue llevar la idea a una base de datos de producción.

---
