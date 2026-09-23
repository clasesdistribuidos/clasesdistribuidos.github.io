---
title: "2. El LSN y los replication slots"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 2
---

# 2. El LSN y los replication slots

La pregunta natural después de estas demos es cómo sabe B desde dónde retomar. Postgres lo resuelve con
dos piezas internas. La publication, que ya vimos, dice qué tablas se replican: es una optimización para
que lo que viaja no incluya los cambios de todas las tablas, solo de las que interesan. La otra pieza es
el *replication slot*, que guarda en qué posición del WAL quedó cada consumidor. Esa posición se llama
**LSN** (*Log Sequence Number*); otras bases usan otros nombres para lo mismo. Si B se cae, al volver
pregunta cuál fue su último LSN y A le envía todo lo posterior.

El slot vive en A, no en B. Tiene sentido: el único que tiene el WAL es el primario. Esto crea una
dependencia fuerte con A, pero como A es el único que acepta escrituras, si A muere el sistema ya está
caído de todos modos. Es el mismo punto único de falla de antes.

Más interesante es cómo avanza el LSN. B podría confirmar cada entrada del WAL de a una: "vi esta,
pasame la siguiente". Pero cada confirmación es un ida y vuelta por la red, y esa latencia es mucho más
cara que procesar datos localmente. Lo habitual, en Postgres y en muchos otros sistemas, es trabajar
por bloques: pedir muchas entradas, procesarlas y confirmar de una vez "vi hasta tal posición". El
tradeoff aparece cuando el consumidor falla en medio de un bloque. Supongamos que B aplicó parte del
bloque y se cayó antes de confirmar el LSN. Como el LSN confirmado no avanzó, al volver B recibe otra
vez entradas que ya había aplicado. Por eso el receptor tiene que poder **deduplicar**: ser idempotente
frente a lo que le llega repetido. Ganamos mucha eficiencia en el caso normal, que es el de no fallar,
y pagamos con duplicados en el caso raro.

Deduplicar no es trivial. Si llegan dos `INSERT` de una fila con el mismo nombre, ¿son dos filas
distintas o la misma entrada reenviada? Ni siquiera podemos apoyarnos en la clave primaria, porque
Postgres no obliga a que las tablas tengan una. Lo único que identifica sin ambigüedad a cada entrada es
su posición en el WAL, y eso funciona porque A es el único que escribe ese log. Esto explica un problema
conocido de Postgres: hasta versiones recientes, al hacer un upgrade de versión mayor el WAL y los
replication slots no se conservaban. Sin esas posiciones, B no tiene cómo saber qué ya vio, y la única
salida es recrear los slots y empezar de nuevo. Los servicios administrados lo trasladan al usuario;
AWS, por ejemplo, pide recrear los slots de replicación lógica en los upgrades, con el cuidado de que
nada se escriba mientras tanto para no perder datos.

El slot tiene una contracara operativa. Mientras un consumidor no confirme su LSN, A tiene que guardar
todo el WAL desde esa posición, porque el consumidor todavía podría pedirlo. Postgres lo guarda en
segmentos grandes, justamente por eficiencia. Si un consumidor queda muy atrás —porque está caído desde
el viernes, porque está mal programado y nunca envía el ACK, o porque lo borramos y nos olvidamos de
borrar su slot—, A acumula la historia completa de cambios de la base, día tras día, hasta quedarse sin
disco. Y el síntoma suele aparecer en un lugar que no parece tener relación con la replicación. La
defensa es una alerta sobre el **lag de cada replication slot**: cuánto atraso hay entre su LSN
confirmado y la cabeza del WAL. Si ese lag crece, hay una replicación enferma, y es una bomba de tiempo.

---
