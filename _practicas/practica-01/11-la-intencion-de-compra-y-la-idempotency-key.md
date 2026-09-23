---
title: "11. La intención de compra y la idempotency key"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 11
---

# 11. La intención de compra y la idempotency key

Producto vuelve con dos pedidos. El primero: que un usuario no duplique su compra por problemas de red.
Nadie quiere cobrarle diez veces a alguien y enviarle diez productos. El segundo: no enviar infinitas
notificaciones si el procesador de eventos tiene un error; a los usuarios no les suele gustar recibir la
misma push una y otra vez.

Empecemos por las compras. En
[`6-basic-service-idempotency`](https://github.com/fiubaTA050/replication-consistency/tree/6-basic-service-idempotency),
`failRandomly()` pasa a estar **después** del commit: la compra queda confirmada, pero el cliente recibe
un `500` y reintenta. Con los reintentos del frontend, cada falla de este tipo es una compra duplicada.
Lo podemos ver sin la UI, reintentando con `curl` hasta recibir un `201`:

```bash
until curl -sf -X POST localhost:3000/api/purchases -H 'content-type: application/json' \
  -d '{"userId":"sin-key","productId":1}'; do echo retry; done
```

¿Cómo evitamos la duplicación? La API recibe `userId`, `productId` y un comentario. El backend no puede
distinguir un reintento de una compra nueva: el usuario puede querer comprar el mismo producto dos veces
porque se le terminó. Las slides de la clase enumeran las alternativas. Podemos deduplicar por el
**payload**, como hacía Twitter al rechazar un tweet idéntico al anterior; pero eso impide las
repeticiones legítimas. Podemos deduplicar por **tiempo**, rechazando lo mismo dentro de una ventana;
pero la ventana es arbitraria y una compra repetida a propósito cae adentro. Otra forma de lograr
idempotencia es que **el cliente elija el id** de la entidad: cada reintento se refiere a la misma
entidad, y para algunas operaciones, como un upsert por ese id, eso alcanza. Es lo que hace el cliente
de Firebase: si el programa no le pasa un id, el propio cliente genera uno aleatorio localmente; el
servidor nunca lo genera. O el cliente puede enviar una **idempotency key** junto con el pedido, que es
el estándar de la industria, combinado con verificar que el payload sea el mismo.

La pregunta de fondo es quién define si dos pedidos son el mismo. Si el servidor generara el id de la
compra y el reintento ocurre porque se perdió la respuesta, el cliente nunca se enteró de ese id. La
intención, reintentar o comprar de nuevo, solo la conoce el extremo más cercano al usuario, que es donde
viven la UX y la semántica del producto. Pensemos en una transferencia bancaria: completamos monto y
destino y apretamos enviar. Si falla, la aplicación puede reintentar automáticamente, y mientras no
salgamos de esa pantalla, usa siempre la misma key, porque para nosotros sigue siendo la misma
transferencia. Si cerramos la aplicación y volvemos a empezar, la key es otra: es una transacción nueva,
y nos toca a nosotros revisar si la anterior se hizo. Si encima la lista de transferencias es
eventualmente consistente, podemos no verla, repetirla y terminar con dos. Lo mismo al revés: si la UI
comprara al primer clic, sin un diálogo de confirmación, cada clic sería una compra nueva y no habría
dónde atar la key más allá de los reintentos automáticos. Definir hasta dónde llega un reintento es
responsabilidad de la UX.

La implementación del branch sigue el formato más común: el frontend genera un número aleatorio muy
grande por compra, lo envía en el header `Idempotency-Key` —fuera del payload, para no cambiarlo— y lo
repite en cada reintento; el diálogo de compra lo muestra. El backend lo extrae del header. Del lado del
servidor, la primera versión guarda las keys en un `Set` de JavaScript, que podríamos pensar como la
simulación de una caché externa: antes de la transacción, si la key ya está, la compra es un reintento y
respondemos OK sin hacer nada; después del commit, agregamos la key al `Set`.

```js
if (idempotencyKey && seenIdempotencyKeys.has(idempotencyKey)) {
    return true;
}
// BEGIN ... COMMIT
if (idempotencyKey) {
    seenIdempotencyKeys.add(idempotencyKey);
}
failRandomly();
```

Con la misma key, los reintentos ya no duplican:

```bash
KEY=$(uuidgen)
until curl -sf -X POST localhost:3000/api/purchases -H 'content-type: application/json' \
  -H "Idempotency-Key: $KEY" -d '{"userId":"con-key","productId":2}'; do echo retry; done
```

---
