---
title: "5. El caso de uso: compras sin transacción"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 5
---

# 5. El caso de uso: compras sin transacción

La segunda parte es un caso de uso que vamos construyendo paso a paso. Los usuarios compran productos a
través de una API HTTP: un `POST` con `userId`, `productId` y un comentario libre. Por cada compra hay
que bajar el stock del producto. El `userId` es un simple nombre de usuario, para no complicar el
ejemplo; los productos son una lista fija con precio y stock. Es deliberadamente la compra más burda
posible: no hay carrito, no hay pago, se compra una unidad de un producto y listo.

La base tiene dos tablas, `products` (id, nombre, precio y stock) y `purchases` (id, usuario, producto,
comentario y fecha). El servidor está en Node sin ningún framework: un `GET /api/products`, un `GET` y
un `POST` en `/api/purchases`, y una UI estática mínima. Es la arquitectura distribuida más simple y
más común que existe, un web server y una base, y conviene entenderla bien antes de cualquier otra. El
Docker Compose de `purchases/` levanta la base, la aplicación y un túnel de Cloudflare: un túnel
temporal y gratuito que permite entrar a la aplicación desde Internet, para que más personas puedan
usarla durante la clase.

El entorno, además, es hostil a propósito. El servidor está muy flojo de papeles y se reinicia seguido
de forma inesperada: por falta de memoria, porque está en una máquina vieja o porque alguien lo
desenchufa. No es un problema exclusivo de un servidor casero; en la nube los nodos tampoco viven para
siempre. Las *spot instances* de AWS son baratas justamente porque AWS puede apagarlas cuando quiere,
con apenas dos minutos de aviso. Y los usuarios compran desde una aplicación móvil, con una conexión
intermitente: pasan por un túnel, entran a un ascensor. El pedido puede no llegar nunca, o llegar y que
la respuesta se pierda. Para simular ese entorno, el código tiene una función `failRandomly()` que lanza
una excepción la mitad de las veces, y que iremos moviendo a distintos puntos del código. La consigna es
pensar que el proceso puede morir en cualquier línea y que, aun así, tiene que poder volver a levantarse
sin romper las invariantes del sistema. Es la misma forma de pensar de la programación concurrente, con
un agravante: allá había que considerar cómo se entrelazan las operaciones; acá, además, cualquiera de
ellas puede fallar.

El branch [`1-basic-service`](https://github.com/fiubaTA050/replication-consistency/tree/1-basic-service)
implementa la compra sin transacción, con la falla entre los dos writes:

```js
await client.query('UPDATE products SET stock = stock - 1 WHERE id = $1', [productId]);

failRandomly();

await client.query(
    'INSERT INTO purchases (user_id, product_id, comment) VALUES ($1, $2, $3)',
    [userId, productId, comment || null],
);
```

Cada vez que la falla ocurre, el stock bajó pero la compra no existe. Lo vemos comparando el stock con
la cantidad de compras de cada producto, que sumados deberían dar el stock inicial:

```sql
SELECT p.id, p.name, p.stock, count(c.id) AS compras
FROM products p LEFT JOIN purchases c ON c.product_id = p.id
GROUP BY p.id ORDER BY p.id;
```

En una prueba con diez intentos sobre el mismo producto, el stock bajó diez unidades y solo quedaron
cuatro compras registradas.

---
