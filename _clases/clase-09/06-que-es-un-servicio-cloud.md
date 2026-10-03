---
title: "6. Qué es un servicio cloud"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 6
---

# 6. Qué es un servicio cloud

Si volvemos a la tabla con la que arrancamos, ya vimos todo: el consistent hashing y los relojes vectoriales en la clase pasada, y el sloppy quorum, los Merkle trees y el gossip hoy. El catálogo quedó completo, y eso es lo que hace valioso este paper: es un gran catálogo de los mecanismos que uno efectivamente termina usando cuando le toca implementar un sistema distribuido.

Queda el otro paper, el de DynamoDB. Su arquitectura es interesante, pero lo más interesante es otra cosa: es el primer servicio cloud que vamos a estudiar.

Más allá del uso comercial del término, ¿qué significa que algo sea un servicio cloud? Se entiende por contraste. Los papers anteriores eran arquitecturas que inventaba Google, Amazon, Facebook o quien fuera, y esas mismas empresas tenían que desplegarlas: poner los nodos, configurarlos y mantenerlos en su propia infraestructura.

Dynamo ilustra bien el punto. Cada equipo de Amazon que quería usarlo le preguntaba al equipo que lo había inventado cómo funcionaba; le pasaban el repositorio, o lo que fuera, y ese equipo desplegaba su propio Dynamo. Eran responsables de que funcionara, y si algo se rompía tenían que arreglarlo ellos. Por mucho tiempo, eso fueron los sistemas distribuidos.

Eso cambió mucho, porque ahora casi todo se delega a servicios cloud. Un servicio cloud es, básicamente, un sistema distribuido que opera otra organización: generalmente un proveedor de cloud como Amazon, Microsoft o Google, los tres grandes, y algunos más pequeños. Esa es la diferencia principal.

Hay otra diferencia, más filosófica. Dynamo, Google File System, MapReduce: ninguno tenía valor en sí mismo, sino que resolvía un problema. Amazon instalaba Dynamo para resolver el carrito de compras y que los clientes realizaran sus compras; de ahí obtenía sus ingresos. Dynamo era solo un componente del sistema. En un servicio cloud la relación es la inversa: el servicio mismo es lo que se vende.

DynamoDB nació justamente con ese objetivo: tomar la idea de las bases no relacionales, que había tenido muy buena recepción, y venderla como un servicio administrado por Amazon. Vamos a llegar ahí. Pero un servicio cloud tiene cuatro propiedades que lo separan de todo lo que vimos antes, y hay que mirarlas primero.

---
