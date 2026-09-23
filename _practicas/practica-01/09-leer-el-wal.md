---
title: "9. Leer el WAL"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 9
---

# 9. Leer el WAL

Volvamos a la replicación asincrónica, pero con un cambio: en lugar de otro Postgres, del otro lado va
un programa nuestro. Postgres permite que cualquier cliente consuma el WAL por *logical replication*,
con el mismo mecanismo de publication, replication slot y LSN que usa B. No todas las bases exponen su
log así: algunas lo ofrecen como un stream público en un formato propio, sin dejarnos tocar nada
interno. Poder leer el estado interno de la base abre un mundo de posibilidades.

En [`4-wal-reader`](https://github.com/fiubaTA050/replication-consistency/tree/4-wal-reader), el
directorio `wal-reader/` es un cliente en Node que usa una librería para no implementar el protocolo a
mano. Se conecta a A (el Postgres de `docker/async`, que ya crea el slot `node_wal_reader`), recibe
cada evento del WAL con su LSN, lo imprime, y solo confirma el LSN cuando apretamos Enter:

```bash
cd docker/async && docker compose up -d
cd ../../wal-reader && npm install && npm start
```

Un `INSERT` en `items` produce una secuencia de eventos. Primero un `begin`, con su LSN, que marca el
inicio de la transacción. Después un `relation`, que describe el esquema de la tabla y que el lector
ignora. Después el `insert`, con **todas las columnas de la fila y sus valores**: aunque nuestro
`INSERT` no incluía el id, el evento lo trae, porque cuando el cambio llega al WAL todo lo que decidió
la base (secuencias, valores por defecto, columnas calculadas) ya está escrito en disco. Por último un
`commit`, con otro LSN. Cada transacción ocupa varias posiciones del WAL, no una sola.

Para ver el ACK en acción, dejamos abierta en A esta consulta sobre los slots:

```sql
SELECT slot_name, confirmed_flush_lsn, pg_current_wal_lsn() FROM pg_replication_slots;
```

Mientras no apretemos Enter, el lector imprime los eventos pero `confirmed_flush_lsn` no avanza. Si lo
matamos y lo volvemos a correr, recibe de nuevo todo lo posterior al último ACK: nunca le dijimos a la
base que guardara nuestra posición. Recién cuando confirmamos, el LSN avanza y un reinicio ya no repite
esos eventos. Hay una sutileza: aunque el slot y el puntero los guarda A, A no puede decidir por su
cuenta avanzarlo; solo el consumidor sabe hasta dónde procesó.

Esto define la semántica del consumidor. Si procesamos un evento (por ejemplo, enviando una push) y
morimos antes de confirmar su LSN, al volver lo procesamos otra vez: la entrega es *at-least-once*, con
duplicados. Y si confirmamos el LSN **antes** de procesar, el peor escenario posible: le dijimos a la
base "ya lo tengo" sin haberlo procesado, y si morimos en ese momento, al volver seguimos de largo sin
verlo nunca. Confirmar antes convierte el at-least-once en *at-most-once*. El ACK se da cuando
terminamos de procesar, no cuando recibimos.

El Postgres de `docker/async` además tiene un `wal_sender_timeout` de 120 segundos. El *WAL sender* es
el mecanismo interno que le transmite el log al consumidor; si el consumidor no confirma ni responde
durante ese tiempo, Postgres asume que no está vivo y corta la conexión con el mensaje
`terminating walsender process due to replication timeout`.

Un detalle adicional de Postgres, que no llegamos a mostrar en clase: un ACK a mitad de una transacción
no evita que esa transacción se vuelva a enviar. Postgres reenvía entera toda transacción cuyo commit
no fue confirmado, así que confirmar el LSN de un `insert` equivale a confirmar solo hasta el commit de
la transacción anterior:

```
BEGIN  INSERT a  INSERT b (ACK)  COMMIT   -> al reiniciar llega la transacción entera
BEGIN  INSERT a  INSERT b  COMMIT (ACK)   -> al reiniciar no llega nada
```

---
