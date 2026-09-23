---
title: "3. Replicación sincrónica"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 3
---

# 3. Replicación sincrónica

La versión sincrónica, en `docker/sync`, es casi idéntica: misma tabla, misma publication, misma
subscription. El cambio está en un parámetro de A que dice que el commit es sincrónico:

```sql
-- Sync: cada COMMIT en A espera a que B (items_sub) confirme el flush.
ALTER SYSTEM SET synchronous_standby_names = 'FIRST 1 (items_sub)';
ALTER SYSTEM SET synchronous_commit = 'on';
SELECT pg_reload_conf();
```

Con los dos nodos arriba, los datos se replican igual que antes, y en A podemos confirmar que B figura
como réplica sincrónica:

```sql
SELECT application_name, sync_state FROM pg_stat_replication;
```

La diferencia aparece al matar B. Un `INSERT` en A queda colgado: no falla ni termina. Desde otra
sesión podemos ver que está esperando a la réplica:

```bash
docker rm -f sync-postgres-b-1
# en A: INSERT INTO items(name) VALUES ('esperando a B');   -> queda bloqueado
docker exec -it sync-postgres-a-1 psql -U postgres -d appdb \
  -c "SELECT pid, wait_event, query FROM pg_stat_activity WHERE wait_event = 'SyncRep'"
```

Como no configuramos ningún timeout, espera para siempre y ni siquiera devuelve un error. No es una
buena idea en un sistema real: todo lo que sea sincrónico debería tener un timeout. Cuando B vuelve, el
`INSERT` bloqueado se destraba y termina, y B tiene el dato:

```bash
docker compose up -d postgres-b
```

El WAL, el slot y el LSN siguen estando; lo nuevo es que A no le confirma el commit al cliente hasta
que B dice que lo tiene guardado. Si agregamos un nodo C, también sincrónico, las esperas pueden ir en
paralelo, así que la latencia no crece linealmente; con máquinas cercanas y parecidas puede ser casi la
misma. Lo que sí se degrada rápido es la disponibilidad: ahora cualquier réplica que se cae detiene las
escrituras, y los percentiles se multiplican en contra.

A cambio obtenemos una promesa fuerte: todo lo que A confirmó está también en B, así que si A se rompe
sin arreglo, B tiene toda la información y puede convertirse en el nuevo primario sin perder nada. Una
réplica así se llama *standby*: un nodo listo para salir a la cancha, que permite hacer failover
automático cuando A muere. Para un banco, perder el último pedacito del WAL no es aceptable; para un
juego, perder el último ítem de alguien puede serlo o no. Depende de cuánto importe la consistencia en
ese caso de uso.

El standby tiene un costo que conviene mirar. Si no recibe consultas —y como solo A acepta escrituras,
en muchos esquemas no recibe ninguna— estamos pagando doble disco, doble CPU y doble memoria por algo
que no usamos, que solo espera. Es lo que pasaba con RDS Multi-AZ de Amazon en su versión clásica:
costaba exactamente el doble y no daba el doble de capacidad, porque el standby no atendía consultas;
replicaba a nivel de almacenamiento y solo entraba en juego en el failover. Es la misma idea que el
*shadow master* de Google File System: una réplica que está ahí sin mejorar el rendimiento, para cuando
haga falta. La alternativa es usar las réplicas para leer, que es el tema de la próxima sección.

También podemos mezclar. Una réplica sincrónica para los datos transaccionales, donde hay que sostener
invariantes del negocio (el saldo de una cuenta no puede quedar negativo) y no podemos perder nada, y
otra asincrónica, un poco atrasada, para consultas pesadas de analytics, donde el atraso no importa.
Pero el failover complica a las réplicas asincrónicas. Si el nuevo primario define su propio WAL y sus
propios LSN, las réplicas que consumían de A pierden su posición y dejan de replicar. En la versión
estándar de Postgres, hasta hace muy poco, la respuesta era empezar de nuevo, sin nada automático.
Algunas implementaciones y versiones nuevas comparten el WAL o los LSN entre las réplicas sincrónicas
para evitarlo. Aun así, para un sistema cuya prioridad es seguir vendiendo, perder las réplicas
asincrónicas por un rato puede ser un buen tradeoff: al menos ya no hay un punto único de falla, solo
un poco de downtime hasta detectar que A murió y pasar a B.

## La promesa real de Postgres

La promesa merece una precisión. Si cancelamos el `INSERT` bloqueado (con Ctrl+C, con
`pg_cancel_backend` o por un timeout del cliente), Postgres responde con un `WARNING`: la transacción
ya quedó confirmada localmente en A, pero puede no haberse replicado. Mientras el `INSERT` espera a B,
las demás sesiones no ven la fila; apenas se cancela la espera, la fila es visible y consultable en A
aunque B no la tenga. B la recibe cuando vuelve, pero si A se pierde antes, esos datos se pierden, y
alguien pudo haberlos leído y actuado en base a ellos. Lo mismo pasa si A se cae durante la espera: al
recuperarse, la transacción aparece confirmada sin haberse replicado. Da igual que el `INSERT` sea
suelto o esté dentro de un `BEGIN … COMMIT` explícito: lo que espera a B es siempre el commit.

No es un descuido sino una limitación implícita de la replicación nativa de Postgres: para replicar, A
primero tiene que confirmar el commit en su WAL, así que siempre hay un momento en que A tiene el dato
y B no. La promesa correcta es entonces más débil: **toda transacción cuyo commit fue confirmado al
cliente** está en A y en B. Un commit sin confirmar tiene un resultado incierto, y lo correcto es
reintentarlo de forma idempotente, que es el tema de la segunda mitad de la práctica. Existen
implementaciones y herramientas que prometen más: sistemas de consenso como Raft, donde un cambio
recién se considera confirmado —y visible— cuando lo tiene la mayoría de los nodos, y servicios
administrados como los clusters Multi-AZ de RDS con standbys legibles, cuyo commit espera la
confirmación de al menos un standby. AWS puede ofrecer standbys sin pérdida de datos porque cambia lo
que hace Postgres de forma nativa: RDS Multi-AZ replica de forma sincrónica a nivel de almacenamiento, y
Aurora reemplaza el almacenamiento por uno distribuido, así que un commit nunca queda escrito en un solo
lugar.

---
