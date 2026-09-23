---
title: "4. Read replicas y read your writes"
parent: "Práctica 1 — Replicación y consistencia"
nav_order: 4
---

# 4. Read replicas y read your writes

Las réplicas también sirven para repartir la lectura. Es el primer paso habitual para escalar una base:
el primario atiende las escrituras y parte de las lecturas se mandan a réplicas, que pueden ser
máquinas más chicas. Muchos sistemas leen mucho más de lo que escriben, aunque también los hay al
revés, y hay bases preparadas para cada extremo; parte del diseño es elegir la adecuada. Una *read
replica* puede ser sincrónica o asincrónica, y la elección depende de si necesitamos ver en la lectura
siguiente lo que acabamos de confirmar, o si podemos esperar lo que tarde el LSN en llegar.

Una réplica asincrónica tiene una diferencia con el primario que suele ser pequeña y acotada, pero
existe, y produce efectos visibles. Imaginemos un carrito de compras que lee de una réplica asincrónica:
agregamos dos productos y al mirar el carrito aparece uno solo; refrescamos y aparecen los dos. O un
producto que desaparece y vuelve. A este atributo se lo llama ***read your writes***: si escribo y
leo inmediatamente después, ¿veo lo que escribí? Hay negocios que no pueden prescindir de él —acabamos
de hacer una compra y, por razones legales o de experiencia de usuario, tiene que verse— y otros que
sí: si un usuario cambia su nombre una vez al mes, mostrar el anterior durante cinco segundos no importa,
y leer de una réplica ahorra mucho.

Algunos sistemas dejan esta decisión en manos del cliente, lectura por lectura. En DynamoDB, y ya en el
paper de Dynamo, podemos pedir una lectura consistente, más cara porque consulta más nodos para
asegurarse de tener el último valor, o una lectura eventualmente consistente, más barata, que puede
devolver un dato un poco más viejo. Otros sistemas fijan la ubicación por clave: todo lo que escribe el
usuario 1 va al mismo nodo, así sus lecturas son consistentes, mientras el usuario 2 cae en otro, y la
carga se reparte. Son temas que retomaremos en próximas clases. ¿Y si permitiéramos escribir tanto en A
como en B, ambos sincrónicos? Ahí aparecen los problemas de escrituras concurrentes en distintos nodos,
que también veremos más adelante.

---
