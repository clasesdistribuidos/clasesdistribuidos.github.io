---
title: "13. Semánticas de entrega"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 13
---

# 13. Semánticas de entrega

Queda el segundo pedido de producto: no inundar al usuario de notificaciones. Repasemos las semánticas
de entrega. *At-most-once*: podemos perder datos pero nunca duplicarlos. *At-least-once*: podemos
duplicar datos pero nunca perderlos. ¿Y *exactly-once*? No es real. Nuestra intuición dice que existe
porque dentro de un programa, al llamar a una función, se ejecuta exactamente una vez; en un sistema
distribuido, si enviamos un mensaje y no recibimos respuesta, no podemos saber qué pasó. Existen
nombres cercanos, como *exactly-once processing* o *effectively-once*, que describen algo distinto:
entregas at-least-once combinadas con deduplicación del lado de quien procesa, que es justamente la
idempotencia.

Para las compras resolvimos la duplicación con idempotencia. Para las notificaciones no podemos:
lamentablemente, muchas APIs de push notifications y de envío de mails no son idempotentes, así que un
reintento después de un `500` puede duplicar el mensaje, porque no sabemos si el primero se envió. Frente
a una dependencia no idempotente tenemos dos opciones, y hay que elegir una: at-most-once o
at-least-once. Un at-least-once sin límite puede spamear a un usuario para siempre si algo falla en
bucle, así que en la práctica se lo acota. Con un máximo de reintentos, si se agotan los intentos el
mensaje puede perderse, y qué hacer en ese caso es una decisión particular de cada negocio.

[`8-notification-delivery-semantics`](https://github.com/fiubaTA050/replication-consistency/tree/8-notification-delivery-semantics)
lo implementa. El notifier tiene un `failRandomly()` después de enviar la notificación y antes del ACK:
el proceso muere, Docker lo reinicia (`restart: unless-stopped`) y Postgres le reenvía todo desde el
último ACK. Para acotar los envíos, el intento se registra **antes** de enviar en una tabla de intentos
cuya clave es el id de la compra, que ya es único; si el proceso muere después de enviar, el intento
igual cuenta. Esa tabla no necesita estar ligada a la de compras, e incluso podría vivir en otro tipo de
base o de storage.

```sql
CREATE TABLE notification_attempts (
    purchase_id int PRIMARY KEY,
    attempts    int NOT NULL
);
```

```js
const attempts = await registerAttempt(purchase); // INSERT ... ON CONFLICT DO UPDATE ... RETURNING attempts
if (attempts > MAX_ATTEMPTS) {
    return;                                       // se agotaron los intentos: se descarta
}
await notify(purchase);
failRandomly();                                   // enviada pero sin ACK: al reiniciar se reenvía
```

En los logs del notifier se ven los crashes y, cuando una compra agota sus tres intentos, que se
descarta. En ntfy llegan notificaciones duplicadas, pero nunca más de tres por compra.

---
