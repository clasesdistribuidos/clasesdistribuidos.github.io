---
title: "1. Por qué un file system distribuido"
parent: "Clase 4 — Google File System"
nav_order: 1
---

# 1. Por qué un file system distribuido

El Google File System viene inmediatamente después de MapReduce porque los dos están íntimamente relacionados. Los papers salieron con poco más de un año de diferencia —el del GFS en octubre de 2003, el de MapReduce en diciembre de 2004—; en qué orden se construyeron internamente es otra cuestión, sobre la que Google nunca fue demasiado explícito. La relación es de dependencia directa: MapReduce usa el GFS como infraestructura fundamental para compartir archivos.

Hay algo que resulta evidente apenas uno empieza a implementarlo. Cada mapper y cada reducer producen archivos, y aparece de inmediato la pregunta de cómo se los comparten. Durante el shuffle se los transfieren directamente, de mapper a reducer. Pero en los dos extremos del proceso la historia es otra: cuando los mappers leen el input y cuando los reducers escriben el output, están leyendo y escribiendo sobre un file system distribuido. Ese file system es el tema de esta clase.

Un file system distribuido es, a grandes rasgos, lo que uno se imagina: la abstracción que ofrece imita de cerca la de Unix, un árbol de nombres y archivos que son grandes tiras de bytes sin mucha estructura, exactamente lo que tiene el file system de cualquier máquina. No es una base de datos: un archivo no va a tener registros, ni índices, ni un esquema declarado; la estructura interna, si hace falta, la arma quien lo use.

Eso es precisamente lo que Google terminó haciendo. Sobre este file system armó un sistema de base de datos que en consecuencia también resultó distribuido, Bigtable, que sigue existiendo hoy tanto de uso interno como ofrecido públicamente en su nube. No sabemos cuánto habrá cambiado por dentro, pero en su momento era lo que le agregaba encima las estructuras necesarias para acceder a registros directamente. Fue uno de los primeros sistemas de los que hoy llamamos NoSQL, y no lo vamos a estudiar en esta clase.

Sí vamos a estudiar el GFS. No es el más fácil de los sistemas de storage, pero es un buen ejemplo, y en él nos vamos a topar con todo lo que vimos la clase pasada: sharding o particionado, replicación, un capítulo enorme de consistencia —la del GFS es quizá demasiado relajada— y algo que, más que tolerancia a fallas, es recuperación automática. La clase pasada tratamos todo eso en el plano teórico; ahora vamos a ver ejemplos concretos de cada una de esas piezas.

Ahora bien, ¿por qué no usar un file system común en lugar de construir uno distribuido? La respuesta está en los requisitos que tuvieron los ingenieros de Google.

Uno de los más básicos era un file system global, en el sentido de global y en el de cómodo: poder compartir archivos sin tener que especificar la máquina, sin preocuparse por en qué máquina estaba tal cosa. Por dentro va a ser importante saber dónde está cada fragmento de dato, pero eso lo querían abstraer.

Una característica de esos archivos —los que iban a producir con MapReduce y alguna otra herramienta que tenían— es que iban a ser muy grandes. El paper habla de varios gigabytes. Hoy puede parecer poco, pero a principios de los 2000 archivos de ese orden eran enormes. Como tenía que soportar ese tamaño, el file system tenía por fuerza que ser escalable, y en lo posible de forma horizontal: agregar máquinas al problema y que el problema se resuelva.

Después, como iba a ser grande y estar distribuido en muchos lugares, con muchas máquinas ejecutando jobs que pueden pasar mucho tiempo corriendo, necesitaba su propia tolerancia a fallas además de la que MapReduce ya tiene. Y ahí hay dos sentidos que conviene separar. Uno es la disponibilidad. El otro, igual de importante, es que no se pierdan los datos: una vez que guardamos un dato y el sistema responde que la operación fue exitosa, queremos saber que quedó razonablemente seguro. La regla —configurable, pero es la que se usa— es que cada dato se guarda en tres máquinas distintas, tres discos rígidos. Eso cuesta el triple de disco, un 200 % de sobrecosto sobre el dato útil, y es el precio que aceptan pagar para no perderlo. Es el tipo de tolerancia a fallas principal que vamos a encontrar en todas las clases sobre sistemas de storage.

El siguiente requisito ya lo tocamos en alguna de las primeras clases: lo querían construir ellos, no comprarle un sistema carísimo y sofisticado a uno de los grandes proveedores. Querían commodity hardware, máquinas que uno puede adquirir por internet —setenta discos de un mismo modelo y un motherboard—, conectarlas todas y montar el sistema encima. Hoy eso se usa mucho y es prácticamente lo que tienen internamente los proveedores de cloud; en esa época era una innovación, seguramente por la escala que sabían que iba a alcanzar el sistema: cientos o miles de máquinas.

Queda un requisito más, y va a pesar en todo el diseño: el sistema está orientado a batch. Un proceso batch es el típico trabajo grande que corre —no necesariamente a la noche, aunque uno siempre se lo imagine así—, toma muchos registros, los procesa y va generando el output. Es lo contrario de interactivo, de tiempo real o de streaming: el ejemplo canónico es el proceso que corren los bancos a la noche para consolidar datos.

Y esos procesos comparten una característica, con pocas excepciones: leen lo que podríamos llamar tablas o listas de datos, que están en los archivos, y generan otras listas de datos. MapReduce es exactamente eso, y ellos se dieron cuenta. Quisieron aprovecharlo construyendo un sistema de archivos muy orientado a esa operación, la que llamaron append: agregar cosas al final de los archivos. Eso es lo que este sistema tiene que tener optimizado.

Y queda una última razón, la que justifica estudiarlo tanto: funcionó. No fue un sistema teórico, sino lo que hizo que Google funcionara durante años, con commodity hardware y a escalas enormes, y le permitió construir encima otros sistemas, Bigtable entre ellos. Después lo evolucionaron a Colossus, sobre el que circulan algunos artículos sueltos, pero con el que fueron mucho más cerrados que con el paper del GFS. Más adelante vamos a hablar también de lo que podrían haber mejorado del diseño original.

---
