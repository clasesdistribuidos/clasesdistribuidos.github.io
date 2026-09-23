---
title: "14. Orden en el consumer del WAL"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 14
---

# 14. Orden en el consumer del WAL

Queda un problema en el consumer que no se ve a simple vista. El listener es una función `async` con
`await` adentro, y parece que procesa los eventos de a uno:

```js
service.on('data', async (lsn, event) => {
    try {
        await handle(lsn, event);
    } catch (error) {
        crash(error);
    }
});
```

Pero el `EventEmitter` de Node no espera la `Promise` que devuelve el listener: cada evento nuevo del
WAL arranca en paralelo con los anteriores. Si hacemos cinco compras seguidas, en los logs aparecen los
cinco "processing" antes que cualquier "notified", y los "notified" salen desordenados. Hay además un
efecto sobre la confiabilidad: el ACK de un commit puede ejecutarse antes de que terminen de procesarse
eventos anteriores, y si el proceso muere en ese momento, esos eventos se pierden. Ya no es
at-least-once.

Para las notificaciones el desorden quizás no importe, pero si en lugar de notificar estuviéramos
replicando datos, procesar en paralelo podría dejar la copia inconsistente. Pensemos en el stock de un
producto: el WAL tiene `stock = 5` y después `stock = 4`. Si los dos eventos se aplican en paralelo y el
primero termina último, la copia queda en `stock = 5` para siempre, aunque el stock real sea 4.

No hace falta escribir una cola propia. En
[`9-wal-consumer-order`](https://github.com/fiubaTA050/replication-consistency/tree/9-wal-consumer-order)
usamos una feature de la librería (`pg-logical-replication`) que permite procesar en orden:

```js
const service = new LogicalReplicationService(connection, {
    acknowledge: {auto: false, timeoutSeconds: 0},
    // no pasa al siguiente evento hasta que termine el listener del actual
    flowControl: {enabled: true},
});
```

Con `flowControl`, la librería espera la `Promise` del listener —el mismo `async`/`await` de antes— y
no consume ningún otro evento hasta que termine, aunque esté esperando mucho tiempo la respuesta de la
API; mientras tanto, deja de leer del socket. Repitiendo las cinco compras, "processing" y "notified"
alternan en el orden del WAL.

Esto tiene una consecuencia directa: si una llamada nunca responde, el consumer queda bloqueado para
siempre, sin ningún error. Por eso todo I/O, a la base o a cualquier sistema externo, tiene que estar
acotado en tiempo; el `fetch` a ntfy, por ejemplo, usa `AbortSignal.timeout(5000)`. Es el mismo consejo
que en la replicación sincrónica: timeouts en todo lo sincrónico.

Un detalle de implementación de Postgres, no necesario para la materia: el WAL intercala los cambios de
transacciones concurrentes, pero el *logical decoding* los agrupa y envía cada transacción completa, en
orden de commit y no de inicio; las que hacen rollback no se envían nunca.

```
WAL:      T1 BEGIN, T2 BEGIN, T2 INSERT a, T1 INSERT b, T2 COMMIT, T1 COMMIT
consumer: T2 (INSERT a), T1 (INSERT b)
```

La excepción es el modo `streaming`, en el que las transacciones grandes se envían por partes antes del
commit y sí pueden llegar intercaladas; el notifier no lo activa. No cambiamos nada por esto, porque lo
que nos interesa es el concepto general de CDC y no los detalles de una base en particular. Y es
precisamente por la cantidad de sutilezas como esta que es poco común escribir un consumer del WAL a
mano en lugar de usar una herramienta madura: Debezium es uno de los proyectos más maduros para consumir
eventos por CDC.

---
