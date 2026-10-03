---
title: "10. La arquitectura de DynamoDB"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 10
---

# 10. La arquitectura de DynamoDB
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


## El request router y el partition metadata system

La arquitectura de DynamoDB, en la figura cuatro del paper, responde esa pregunta. Tiene bastantes más componentes que Dynamo, pero para lo que nos interesa se reduce a dos piezas. De un lado están el usuario y la red que lo conecta, que no importan demasiado. Lo primero que encuentra el request al llegar es el **request router**.

El request router es, básicamente, el servidor web por el que entran todas las peticiones y que después las manda a alguno de los storage nodes. Tiene además dos tareas propias, que no son lo que más nos interesa. Una es autenticar el request: verificar que nadie trate de acceder a la base de datos de otro. La otra es contar cuántos requests por segundo se hacen, que es justamente lo que se le manda al metering que describimos antes.

Lo que sí nos interesa es la otra pieza, el **partition metadata system**: una base de datos adicional donde vive cómo se reparten las particiones sobre el espacio del hash y en qué nodo está cada una. No es una tabla auxiliar menor, sino una base de datos en sí misma, con una gran tabla adentro. El paper menciona un detalle curioso: la primera versión guardaba esa tabla en DynamoDB, una circularidad incómoda —el sistema que dice dónde está cada cosa, guardado dentro del sistema que uno quiere consultar—. Después la movieron a un sistema aparte, MemDS, un datastore distribuido en memoria: los request routers le consultan a MemDS tanto cuando su caché local falla como cuando acierta, para que la carga sobre el metadata service sea constante y una caché fría no provoque una avalancha. Y dentro de cada nodo de MemDS vive una estructura llamada *Perkle*, un híbrido entre un Patricia trie y un árbol de Merkle: los mismos árboles de hashes de la sección 4, reaparecidos para otra tarea, la de buscar por prefijo y por rango sobre las claves ordenadas.

{: .nota }
> MemDS y el Perkle no tienen un paper propio; están descritos en el paper de DynamoDB —Elhemali et al., "Amazon DynamoDB: A Scalable, Predictably Performant, and Fully Managed NoSQL Database Service", USENIX ATC 2022—, el mismo que la clase toma como fuente. Lo que ese paper efectivamente no detalla es dónde queda almacenada la metadata en última instancia.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la arquitectura de DynamoDB, figura 4 del paper — el cliente, el request router, la columna de tres storage nodes que forman el grupo de replicación, y abajo el partition metadata system; con la advertencia de que aquí no hay ningún anillo
    <span class="figura-ref">notas pág. 7</span>
  </figcaption>
</figure>

Esa gran tabla tiene dos columnas: el rango del hash y los storage nodes que le corresponden. Por ejemplo: el rango del 0 al 1000 —del hash, no de la clave— está en S1, S2 y S3; el del 1001 al 5000, en S4, S8 y S10; y así hasta el último valor del espacio, ese FF de la notación hexadecimal. La tabla tiene que cubrir el rango completo: ninguna porción del espacio de hash puede quedar sin nadie que lo atienda.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la tabla del partition metadata system — dos columnas, rango de hash y storage nodes: del 0 al 1000 van S1, S2 y S3; del 1001 al 5000, S4, S8 y S10; y así hasta cubrir el espacio completo
    <span class="figura-ref">pizarra pág. 7 / notas pág. 7</span>
  </figcaption>
</figure>

Esta es la primera diferencia de fondo con Dynamo. Dónde va cada cosa no se infiere de un anillo ni lo saben los nodos mismos: hay una base de datos aparte con los rangos, y cada rango dice a qué grupo de storage nodes pertenece. Tampoco hay preference list construida avanzando por un anillo: el rango está conectado directamente con sus tres storage nodes, y así se sabe dónde vive cada partición.

## Tres nodos que no son casualidad

Que los storage nodes de cada rango sean tres no es casualidad. Forman un grupo de replicación que, según el paper, usa multi-Paxos. Como no vimos multi-Paxos, podemos suponer que corren Raft: para lo que nos importa es bastante equivalente, y todo lo que sabemos de Raft se aplica igual.

## El recorrido de un get y de un put

Con las dos piezas presentadas, veamos el recorrido de un request completo. El cliente lo manda y llega al request router. El router, que por sí solo no sabe dónde vive cada clave, le manda al partition metadata system la clave hasheada —con MD5, por ejemplo—, y este le responde en qué tres storage nodes está.

Si es un get, el router se lo manda a uno cualquiera de esos tres, que responde, por defecto, con lo que tiene. La consecuencia es grande: por defecto la lectura no es linealizable, no es fuertemente consistente. Nadie buscó al líder ni armó un quórum de lecturas; se le preguntó a una réplica y se devolvió lo que tenía.

Si es un put, todo es igual hasta que el router se lo manda a un storage node. Ahí hay dos casos conocidos. Si llega al líder, este se lo manda a los otros dos, responden, se forma el quórum y contesta. Si llega a uno que no es líder, ese le reenvía el put al líder, que hace lo de siempre. Es la misma estrategia de Raft, y es lo elegante del asunto.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el recorrido completo de un put — el cliente llega al request router, el router consulta el partition metadata con MD5 de la clave, y manda el put al storage node líder, que lo replica en las otras dos réplicas del grupo
    <span class="figura-ref">pizarra pág. 7</span>
  </figcaption>
</figure>

## Adentro de un storage node

Por dentro, un storage node tiene dos piezas que ya conocemos de Raft.

Una es un **write-ahead log**, que es justamente lo que se replica con los otros pares del grupo. La otra es un **B-tree**, donde terminan guardados los datos, porque es fácil de acceder y resuelve rápido gets y puts. No es esencial que sea un B-tree —podría ser un hash gigante, o cualquier estructura que resuelva el acceso por clave en un puñado de saltos de disco—, pero el conjunto es el mismo que en Raft: una mitad es el log replicado y la otra es la aplicación con sus datos, ambas dentro de la misma máquina. Nosotros lo dibujábamos invertido; en el paper aparece en horizontal.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    figura 2 del paper de DynamoDB — el interior de un storage node: el write-ahead log replicado y el B-tree donde viven los datos
    <span class="figura-ref">del paper, referenciada en notas pág. 7</span>
  </figcaption>
</figure>

Recapitulando las diferencias con Dynamo: no hay relojes vectoriales, no hay sloppy quorum, no hay nada de eso. DynamoDB es básicamente un conjunto de grupos de replicación, cada uno replicado con un algoritmo símil Raft, que con el request router y el partition metadata system se comporta como una gran unidad.

---
