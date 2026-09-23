---
title: "1. Replicación asincrónica"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 1
---

# 1. Replicación asincrónica

Esta práctica baja a tierra lo que vimos sobre replicación y consistencia. Todo el código está en el
repositorio de la materia, [fiubaTA050/replication-consistency](https://github.com/fiubaTA050/replication-consistency),
organizado como una secuencia de branches: cada uno agrega un paso sobre el anterior y trae en su
README los comandos para reproducirlo. Solo hacen falta Docker con Compose y Node.js. Usamos Postgres
porque es una base que todos conocemos, pero conviene no perder de vista que estamos mirando una
implementación particular. Cada base replica de una forma ligeramente distinta; lo que no cambia es
que tiene que definir un orden y elegir entre replicar de forma sincrónica o asincrónica, y cualquiera
de las dos decisiones trae consecuencias.

Empecemos por recordar cómo replica Postgres. Tenemos dos nodos, A y B: A es el primario y B la
réplica. Toda escritura va a A, y A la registra en su *write-ahead log*, el WAL. El WAL sirve para
reconstruir el estado si el nodo se cae, pero nos da algo más importante para replicar: un orden
único. No importa cuánta concurrencia tenga la base, cada transacción termina ocupando una posición en
el WAL, y quien replique siguiendo ese log aplica los cambios siempre en el mismo orden. Sin orden no
hay replicación consistente posible. Y el orden es único justamente porque todas las escrituras pasan
por un solo nodo: en cada instante hay uno solo que decide qué va primero.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    nodos A (primario) y B (réplica); A escribe su WAL y B lo consume en orden — pizarrón en clase
  </figcaption>
</figure>

El repositorio levanta los dos nodos con Docker Compose, en `docker/async`. Cada uno tiene su volumen,
así que un container puede morir y volver a prenderse sin perder su estado. A crea una tabla `items`
muy simple —un id autoincremental y un nombre— y una *publication*, que declara qué tablas se
publican para replicar. Su configuración le dice que no espere a nadie al hacer commit: cada
transacción se confirma en A y se envía a la réplica cuando se pueda, mientras A sigue trabajando.

B tiene una particularidad de Postgres: la replicación lógica copia filas, no esquema. Todo el DDL lo
tiene que crear B por su cuenta; si la tabla no existe del lado de B, la replicación no funciona. Además
crea una *subscription* que apunta a la publication de A:

```sql
CREATE TABLE items (
    id   SERIAL PRIMARY KEY,
    name text NOT NULL
);

CREATE SUBSCRIPTION items_sub
    CONNECTION 'host=postgres-a port=5432 user=postgres password=postgres dbname=appdb'
    PUBLICATION items_pub
    WITH (copy_data = true, streaming = on);
```

¿Por qué querríamos que A no espere la confirmación de B? La primera respuesta es la velocidad: el
commit no paga el ida y vuelta hasta la réplica. La segunda es más importante: la **disponibilidad**.
Si B está muerto, quien escribe en A no se entera. Es una decisión que se toma al diseñar el sistema, y
tiene una aritmética clara: cuantas más piezas tienen que estar disponibles a la vez para completar una
operación, más difícil es prometer un percentil alto de disponibilidad o de latencia. Si la escritura
depende de A y de B, el sistema es menos disponible que cualquiera de los dos por separado. Con
replicación asincrónica, la caída de B no afecta a las escrituras. A sigue siendo un punto único de
falla, así que no es una maravilla, pero ganamos un poco.

## Las demos

Levantamos todo y abrimos una sesión de `psql` en cada nodo. En B dejamos una consulta que se repite
cada segundo, así vemos llegar los cambios:

```bash
cd docker/async
docker compose up -d
docker exec -it async-postgres-a-1 psql -U postgres -d appdb
docker exec -it async-postgres-b-1 psql -U postgres -d appdb
```

```sql
SELECT * FROM items ORDER BY id
\watch 1
```

Un `INSERT` en A aparece en B casi de inmediato. La primera prueba interesante es matar B mientras A
sigue escribiendo. Usamos `docker rm -f`, que mata el proceso sin *graceful shutdown*, como una falla
real; el volumen sobrevive, así que al volver a prenderlo recupera los datos confirmados:

```bash
docker rm -f async-postgres-b-1
# en A: INSERT INTO items(name) VALUES ('mientras B está muerto');
docker compose up -d postgres-b
```

A responde sin esperar a nadie, y cuando B vuelve recibe todo lo que se perdió. La segunda prueba
muestra el costo. Insertamos algo en A que B alcanza a recibir, matamos B, hacemos más cambios en A y
matamos también A. Si ahora prendemos solo B, los últimos cambios no están: existen únicamente en el
disco de A. B intenta reconectarse sin éxito hasta que A vuelve, y recién entonces, unos segundos
después, recibe lo que le faltaba:

```bash
docker rm -f async-postgres-b-1
# en A: INSERT ... ; UPDATE ...
docker rm -f async-postgres-a-1
docker compose up -d postgres-b    # B no tiene los últimos cambios
docker logs -f async-postgres-b-1  # B intenta reconectarse a A
docker compose up -d postgres-a    # a los ~5 s B los recibe
```

Para poder hacer estas pruebas, A y B tienen que prenderse y apagarse de forma independiente. En clase
eso no pasó: B tenía un `depends_on` sobre A con un healthcheck, pensado para que B no arrancara antes
que A, y `docker compose` respetaba la dependencia prendiendo también A cada vez que pedíamos prender
solo B. Es una configuración razonable para producción y una trampa para una demo. El repositorio la
reemplaza por un script que corre solo en el primer arranque de B y espera a que A acepte conexiones
antes de crear la subscription; mientras A corre sus scripts de inicialización solo escucha por socket
local, así que esperar la conexión TCP también garantiza que la publication ya exista. Después de eso,
B se reconecta solo cada vez que A vuelve.

La conclusión de esta parte es un tradeoff. La replicación asincrónica mejora la disponibilidad de A y
la latencia de sus escrituras, que no esperan a nadie. A cambio, B es eventualmente consistente, y si A
muere antes de replicar y no se puede recuperar, esos datos se pierden. Según el caso de uso puede ser
aceptable, pero el riesgo existe.

---
