---
title: "10. El notifier como consumer del WAL"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 10
---

# 10. El notifier como consumer del WAL

Con esto podemos resolver la notificación sin dual writes. En
[`5-basic-service-with-wal-reader`](https://github.com/fiubaTA050/replication-consistency/tree/5-basic-service-with-wal-reader),
la API solo escribe en la base; la notificación sale de un proceso aparte, el *notifier*, que consume el
WAL y envía una push por cada `INSERT` en `purchases`. La base del servicio suma la configuración para
consumir su WAL:

```sql
CREATE PUBLICATION purchases_pub FOR TABLE purchases;

SELECT pg_create_logical_replication_slot('purchases_notifier', 'pgoutput');
```

¿Por qué un proceso aparte? Recibir requests y consumir eventos tienen ciclos de vida independientes.
Podríamos correr las dos cosas en el mismo proceso, pero si una muere, el proceso necesita la
inteligencia suficiente para reiniciar todo. Separados, si el notifier muere o necesita más recursos, la
API sigue funcionando: no están conectados de ninguna forma salvo por el WAL.

La consistencia sale gratis de la transacción: una compra que hizo rollback nunca llega al WAL, así que
nunca se notifica, y una que hizo commit siempre termina notificada, porque el consumidor es durable. La
entrega es at-least-once. Para que se vea, el notifier confirma el LSN solo cada diez compras. Además de
servir para la demo, es realista: confirmar por cada transacción suele ser poco performante. El ACK se
hace en el evento `commit`, por lo que vimos en la sección anterior:

```js
async function handle(lsn, event) {
    if (event.tag === 'insert') {
        await notify(event.new);
        processed++;
    }
    // "por eficiencia" solo confirmamos cada 10 compras (en el commit de la transaction)
    if (event.tag === 'commit' && processed % 10 === 0) {
        await service.acknowledge(lsn);
    }
}
```

Si matamos el notifier con menos de diez compras desde el último ACK, al volver reenvía todas esas
notificaciones: no se pierden, pero se duplican.

```bash
cd purchases && npm install && docker compose up -d
docker compose logs -f notifier
docker rm -f purchases-notifier-1
docker compose up -d notifier
```

---
