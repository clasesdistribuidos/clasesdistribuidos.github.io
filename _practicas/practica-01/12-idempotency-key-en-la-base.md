---
title: "12. Idempotency key en la base"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 12
---

# 12. Idempotency key en la base

La implementación anterior tiene un problema grave. Estamos escribiendo en dos sistemas distintos, la
memoria del proceso y la base, sin una transacción que los una: es otra vez un **dual write**. Si el
proceso muere entre el commit y el `add`, perdimos la key. Y aunque no muera entre esas dos líneas, basta
con reiniciar el servidor para vaciar el `Set`. Lo podemos ver todavía en el branch 6:

```bash
KEY=$(uuidgen)
until curl -sf -X POST localhost:3000/api/purchases -H 'content-type: application/json' \
  -H "Idempotency-Key: $KEY" -d '{"userId":"restart","productId":2}'; do echo retry; done
docker compose restart app
curl -s -w "%{http_code}\n" -X POST localhost:3000/api/purchases -H 'content-type: application/json' \
  -H "Idempotency-Key: $KEY" -d '{"userId":"restart","productId":2}'
```

La compra se duplica. Tampoco soporta concurrencia (dos requests con la misma key pasan los dos el `has`
antes de que alguno llegue al `add`) ni réplicas del servidor, porque cada instancia tiene su propio
`Set` y basta que el reintento caiga en otra.

La solución, en
[`7-basic-service-better-idempotency`](https://github.com/fiubaTA050/replication-consistency/tree/7-basic-service-better-idempotency),
es guardar la key en la misma escritura que la compra. La tabla `purchases` suma una columna y un
constraint:

```sql
idempotency_key text,
CONSTRAINT purchases_idempotency_key_uniq UNIQUE (user_id, idempotency_key)
```

La key es única por usuario, aunque siendo un número aleatorio tan grande no cambia mucho; conviene
saber igual que las colisiones son posibles. Si el `INSERT` falla por ese constraint, la compra ya
existe y respondemos OK. El branch lo hace capturando el error de unicidad dentro de la transacción:

```js
} catch (error) {
    await client.query('ROLLBACK');
    // la key ya existe: la compra se hizo en un intento anterior
    if (error.code === '23505' && error.constraint === 'purchases_idempotency_key_uniq') {
        return true;
    }
    throw error;
}
```

En clase lo resolvimos con una alternativa propia de Postgres: `INSERT ... ON CONFLICT ON CONSTRAINT
purchases_idempotency_key_uniq DO NOTHING`, que no falla si la fila ya existe y devuelve cuántas filas
insertó; si insertó cero, era un reintento. En bases sin `ON CONFLICT` hay que capturar el error, con
cuidado de reconocer ese error y solo ese, para no responder OK ante cualquier otra falla. Lo importante
es la respuesta: idempotente no significa que el segundo pedido devuelva un `400` o un `500`, sino que
devuelve el mismo resultado exitoso, como si nada hubiera pasado. Repitiendo los comandos del punto
anterior, reinicio incluido, queda una sola compra.

Una implementación seria agrega dos cosas que el branch no tiene. La primera es **validar el payload**:
si llega una key conocida con un pedido distinto, es un error del cliente. Imaginemos que compramos un
mate con la key `123`, falla, abandonamos la pantalla y un error de programación reutiliza la misma key
para comprar yerba: el servidor respondería "ya lo compraste" por algo que nunca compramos. Los sistemas
que implementan bien la idempotencia comparan la key con las partes relevantes del pedido y rechazan las
diferencias.

La segunda es una **ventana de retención**. La idempotencia no es gratis cuando hay que persistir una
idempotency key: cada operación nueva obliga a recordar la historia de keys, y para Amazon esa historia
es enorme. Hay que acotarla en tiempo o en
espacio; para siempre no existe. Las transacciones de DynamoDB, por ejemplo, reciben un
`ClientRequestToken` que es válido por diez minutos. Si un consumidor se rompe un viernes a la noche y
reintenta todo el fin de semana, diez minutos no alcanzan, y el lunes tenemos mil compras en lugar de
una. La ventana tiene que cubrir el peor escenario de reintentos, y es una definición de cada producto.

No todas las operaciones necesitan una key. Borrar es naturalmente idempotente: si quitamos un producto
de un carrito con un `DELETE` por usuario y producto, repetirlo mil veces da el mismo resultado, gratis y
sin guardar nada. (Un `DELETE` que responde `400` porque el recurso ya no existe es una mala API: el
objetivo era que no estuviera, y no está.) Lo mismo un update que pisa un valor, como cambiar el nombre
de usuario, o un upsert por id: el último gana, y reintentar lleva al mismo lugar. Es más barato y, sobre
todo, más simple de mantener que ponerle una key a todo.

Tampoco siempre hay que persistir la key. Si nuestro servicio no tiene base y solo llama a otra API que
es idempotente —naturalmente o por su propia idempotency key—, alcanza con pasarle la key: la
idempotencia de la UI se transmite a través nuestro. Si llamara a dos APIs, estaríamos otra vez en un
dual write. Cuando derivamos una key nueva para el siguiente eslabón, tiene que ser **determinística**:
en un sistema bancario donde todas las operaciones de mutación exigían una idempotency key larga, la
regla era construirla a partir de datos del pedido original, nunca de un número aleatorio ni del reloj,
porque cada reintento generaría una key distinta y dejaría de deduplicar. Y si la API de abajo no es
idempotente, la decisión vuelve a ser nuestra, que es el tema de la próxima sección.

---
