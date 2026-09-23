---
title: "6. Transacción y reintentos"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 6
---

# 6. Transacción y reintentos

La solución a este primer problema ya la conocemos: una transacción. En
[`2-basic-service-tx`](https://github.com/fiubaTA050/replication-consistency/tree/2-basic-service-tx)
los dos writes van entre un `BEGIN` y un `COMMIT`, y ante cualquier error se hace `ROLLBACK`. La
transacción es atómica, todo o nada, y con aislamiento `SERIALIZABLE` las transacciones se comportan
como si se ejecutaran una detrás de otra, sin superponerse. Cada base tiene sus detalles y sus anomalías
según el nivel de aislamiento elegido, pero no es el foco de la materia.

```js
await client.query('BEGIN ISOLATION LEVEL SERIALIZABLE');
// SELECT del producto, UPDATE del stock, failRandomly(), INSERT de la compra
await client.query('COMMIT');
// ...
} catch (error) {
    await client.query('ROLLBACK');
    throw error;
}
```

Cabe preguntarse si el `ROLLBACK` explícito es necesario, porque una transacción que nunca llega al
commit no se confirma. Depende de la base, del cliente y de cómo manejemos la conexión: si al fallar la
sesión se cierra, el rollback es implícito, pero con un pool la conexión vuelve al pool con la
transacción abierta si no la cerramos. Hay que leer el manual del cliente que usamos. Con el rollback,
ahora la falla dentro de la transacción deja la base intacta y la API responde `500`: stock y compras
siempre coinciden.

Como la red y el servidor fallan, este branch también agrega reintentos en el frontend: hasta tres
intentos automáticos, con una pausa entre ellos, y un botón para volver a intentar. En el diálogo de
compra se ve cada intento fallido y el que finalmente funcionó. Por ahora los reintentos son inofensivos,
porque una compra que falló no dejó rastro; enseguida veremos que eso deja de ser cierto.

---
