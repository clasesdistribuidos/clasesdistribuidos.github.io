---
title: "7. La notificación y la transacción"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 7
---

# 7. La notificación y la transacción

Producto trae un requerimiento nuevo: por cada compra hay que enviarle una push notification al
usuario. Usamos [ntfy.sh](https://ntfy.sh), un servicio donde cualquiera puede suscribirse a un tema
(`ta050`) desde la aplicación del teléfono y recibir lo que se publique ahí. Enviar una notificación es
un `POST` HTTP; los detalles no importan. Lo que importa es dónde ponemos esa llamada.

La primera idea, la que propondría cualquier asistente de código, es ponerla dentro de la transacción,
justo antes del commit. Es lo que hace
[`3-basic-service-notifications`](https://github.com/fiubaTA050/replication-consistency/tree/3-basic-service-notifications),
con `failRandomly()` entre la notificación y el commit:

```js
await client.query('INSERT INTO purchases ...');

// I/O dentro de la transaction: la conexión y los locks quedan tomados mientras esperamos a ntfy
await notify(userId, products[0], comment);

// notificación enviada, pero la transaction todavía puede fallar
failRandomly();

await client.query('COMMIT');
```

Funciona en la primera prueba, pero tiene dos problemas serios. El primero es de recursos: **una
transacción de la base solo debería hablar con la base**. Mientras esperamos la respuesta de un sistema
externo, la transacción mantiene tomados una conexión y los locks de las filas que modificó, y la base
tiene que seguir sosteniendo las promesas de aislamiento de una transacción abierta. Si el sistema
externo tarda diez segundos, reservamos recursos caros de la base durante diez segundos mientras solo
esperamos I/O. Eso no escala. Con muchas compras concurrentes el pool de conexiones se agota y las
compras del mismo producto quedan esperando el lock de la fila; es un antipattern clásico, y el síntoma
típico en producción es un monitor de la base lleno de filas bloqueadas por transacciones que están
hablando con otros sistemas.

El segundo problema es de consistencia, y es el más engañoso: poner la llamada dentro de la transacción
no la vuelve atómica. El servicio de notificaciones y la base no comparten ninguna transacción, ni un
two-phase commit ni nada parecido; que una operación funcione es independiente de que funcione la otra.
Es una de las grandes mentiras que aparecen en producción: "pero si lo puse dentro de la transacción".
Recorramos todas las ubicaciones posibles, sabiendo que el proceso puede morir en cualquier línea:

Si notificamos **antes o dentro** de la transacción y después el commit falla, el usuario recibió la
confirmación de una compra que no existe. Es el peor escenario: le dijimos que compró y no compró nada.
Y con los reintentos del frontend, cada intento fallido envía otra notificación para una sola compra.
Hay una variante más sutil incluso sin fallas: si el usuario recibe la notificación y va a consultar la
compra antes de que el commit termine, no la encuentra. Es otra forma de no tener *read your writes*: si
le dijimos que algo existe, tiene que existir cuando lo pida.

Si notificamos **después** del commit y el proceso muere entre el commit y el envío, la compra existe y
nunca se notifica. Como mucho notificamos una vez, o ninguna: la entrega es *at-most-once*. A diferencia
de las otras opciones, esto puede ser una decisión válida. Podemos preguntarle a producto si la
notificación es un efecto secundario que a veces puede no ocurrir; si la respuesta es que sí, terminamos.
Pero si la respuesta es que al menos una notificación tiene que llegar, por ejemplo por razones legales,
no hay ubicación que funcione.

Tampoco ayuda cambiarle el nombre al problema. Si en vez de enviar la push publicamos un evento en una
cola, seguimos escribiendo en un sistema distinto de la base, que falla de forma independiente y no
comparte la atomicidad de la transacción. ¿Y si después del commit reintentamos la notificación en un
`while (true)` hasta que funcione? El ciclo no nos promete nada, porque el proceso puede morir en
cualquier momento, incluso entre el commit y el primer intento. Por más veces que iteremos, la
transacción y la notificación siguen ocurriendo por separado; no existen como un todo.

---
