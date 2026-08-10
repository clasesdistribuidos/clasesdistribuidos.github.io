---
titulo: Clase 1 — Introducción, TCP/IP y RPC
fecha: 2026-03-11
---

## 1. Qué es un sistema, y de qué está hecho

### Qué es un sistema

Cuando uno comenta que está por dar esta materia, la reacción más común es la envidia: qué bueno, qué divertido. A casi todo el mundo le entusiasma Sistemas Distribuidos, y la razón es que se la percibe como una materia unificadora. Es de las últimas de la carrera y depende de casi todo lo que vino antes. Lo curioso es que no dependa de bases de datos: no es correlativa, y probablemente debería serlo, porque vamos a ver muchas bases de datos distribuidas. Quien está cursando seguramente prefiera que las cosas queden como están —cuantas menos correlativas haya, más materias se pueden llevar en paralelo—, pero la deuda conceptual sigue estando.

Al escuchar "sistema distribuido", lo primero que uno piensa es en la red: cables, protocolos, máquinas hablando entre sí. La red va a estar, por supuesto, pero más allá de ella vamos a estar hablando sobre todo de *sistemas*. Por eso lo primero que necesitamos es una definición de sistema —algo que no es seguro que hayamos visto formalmente en ningún lugar de la carrera—, y solo a partir de ella vamos a poder decidir cuáles son los sistemas que nos interesan y de qué manera los vamos a estudiar.

La versión que vamos a usar es esta: un sistema es un conjunto de componentes interconectados que interactúan entre sí para producir un comportamiento observable en su interfaz con el entorno. Vale la pena desarmarla despacio. Lo primero que dice es que hay muchos componentes y que están interconectados: todas esas piezas hablan unas con otras. Lo segundo, y lo verdaderamente importante de cualquier sistema, es el concepto de abstracción. Si bien cada componente hace lo suyo, uno los termina viendo desde afuera como una gran unidad. Esa unidad es la interfaz que tiene el sistema distribuido, o cualquier otro sistema.

[FIGURA: óvalo con componentes interconectados por flechas; la frontera rotulada como interfaz/APIs, el adentro como lo que está en discusión y el afuera como el entorno — notas pág. 1 / pizarra pág. 1]

Lo que estamos dibujando es un diagrama genérico sobre diagramas, y lo venimos viendo desde que empezamos la facultad. La caja que representa al kernel contiene adentro el componente del file system y el de tantas otras cosas: un sistema que contiene otros subsistemas. Es algo a lo que ya estamos acostumbrados. La clave está en preguntarse para qué hacemos estos diagramas, y la respuesta es que sirven para definir la granularidad con la que vamos a estudiar las cosas —que va a resultar importante— y el nivel de abstracción en el que decidimos pararnos.

Esa interfaz que rodea al sistema recibe distintos nombres; en un sistema distribuido se la suele llamar API endpoints, o simplemente interfaz. Y lo que ese contorno nos está diciendo es cuál es el recorte que hicimos: lo de adentro es lo que estamos estudiando, lo de afuera es el entorno, que no nos interesa. Son perspectivas distintas según dónde nos coloquemos.

Cada uno de esos componentes puede ser, a su vez, otro subsistema. Vamos a ver que en un sistema distribuido es muy frecuente que no haya un mapeo directo entre estos círculos del diagrama y las computadoras que lo componen: muchas veces un sistema interactúa internamente con otro sistema entero, que ya es una complejidad en sí mismo.

### Cómo vamos a estudiar estos sistemas

Con esa definición en la mano podemos precisar cuáles son los sistemas que nos interesan. Vamos a estudiar sistemas distribuidos: sistemas en el sentido que le acabamos de dar a la palabra, pero *grandes*. No hace falta enfatizar tanto que están conectados por una red —típicamente lo van a estar—, porque la característica que verdaderamente los define es el tamaño. Y ahí está buena parte del motivo por el cual la materia entusiasma tanto: al ser grandes, tocan problemas que ya vimos por todos lados en la carrera: comunicaciones de red, los algoritmos que tiene adentro cada uno de ellos y, sobre todo, concurrencia, muchísima concurrencia, justamente porque las partes están separadas y se comunican a través de la red. Conviene anotar una advertencia desde ahora: de todo lo que aprendimos en concurrencia, algunas cosas van a servir y otras no. Hay herramientas que ya conocemos y que sencillamente no se pueden aplicar aquí, y esa diferencia va a ser una parte importante de lo que tenemos por delante.

¿Y cuál va a ser nuestro método de estudio? Van a ser papers de sistemas reales de empresas reales. La clase va a funcionar como un club de lectura técnico: vamos a leer estos papers y los vamos a discutir entre todos, y los temas de sistemas distribuidos van a ir emergiendo de esos casos de uso reales, en lugar de bajar desde una teoría previa. El primero que vamos a leer es el de MapReduce, un paper clásico de Google que se espera que leamos y entendamos antes de discutirlo en clase. La palabra "paper" puede llevar a confusión: no son papers académicos estrictos, en el sentido de un trabajo de investigación en abstracto. Son problemas de ingeniería reales que estas empresas tuvieron que resolver, y que después contaron. Se va a notar además que fueron tres las líderes de esta nueva era —Google, Amazon y Facebook son las que más innovaron—, y de ellas nos vamos a nutrir para la mayor parte de la materia. Los temas, en cambio, van a ser generales: en el programa figuran algunas cuestiones transversales que vamos a ir viendo una y otra vez, sin importar de qué sistema estemos hablando.

Todo eso lo vamos a estructurar en cuatro grandes ejes temáticos de aplicación. El primero es compute: cuando una sola máquina no soporta el trabajo, ¿cómo hacemos para particionar un cálculo gigante entre muchas máquinas? El ejemplo típico es MapReduce. El segundo es storage, y a eso le vamos a dedicar gran parte de la materia, con muchísimos papers, porque es de las cosas más difíciles de hacer; ya nos vamos a ir dando cuenta de por qué. Ahí aparecen distintas variaciones del mismo problema: file systems distribuidos, bases de datos relacionales, bases de datos no relacionales. De ahí viene también la dificultad de que bases de datos no sea correlativa; algunos la habrán cursado ya y otros no, así que vamos a dar una introducción al tema. Los otros dos ejes son los nuevos, en los que queremos profundizar y vamos a ver si nos sale. Uno es stream processing, que no se trata de streams multimedia sino de streams de datos, procesados en tiempo real o casi real, junto con todo lo que es mensajería. El otro es cloud computing, que tampoco se suele dar mucho: todas esas empresas que ofrecen aplicaciones en la nube, y qué queremos decir exactamente con eso.

Una pregunta razonable es si alguna vez vamos a tener que implementar nosotros mismos uno de estos sistemas, y la respuesta honesta es que no: difícilmente alguno de nosotros tenga que implementar DynamoDB. Son sistemas que construyen grandes equipos, y el trabajo que los funda termina recibiendo, años más tarde, los premios más altos de la disciplina. Pero al saber cómo funcionan internamente, uno puede —incluso antes de consultar cualquier herramienta— intuir cuáles pueden ser los problemas y dónde puede fallar el sistema, y cuando lo usamos desde afuera vamos a poder entender mucho mejor las garantías que nos ofrece. Un ejemplo concreto: si escribimos algo en DynamoDB y lo leemos inmediatamente después, es posible que nos devuelva un valor diferente del que acabamos de escribir, salvo que activemos un modo especial de lectura. Esa clase de comportamientos resultan misteriosos para la mayoría de la gente que los sufre, y nosotros vamos a entender por qué DynamoDB tiene consistencia eventual. Después de hacer el trabajo de Raft va a ser obvio por qué surge: va a dejar de ser mágico y va a dejar de parecer una feature, para pasar a ser, principalmente, un problema con el que hay que convivir.

*[Nota: El paper que funda el sistema es *Dynamo: Amazon's Highly Available Key-value Store*, de DeCandia et al., presentado en SOSP 2007; recibió el ACM SIGOPS Hall of Fame Award en 2017. **Dynamo** es el sistema interno que ese paper describe, y **DynamoDB** el servicio público que Amazon construyó después.]*

Hay además otras razones para leer papers, y tienen que ver menos con los sistemas distribuidos que con el oficio de ingeniero. La primera es que hay que saber leer, y no es una obviedad: se está subestimando mucho, justo ahora, la capacidad para comprender textos. Y sin embargo va a ser importante poder entender las cosas que están haciendo las inteligencias artificiales, interpretarlas bien y también alimentarlas, darles contenido de manera que hagan cosas. La segunda es saber interpretar diagramas, y aquí conectamos con lo anterior, porque los diagramas son siempre variaciones de sistemas. Si abrimos el paper de Google File System, que vamos a ver la próxima vez, y pensamos ese dibujo como un sistema, lo que tenemos es la frontera de un sistema que se llama master; esos otros de al lado son subsistemas, los chunkservers; y todo el conjunto es el Google File System. Ese tipo de lectura, y entender cómo se comunican esas partes entre sí, es lo que hay que poder sacar de un diagrama. Estas cosas se aprenden practicándolas, leyendo y tratando de entender una fuente primaria: el paper mismo, no un libro que lo explica.

La última razón es la de los patrones. Después de leer toda esa cantidad de papers vamos a ver que, si bien son sistemas diferentes, hay muchos patrones que surgen siempre. Por ejemplo, en los primeros papers siempre hay una especie de master central, coordinador o primary, que coordina cosas. Eso va a surgir naturalmente de ver varios papers, y va a quedar claro que es un patrón común, uno de tantos de ese tipo. Lo importante es descubrirlo por cuenta propia al comparar un paper con otro, y no que nos lo enumeren de antemano. Para complementar vamos a ir recomendando también algunos libros. El de esta primera clase no es un paper sino un libro, escrito por dos profesores del MIT, Jerome Saltzer y Frans Kaashoek: es mucho más básico que lo que queremos ver nosotros, del tipo de un primer curso de sistemas en general, pero tiene un par de cosas que sirven bien para una clase introductoria como esta.

*[Nota: *Principles of Computer System Design: An Introduction*, Jerome H. Saltzer y M. Frans Kaashoek, Morgan Kaufmann, 2009. De ahí sale el marco de las tres abstracciones de la subsección siguiente, y también varias de las figuras que se proyectan a lo largo de la clase.]*

### Las tres abstracciones fundamentales

Saltzer y Kaashoek tienen una idea que siempre resultó particularmente buena: organizar todo en tres abstracciones fundamentales. La observación de fondo es que los componentes que forman los distintos sistemas siempre terminan cayendo, y a veces superponiéndose, en apenas tres funcionalidades básicas. Y esto no es solo un ejercicio de ordenamiento: es lo que nos va a permitir llegar después a una definición de los sistemas distribuidos que vamos a estudiar.

La primera es la memoria, la segunda son los intérpretes y la tercera son los enlaces de comunicación. En nuestra disciplina siempre estamos ante variaciones de esas tres.

Lo primero que conviene despejar es la idea de que estemos hablando necesariamente de hardware. Si uno piensa en dispositivos de memoria, los ejemplos obvios son de hardware: la flash memory, que se llama memoria y evidentemente lo es. Pero hay cosas bastante más de alto nivel que representan exactamente la misma abstracción. El RAID, por ejemplo, esa capa de software que junta varios discos y hace que parezcan uno solo. El file system es una abstracción de memoria, y los sistemas de base de datos son, para nosotros, otra abstracción de memoria.

Si todas esas piezas son una misma abstracción, tiene que haber una esencia compartida, y esa esencia es la interfaz. Se puede interpretar que la memoria está caracterizada por una interfaz de esta forma: una operación `write(nombre, valor)`, a la que se le pasa un nombre y un valor, y otra que escribimos `valor ← read(nombre)`. Esto es muy abstracto: ese nombre puede ser una dirección en binario de la memoria física, pero también puede ser el nombre de una variable. Lo importante, la esencia de la abstracción de memoria, es que lo que uno pone ahí el sistema lo recuerda, y cuando después hace `read` le devuelve el mismo valor que le puso.

[FIGURA: ejemplos de dispositivos de memoria, de la RAM y la flash a los sistemas de más alto nivel — RAID, file system, base de datos — con la interfaz write/read al costado — notas pág. 2 / pizarra pág. 2]

En nuestro estudio, lo más parecido a esta abstracción van a ser los sistemas de storage: sistemas en los cuales queremos escribir bytes y queremos que el sistema nos los devuelva, idealmente, en el mismo orden en que se los pusimos.

La segunda abstracción es el intérprete. Lo primero que uno piensa al escuchar la palabra es, de vuelta, un procesador, un pedazo de hardware. Pero un intérprete puede ser cualquier cosa que ejecute código: desde los procesadores físicos hasta la máquina virtual de Java o Node.js. Hasta la máquina de Turing podría considerarse una abstracción de un intérprete, aunque tenga además una memoria y algunas cosas más.

¿Y qué hace un intérprete? Tiene un entorno en el cual se ejecuta, tiene un lugar donde están las instrucciones, toma una instrucción, la interpreta y guarda el resultado en la memoria. En nuestro caso va a ser el elemento que hace cosas.

[FIGURA: estructura del intérprete abstracto: la referencia a la instrucción, el repertorio y la referencia al entorno, con el ciclo de traer una instrucción, interpretarla y volver a empezar — notas pág. 2 / pizarra pág. 3]

Estas dos primeras abstracciones vienen acompañándonos desde hace tiempo: durante toda la carrera vimos distintas variaciones de intérpretes y de memorias sin llamarlas así. Aprender a programar, por ejemplo, es aprender a usar un intérprete; el lenguaje en sí podría considerarse un intérprete que usa una memoria para ir guardando cosas.

La tercera son los enlaces o canales de comunicación, y con ellos la historia cambia. Son, en principio, lo que uno correctamente puede interpretar como una red. Si la memoria tenía una interfaz fundamental que era `write` y `read`, los enlaces van a tener una que es `send` y `receive`. El `send` lleva un nombre y un buffer con lo que se quiere mandar; el `receive` lleva un nombre y un buffer donde se lo quiere recibir.

Inicialmente parecería que es exactamente lo mismo que una memoria. Pero ahí ya hay que ir más allá de la interfaz —que sí es parecida— e ir a la realidad, porque lo que suelen tener abajo los enlaces tiene semánticas muy diferentes. Para empezar, suelen ser más secuenciales. En la memoria cada nombre era una variable o una dirección; en un enlace ese nombre suele ser el nombre del canal, y por ese mismo nombre se mandan cosas una después de la otra, que llegan a veces ordenadas y a veces desordenadas.

Pero, dicho sin rodeos, los enlaces de comunicación sirven para conectar dos computadoras mediante un cable, básicamente, o mediante abstracciones de ese cable. Y al conectar dos componentes mediante un enlace físico, o no tan físico, aparecen problemas que no aparecen con la memoria. Esos links suelen ser poco confiables: se pueden romper, se pueden perder paquetes, pueden ser lentos, y el orden en que se mandan las cosas no está garantizado. En la memoria uno no tiene el problema de escribir un valor y después otro y que lleguen en desorden. Con los enlaces vamos a ver que hay maneras de solucionarlo, pero de entrada nadie nos garantiza nada. El caso extremo es todavía peor: puede perderse completamente lo que se mandó. Uno puede hacer un `send` y el que hace `receive` del otro lado no recibe nada, y también hay que recurrir a ciertos mecanismos para que eso no ocurra.

¿Por qué querríamos, entonces, una abstracción tan deficiente? Porque es inevitable: las computadoras hay que conectarlas mediante un cable, y ese cable tiene esos problemas. Vamos a ver enseguida que si vamos demasiado lejos con las abstracciones y nos olvidamos de cómo están implementadas, a veces surgen problemas, porque no funcionan como en nuestra imaginación ideal querríamos.

### Del enlace a la red

De las tres abstracciones, la última merece más detenimiento, porque los enlaces son un elemento central de esta materia. En abstracto, un enlace de comunicación es esto: un nodo, otro nodo, y la línea que los une. El enlace es esa línea, y nada más.

[FIGURA: dos nodos unidos por un enlace de comunicación — notas pág. 2 / pizarra pág. 4]

Dicho así, el dibujo no dice demasiado. Lo que hace falta saber es cómo se manifiestan esos enlaces, y en nuestro curso se manifiestan con redes. Las redes van a ser el principal tipo de enlace que vamos a usar, y la forma en que se conectan estas tres abstracciones va a ser lo que define un sistema distribuido tal como lo entendemos nosotros.

Antes hace falta un repaso breve de los modelos de redes, con una pregunta encima: cuál es el nivel de abstracción en el que vivimos nosotros, hasta dónde nos interesan pensando como sistema.

Toda clase de redes arranca por el modelo OSI, el estándar que publicó ISO. Empieza con la capa física, y encima vienen la capa de enlace, la de red, la de transporte, la de sesión, la de presentación y la de aplicación. Son tantas que casi nadie termina aprendiéndoselas de memoria: el modelo está un poco sobrediseñado. Es de suponer que a quienes se dedican a redes les importan todas esas divisiones, pero a nosotros rara vez nos hace falta tanto detalle. Esas capas se representaban además por números, del 1 al 7, y de ahí viene una expresión que se escucha todo el tiempo: cuando alguien habla de un router de capa 3 se está refiriendo a este modelo.

*[Nota: El modelo está publicado como ISO/IEC 7498-1, *Information technology — Open Systems Interconnection — Basic Reference Model*.]*

Hay un lugar donde el modelo se vuelve incómodo, y es arriba de todo: las capas de presentación, sesión y aplicación siempre aparecen mezcladas entre sí. Hay quienes dicen que HTTPS es la capa de sesión y que lo que está por encima es la capa de aplicación, y la discusión resulta francamente confusa. Desde el punto de vista de alto nivel en el que vivimos nosotros, esa subdivisión termina siendo un poco redundante.

El modelo de internet, también conocido como modelo TCP/IP, mejora bastante el panorama, y lo hace unificando. Lo primero que unifica son las dos capas de abajo, la física y la de enlace, que pasan a llamarse capa de acceso a la red. Después la capa de red sobrevive con la misma funcionalidad de siempre, encima está la capa de transporte, y arriba de todo aparece la gran unificación, que es la capa de aplicación: si buscamos un equivalente en OSI, corresponde a esas tres de más arriba tomadas juntas.

El foco de esta división se ve apenas uno mira dónde cae cada protocolo. En la capa de red está IP, y en la capa de transporte están TCP y UDP, que son los dos principales. Hay otros, por supuesto: en la capa de red vive también ICMP, el protocolo del que se vale `ping` para averiguar si una máquina responde.

Nosotros lo vamos a simplificar todavía más, porque en la práctica —y así lo plantea el libro que vamos a estar usando— son principalmente tres capas. Abajo de todo hay una capa de bajo nivel, la capa de enlace: cómo se conecta una máquina físicamente con otra. Ahí queda mezclado todo lo que es la parte física, y principalmente los protocolos de Ethernet, Wi-Fi y Bluetooth. Y aunque decepcione, eso ya se estudió: es materia de redes y no vamos a volver sobre ello.

Encima viene la capa de red, la que hace que las cosas lleguen de un lugar a otro pasando por varios de esos enlaces. Esa definición, por suerte, es consistente en los tres modelos: se trata de saltar de una red a otra para que las cosas se ruteen. El principal problema que resuelve es el ruteo de paquetes a través de una red heterogénea: algunos tramos son Ethernet, otros son Wi-Fi, y los paquetes igual llegan de un lugar a otro.

Y arriba de todo, lo que a nosotros como programadores nos interesa son las tres capas superiores tomadas juntas, que podríamos llamar end to end, porque ese es típicamente el problema que vamos a resolver. A este nivel no nos interesa tanto cómo son los frames de Ethernet ni cómo funciona el ruteo; generalmente hay otra persona en la empresa que se dedica a configurar los routers. A nosotros nos interesa que una máquina, que puede estar en cualquier lugar del universo, pueda mandarle un mensaje a otra máquina que está en otro lugar del universo. Nuestros canales de comunicación viven ahí: eso es la materia.

[FIGURA: las tres pilas de capas comparadas — OSI numerada del 1 al 7, TCP/IP con su capa de acceso a la red, y el modelo de tres capas de la materia: end to end, red y enlace — notas pág. 2 / pizarra pág. 4]

Aparece naturalmente la pregunta de cómo se llama este último modelo. No tiene un nombre demasiado célebre: es el que plantea ese libro del MIT. Y no vamos a poner mucho énfasis en el nombre, porque lo que importa es definir la perspectiva. Vamos a ver que probablemente nunca más volvamos a hablar del protocolo IP, y que vamos a asumir sin más que las cosas llegan de alguna forma. Pero sí va a resultar interesante la diferencia entre TCP y UDP, porque cuando uno está desarrollando una aplicación necesita saber si tiene la garantía de que las cosas llegan ordenadas, o si en cambio se pueden perder o llegar en cualquier orden. Eso no va a ser totalmente transparente: al final de la clase vamos a ver un ejemplo donde tenemos que usar TCP para obtener ciertas garantías. Como diseñadores de un sistema distribuido vamos a decidir hasta ahí, hasta la capa de transporte. Sobre la capa de red no va a haber mucha discusión, porque es prácticamente siempre IP, y es justamente por eso que el modelo se permite unir las dos capas de abajo.

Hay una palabra que se viene colando y que todavía no definimos. Eso que se le manda al enlace, esos bytes que viajan por el canal, es lo que vamos a llamar mensaje. Vamos a ver una y otra vez que estas máquinas tomadas en abstracto —un nodo hablando con otro nodo, en términos de comunicaciones end to end— se mandan mensajes entre sí.

Es cierto que las tecnologías pueden soportar streams, un flujo continuo que nunca termina. Pero las cosas, de alguna forma, siempre hay que dividirlas. Un archivo también podría ser teóricamente una única tira larguísima de bytes, y sin embargo en bases de datos explican que se lo suele organizar en bloques. Aquí pasa exactamente lo mismo: todos los protocolos que vamos a ver se van a intercambiar mensajes.

Un mensaje es, conceptualmente, algo abstracto: un paquete de información de alto nivel que un nodo le manda a otro. No estamos hablando de un paquete de TCP. Pueden ser de tamaño fijo o variable, muy grandes o muy pequeños, y puede haber distintos tipos. Pero la abstracción fundamental es siempre la misma.

Hay diseños de sistemas distribuidos que hacen mucho énfasis en los mensajes y hay otros que los esconden un poco más. Al final de esta misma clase vamos a ver uno que esconde el mensaje y hace que todo parezca una llamada a un procedimiento. Y hay otros, como los message oriented middleware, donde esos mensajes son explícitos. Vamos a ver que los nombres confunden, porque se usa el mismo nombre para cosas distintas; la cuestión tiene algo de filosófico, pero se va a ir aclarando sobre la marcha.

Aparece entonces la pregunta de qué diferencia hay exactamente entre un mensaje y un stream, y si un stream puede ir por TCP o debería ir por otro protocolo —más aún cuando UDP suele tener tamaño fijo y un stream se parecería a muchos paquetes UDP encadenados—. La respuesta es que TCP genera un canal por donde uno manda un stream de bytes. Se puede pensar como que uno manda bytes individuales y van llegando del otro lado: es la misma semántica que tiene escribir un archivo.

Ahora bien, cuando más adelante estudiemos streams, esos van a ser distintos de los streams de TCP. Nosotros vamos a estudiar streams de mensajes: muchos mensajes que vienen uno después de otro y que tenemos que ir procesando. Y en ningún caso, probablemente, vamos a tener algo donde no haya mensajes. Ni siquiera con los streams de video, de los que no sabemos con certeza cómo funcionan por dentro, pero donde uno se imagina que también van enviando paquetes que hay que ir armando y reproduciendo. Y la abstracción que nos provee TCP resulta muy útil justamente por eso: como es un stream de bytes, sobre él nosotros podemos mandar mensajes uno después del otro.

Hay aquí una advertencia que vale para toda la materia: se usan las mismas palabras para significar cosas distintas, y se complica todavía más porque a veces, tratándose de la misma palabra, las cosas son además parecidas. El stream de TCP no es completamente diferente del stream de mensajes que vamos a procesar con Flink: conceptualmente los dos son un flujo de datos. Pero en la práctica la diferencia se nota.

### Sockets en C

Todo esto se materializa de una manera muy concreta apenas uno se sienta a escribir código, y vale la pena verlo por lo menos una vez: un servidor y un cliente que se comunican por sockets. Quien haya programado sockets alguna vez probablemente lo haya hecho en Python; la versión que vamos a mirar es la de C, la de bajo nivel. El consuelo va por adelantado: en la materia vamos a usar Go, así que no va a haber que escribir esta clase de código. Pero estas son las system calls con las que se programan los sockets.

`[CÓDIGO PENDIENTE: servidor y cliente con sockets en C — la secuencia socket/bind/listen/accept/read/close del servidor, y socket/connect/read/close del cliente]`

La pregunta natural es cómo se hace un servidor. Del lado del servidor la respuesta es una secuencia de llamadas al sistema engorrosa para los estándares actuales, aunque conviene recordar que esta es una tecnología muy antigua y que buena parte de su forma se explica por su edad. Lo primero es llamar a `socket()`. Después hay que hacer `bind()`, que asocia ese socket a una dirección. Después `listen()`. Después `accept()`, para aceptar una conexión. Después `read()`. Y eventualmente se lo cierra con `close()`.

Lo interesante de esa secuencia es otra cuestión: aquella división de capas que acabábamos de unificar reaparece unificada también en el código. Cuando uno arma el socket le tiene que pasar `SOCK_STREAM`, y eso es decirle que queremos un socket de tipo TCP; si quisiéramos uno de tipo UDP le pondríamos otra flag, `SOCK_DGRAM`. Aun estando parados en la capa de aplicación, entonces, estamos tomando una decisión sobre la capa de transporte. Es exactamente lo que anticipábamos: como diseñadores la decisión nos llega hasta la capa de transporte, y esa elección nos toca a nosotros.

En este ejemplo estamos usando un stream porque prácticamente todas las aplicaciones que hay ahora usan TCP —salvo alguna de sensores—. Y usan TCP porque sus garantías nos facilitan enormemente la vida: que las cosas lleguen ordenadas, y que si llega algo esté garantizado que no van a faltar cosas en el medio. Eso permite sacar una cantidad de código de nuestra aplicación y pasárselo a TCP, que lo resuelve de manera automática.

El cliente no es tan interesante: también arma un socket, y también hay que decirle de qué tipo lo queremos. De ahí en adelante es más fácil, porque simplemente se conecta, después empieza a leer y eventualmente cierra.

Aquí aparece por primera vez otro de los términos que van a reaparecer con distintas interpretaciones: cliente y servidor. A nivel de sockets, a nivel de TCP, la diferencia es clara: el cliente es el que inicia la comunicación; el servidor es el que está ahí escuchando y recibe la comunicación. Nosotros vamos a hacer más adelante una interpretación más de alto nivel —conviene anticiparla ahora para que no quede descolgada—: el cliente va a ser el que pide, el que necesita algo, y el servidor el que tiene eso que hace falta y se lo da.

Cliente y servidor se dicen, además, para diferenciarlos de peer to peer, donde tenemos dos máquinas que son iguales: tienen el mismo código, tienen distinta información, pero son dos pares iguales entre sí. Lo interesante es lo que ocurre cuando esas dos máquinas se ponen a hablar: lo más probable es que se conecten por alguna red TCP/IP y por sockets, así que uno de los dos pares, visto desde el punto de vista de los sockets, va a actuar como cliente y el otro como servidor, simplemente porque una máquina se quiere conectar a la otra. Los dos niveles de lectura conviven sobre el mismo par de máquinas, y por eso todo esto resulta confuso.

El consuelo con el que abrimos sirve también para cerrar: nada de esto va a haber que escribirlo en esta materia. Con Go es mucho más simple, y de hecho con la herramienta que vamos a usar es más fácil todavía.

---

## 2. Qué es un sistema distribuido y por qué querríamos uno

### Multiprocesador contra sistema distribuido

Con todo ese preámbulo ya estamos en condiciones de definir qué entendemos por un sistema distribuido. Conviene dar esa definición al revés, empezando por decir qué *no* es, porque configuraciones posibles hay varias y no todas cuentan.

No es un sistema donde hay una memoria —memoria propiamente dicha, memoria RAM— y varios CPUs conectados a ella. Ahí estamos muy bien a bajo nivel, pero cuando tenemos varios CPUs conectados a la misma memoria, como ocurre en cualquier máquina multicore —que es como son todas las máquinas hoy—, eso es un multiprocesador y no un sistema distribuido.

Un sistema distribuido va a ser otra cosa: una memoria y otra memoria, un CPU y otro CPU, cada CPU con la suya. Lo que cambia es la conexión entre los dos, que ahora pasa a ser un enlace, una red. El dibujo es esquemático y a alguien de organización de computadoras podría no gustarle, porque los CPUs no se conectan literalmente de esa manera; pero ese enlace está ahí para enfatizar una sola cosa, la importante: este CPU no puede acceder directamente a aquella memoria. Eso no existe.

[FIGURA: a la izquierda, una memoria con dos CPUs colgando de ella, rotulado multiprocesador; a la derecha, dos pares de memoria y CPU donde lo único que une a los dos CPUs es un enlace de red, rotulado sistema distribuido — notas pág. 3 / pizarra pág. 5]

Y eso nos complica enormemente la vida. Muchas de las cosas que ya sabemos hacer dejan de valer. Cuando programamos con procesos, si bien están aislados entre sí, sabemos que podemos recurrir a memoria compartida o a otros mecanismos para que dos procesos escriban sobre la misma memoria. Cuando programamos con threads, más todavía. Aquí eso es físicamente imposible: son dos máquinas separadas y no hay forma de que una escriba en la memoria de la otra.

A lo sumo podemos armar un sistema que *simule* una memoria compartida, y va a ser eso, una simulación: el CPU siempre va a tener que pasar por el otro CPU para poder escribir en esa memoria. No tenemos un bus PCI que atraviese el data center y conecte dos memorias entre sí.

Esos son los sistemas que vamos a armar nosotros. La separación puede ser una ventaja en algunas ocasiones y una desventaja en otras, y lo que sigue es justamente ver cuáles son las ventajas.

### Escalar y tolerar fallas

¿Por qué querríamos complicarnos así? Empecemos por las razones más habituales.

La primera es la escalabilidad. Lo que queremos es un sistema que se pueda hacer más grande, y hay dos maneras de darle más potencia: más capacidad de procesar datos, más capacidad de storage, lo que haga falta.

La más típica es el escalamiento vertical, que consiste en comprar una máquina más grande. Si el procesador resulta lento, compramos uno más grande; si se nos está acabando el disco, tiramos el que tenemos y le ponemos uno más grande. Es poner una máquina más potente en lugar de la pequeña para hacer exactamente lo mismo.

La otra se llama escalamiento horizontal, y es donde los sistemas distribuidos tienen verdadero sentido: en lugar de una máquina más grande, ponemos más máquinas, que trabajan en paralelo.

Hay una advertencia que hacer de inmediato. Tomar un sistema que funciona con una máquina y agregarle más máquinas, si no lo pensamos bien, no va a funcionar: el sistema tiene que estar diseñado para poder escalarse horizontalmente. Vamos a ver enseguida un ejemplo donde eso es fácil y otro donde es difícil. Y conviene decirlo con todas las letras: cómo hacer un sistema que pueda escalar horizontalmente es, en esencia, el contenido de la materia.

Para eso, y para la otra razón, que es la tolerancia a fallas. Cuando tenemos una única máquina, si bien se pueden aislar un poco las fallas entre sí, generalmente cuando una máquina muere, muere entera. Los sistemas operativos tratan de aislar las fallas entre procesos, pero siempre hay cosas que pueden afectar a la máquina entera. Cuando las máquinas están separadas físicamente, en cambio, pueden fallar de manera independiente. Y si usamos algunas técnicas de redundancia podemos tolerar que mueran máquinas enteras y que el sistema, como un todo, siga funcionando. Los nodos pueden morir; el sistema sigue.

Lo que estamos buscando, en el fondo, es un sistema que no se apague porque se rompió un nodo y que siga funcionando siempre. Resulta llamativo, y sin embargo es algo que se puede lograr con relativa facilidad.

Estas dos son las que más nos van a interesar, y son la motivación principal para armar un sistema distribuido. Queremos poder escalar algo y queremos poder tolerar fallas en eso mismo, que nunca se pueda romper del todo, y que cuando la capacidad no alcance podamos agregarle más máquinas baratas, pero muchas, y siga funcionando.

Hay otras razones, menos importantes y casi una consecuencia de esas dos. Una es compartir recursos: si el recurso está físicamente en otro lugar, podemos usar un sistema distribuido para acceder a él.

### Economía de escala y commodity hardware

Otra de esas razones es la economía; en particular, la economía de escala. Estos sistemas, cuando escalan horizontalmente, tienden a salir más baratos que comprar una máquina más grande. La potencia que se consigue es muchísimo mayor, y sobre todo el costo por unidad de potencia es muchísimo mejor escalando horizontalmente que comprando máquinas cada vez más grandes.

De esto tomaron nota en Google, que fue quien difundió los clústeres de computadoras baratas: lo que se conoce como *commodity hardware*. Commodity quiere decir precisamente eso, máquinas comunes, de las que se consiguen en cualquier comercio. No eran servidores especiales de HP ni equipamiento fuera de lo común: eran máquinas que compraron, atornillaron entre sí, y con eso armaron una supercomputadora improvisada. Tampoco tuvieron que comprar un mainframe, de esos que tenían los bancos. El contraste está justamente ahí: commodity hardware contra mainframes.

Lo que querían resolver es lo que vamos a ver la clase que viene. Querían indexar la web entera: escanearla, recorrerla con un crawler, armar un índice invertido. Era un problema computacionalmente gigantesco. Por eso inventaron MapReduce, que corría en muchísimos nodos. ¿Y qué eran esos nodos? Máquinas modestas y baratas, que se rompían con frecuencia y cuya falla no generaba mayor preocupación: se descartaba la que se había roto y se atornillaba otra en su lugar. Si necesitaban más potencia, compraban más máquinas y las agregaban al clúster, y el sistema estaba diseñado para escalar sin inconvenientes.

Se suele señalar a Google como uno de los pioneros en usar commodity hardware para resolver problemas reales, y en efecto todo empezó como un proyecto de investigación en Stanford. Lo que Google no inventó es el término *cluster computing*: juntar máquinas para que trabajen como una sola es una idea bastante anterior a la empresa. Lo que sí hizo fue llevarla a una escala que nadie había intentado, y con las máquinas más baratas que había a mano.

*[Nota: El primer producto comercial de clustering fue el Attached Resource Computer de Datapoint, de 1977, y la práctica se difundió con el VAXcluster que Digital Equipment lanzó en 1984 para VMS. El antecedente más cercano al modelo de Google son los clústeres Beowulf, que Thomas Sterling y Donald Becker armaron en la NASA en 1994 con PCs de venta masiva. Google se fundó en 1998.]*

Hay un caso célebre de esa misma idea. En 2010, la Fuerza Aérea de los Estados Unidos compró unas mil setecientas PlayStation 3 para armar una supercomputadora, y ahí la economía de escala se ve con una nitidez que ningún argumento abstracto consigue: el equipamiento equivalente en máquinas de propósito específico costaba unos diez mil dólares por unidad, así que las mil setecientas habrían salido diecisiete millones de dólares. El clúster de consolas costó dos, y encima consumía la décima parte de la energía.

*[Nota: El Condor Cluster del Air Force Research Laboratory, inaugurado el 1 de diciembre de 2010 en Rome, Nueva York, con 1.760 consolas.]* Una PlayStation 3 es un equipo muy barato para el gobierno de los Estados Unidos. También se decía por entonces que las combinaban para intentar descifrar información, pero la idea es exactamente la misma. Combinar todo eso, eso sí, no es automático.

Algo parecido ocurre hoy con las GPUs, y conviene aclararlo: no es un tema que dominemos. Todos los entrenamientos de redes neuronales se están haciendo con clústeres de máquinas que tienen muchísimas GPUs. Y ahí aparece una sutileza que conecta con la distinción del principio: las GPUs que entrenan redes neuronales se parecen más al modelo de memoria compartida, porque hay distintas clases de memoria pero es una máquina donde la GPU tiene acceso directo a la memoria. Lo que hacen las empresas es combinar esas máquinas entre sí para poder entrenar entre muchas y escalar el entrenamiento. Y ahí terminan combinándose las dos cosas a la vez: la multiprogramación con el sistema distribuido.

De los data centers donde vive todo esto circulan fotos que uno encuentra buscando en internet, y no está claro que sean reales: nadie puede ir hasta ahí, y cuesta creer que dejen sacarle fotos a los data centers de Google. Pero la idea es la misma en todos. Tanto Amazon como Facebook —que incluso publicó con cierto detalle cómo funcionan los suyos— son variaciones de commodity hardware. Hoy ya son PCs algo más especializadas, pero terminan siendo procesadores comunes con memorias comunes, puestos de a muchos.

[FIGURA: dos fotos de clústeres — arriba, un rack temprano de Google con las placas al aire y los cables desordenados; abajo, el pasillo de un data center moderno con racks a ambos lados — pizarra pág. 6]

De hecho, el *cluster computing* en este sentido —tomar muchas máquinas comunes y hacer data centers gigantes con muchísimas veces la misma máquina— es lo que permitió el Cloud. La historia que se suele contar es que el problema de Amazon era que había armado uno de estos data centers para tener la capacidad que necesitaban en Navidad, y que después empezaron a alquilarle a la gente esa capacidad de cómputo que les quedaba ociosa el resto del año. Es una historia épica, una historia de origen elegante, y conviene desconfiar de ella: los propios ejecutivos de Amazon la desmintieron más de una vez. Lo que efectivamente ocurrió es menos cinematográfico y más interesante, porque el servicio se diseñó desde el principio para venderse afuera. Lo que sí sigue en pie es la parte económica del argumento: una vez que uno sabe armar data centers gigantes con muchísimas veces la misma máquina barata, alquilar esa capacidad se vuelve un negocio posible.

*[Nota: La versión documentada es que en 2003 Benjamin Black y Chris Pinkham escribieron dentro de Amazon un documento que proponía una infraestructura completamente estandarizada y automatizada, apoyada en servicios web, y sugería de paso que se podría vender el acceso a esos servidores virtuales; el trabajo arrancó en 2004 y S3 salió en 2006.]*

Estos data centers son además muy elásticos, en el sentido de que es fácil agregar máquinas nuevas. Hay que diseñarlo, claro, y hay que tener algunos cuartos disponibles.

Al final de la materia vamos a ver que en Google publicaron directamente un paper, o un libro, o una monografía que se llama *The Datacenter as a Computer*, donde consideran que el data center entero funciona como una especie de computadora gigante. De ahí surgió el orquestador para ejecutar cosas dentro de ese data center, que Google llamó Borg y que años después, liberado como código abierto, se convirtió en Kubernetes.

*[Nota: *The Datacenter as a Computer: An Introduction to the Design of Warehouse-Scale Machines*, de Luiz André Barroso y Urs Hölzle (2009). Borg es de alrededor de 2003-2004; Kubernetes se liberó en 2014.]*

Todo ese argumento merece una aclaración de escala. La economía de escala no nos resulta demasiado relevante en lo individual, porque no vamos a comprar literalmente dos mil PCs y armar un data center. Pero a estas empresas, que sí disponen de mucho capital, les resulta muy conveniente, y por eso desarrollaron tanto el tema.

### Modularidad forzada: aislar fallas y aislar equipos

Hay otro concepto importante que también menciona el libro del MIT y que en la carrera uno nunca escucha: la modularidad forzada. Modularizar es algo que ya sabemos hacer desde que empezamos la carrera. Las funciones son una forma de crear módulos —una unidad de código que se reutiliza y que abstrae algo—; las clases también son módulos; y los lenguajes modernos suelen tener además módulos propiamente dichos. Pero entre todo eso y lo que viene ahora hay una diferencia, y es justamente la que le da nombre al concepto: modularizar en esos casos depende de la voluntad, del conocimiento y de la habilidad que uno tenga para diseñar bien, de manera que un módulo no se meta donde no debe y rompa la abstracción. ¿Y por qué queríamos modularizar en primer lugar? Fundamentalmente, para obtener simplicidad en los diseños. Los módulos los necesitamos nosotros: probablemente un modelo de lenguaje no necesite módulos, porque procesa la información de otra manera, pero nosotros, con nuestras limitaciones cognitivas, tenemos que pensar en abstracciones, en módulos que hacen una sola cosa. El problema es que a veces esos módulos tienen fugas, y a veces uno se puede meter y romper esas abstracciones que con tanto cuidado se habían dibujado.

Ahora bien, si en lugar de todo eso usamos sistemas que están físicamente separados, la historia cambia. Si decimos que este es el módulo de la base de datos y que está en esta máquina, y que este otro es el módulo del servidor web y está en aquella otra, ya no hay forma de acceder por otra cosa que no sea la interfaz que se pensó para esos dos módulos. No es que meterse por otro lado esté mal visto: es que no se puede. Eso es lo que podemos definir como modularidad forzada, la que logramos rompiendo a la fuerza, físicamente. A veces esas dos máquinas son en realidad máquinas virtuales, pero conviene seguir con el ejemplo de que están físicamente separadas: dos módulos conectados por un cable, y por ese cable tiene que ir una interfaz bien definida. Al forzar esa modularidad, lo que uno logra es compartimentalizar las fallas —el término es incómodo, pero es el que se usa—: que una falla que aparece en un módulo no se propague hasta el otro. Si la base de datos falla gravemente y deja de responder, quizá el servidor web tenga alguna forma alternativa de seguir adelante: quizá guardó algo en una caché, quizá puede funcionar más o menos hasta que la base se restablece. Si en cambio la base de datos estaba junto con el web server en la misma máquina y esa máquina se quema, entonces una falla que se originó en el hardware se propagó al resto del sistema. Y de esa compartimentalización de fallas es de donde emerge la propiedad de la tolerancia a fallas. Digámoslo con todas las letras: las cosas son tolerantes a fallas en un sistema distribuido porque fallan parcialmente. Fallas parciales.

El ejemplo que mejor ilustra esto viene de los barcos. En ingeniería naval se hace algo parecido para evitar que venga algo, le rompa el casco al barco, el barco se llene de agua y se hunda: se divide en muchos compartimentos la parte de abajo, de manera que si se rompe uno se inunde uno solo, y uno solo no es suficiente para hundir el barco. La idea que perseguimos nosotros es exactamente la misma: que si falla una parte del sistema falle un nodo solo, y que después el resto se pueda restaurar. Vamos a ver que en general los sistemas suelen tener formas de sacar ese nodo y levantar uno nuevo en su lugar, y que eso suele ser automático. La paradoja está en que el barco de la foto es justamente el Titanic, con lo cual la estrategia no le funcionó. El problema fue que el iceberg impactó de costado y rompió varios compartimentos consecutivos: el barco estaba diseñado para flotar con los primeros cuatro inundados, el iceberg le abrió cinco, y ese uno de más alcanzó para hundirlo entero. Y alcanzó por una razón que vale la pena entender, porque es la misma que vamos a ver enseguida en un sistema real: los mamparos que separaban los compartimentos no llegaban hasta arriba, así que con cinco compartimentos llenos la proa se hundía lo suficiente como para que el agua desbordara por encima del mamparo hacia el sexto, y de ahí al séptimo. La falla no se quedó quieta donde empezó: se fue propagando. Se sostiene, inclusive, que el error fue haber intentado esquivarlo: con un impacto frontal, el Titanic podría haberse salvado. Eso es exactamente lo que queremos evitar cuando diseñamos bien un sistema.

*[Nota: El Titanic tenía quince mamparos estancos y podía mantenerse a flote con cualquiera de sus dos primeros compartimentos inundados, o con los primeros cuatro; la colisión abrió costuras y planchas a lo largo de unos noventa metros y dejó abiertos al mar los primeros cinco.]*

[FIGURA: las condiciones de inundación admisibles del Titanic — el casco intacto y las distintas combinaciones de dos, tres y cuatro compartimentos inundados — notas pág. 3 / pizarra pág. 7]

La versión de todo esto en la vida real ocurrió el 28 de febrero de 2017. S3 es un sistema que se puede pensar como un file system distribuido, pero gigantesco: prácticamente todos los demás sistemas de Amazon dependen de él, y muchísimas otras aplicaciones de internet también. Probablemente sea el storage de archivos más grande que hay en el mundo; se los llama objetos, pero terminan siendo archivos. Naturalmente estaba diseñado con mucha redundancia, con nodos distribuidos por todos lados, de manera que si se rompía uno se restauraba automáticamente. Lo que pasó fue que alguien ejecutó un comando pensado para remover una pequeña cantidad de servidores que querían reemplazar; parece que puso mal el número, y ese comando terminó sacando una gran cantidad de servidores del clúster. Y aquí está el parecido con el Titanic: los que quedaban se saturaron y dejaron de responder pedidos, porque no soportaban el resto del tráfico. S3 tenía muchos sistemas que dependían de ese subsistema y que estaban tratando de responder; entonces esos otros sistemas empezaron a fallar, y como no podían responder, la gente les seguía pidiendo cosas y se siguieron saturando cada vez peor. Lo que tuvieron que hacer fue reiniciar todo el sistema, literalmente miles de nodos. Y tuvieron un problema adicional: nunca habían reiniciado S3, así que no estaban muy seguros de cómo levantarlo desde cero. El problema fue tan grande que llegó a los diarios: es el día en que se rompió internet. Quien busque esa fecha va a ver que se cayó cerca de la mitad de internet, una proporción enorme. Se originó por un problema humano, y porque se cayeron muchos más de esos compartimentos de los que se suponía que podían caerse. Lo interesante es que Amazon, cuando comete un error de esta magnitud, publica una explicación para los clientes contando qué fue lo que hicieron, y qué iban a hacer para evitar que el problema se repitiera.

[FIGURA: el comunicado de AWS sobre la interrupción del servicio de S3 en la región de Virginia del Norte, con el párrafo del comando mal tipeado resaltado — pizarra pág. 9]

Queda una última ventaja: separar responsabilidades administrativas. Es un argumento que se usa mucho a favor de los microservicios, aunque los microservicios no terminan de convencernos —resulta preferible el concepto de servicios, no tan micro— y esa discusión queda pendiente para más adelante. Lo importante es lo siguiente: si una empresa es grande y tiene muchos equipos, y el sistema es un único monolito acoplado con todo, administrar eso resulta muy complejo desde el punto de vista organizativo. Termina siendo mucho más fácil si las cosas se diseñan como un sistema distribuido donde las interfaces están modularizadas forzosamente: los distintos subsistemas están a la fuerza separados, se comunican mediante interfaces claras que los dueños de cada uno se comprometen a respetar, cada uno puede desplegar de manera independiente, y si algo se rompe se sabe a qué equipo hay que ir. Esa distribución, nótese, ya no es tanto de nodos sino de subsistemas dentro del gran sistema, donde el gran sistema bien podría ser la empresa entera. No vamos a hablar muchísimo de esto: lo que más nos interesa son las dos primeras razones. Pero es también una de las razones por las cuales inevitablemente se terminan usando sistemas distribuidos. Hoy, prácticamente, cuando uno habla de un sistema o de una aplicación, está hablando de un sistema distribuido: la única diferencia está en dónde queda la máquina física, que siempre está en la nube.

### La transparencia y sus límites: NFS y Waldo

Hay una propiedad más para sumar a la lista, y tiene un carácter distinto de las anteriores: es deseable, sí, pero deseable más o menos. Se trata de la transparencia en la distribución, un punto polémico de entrada, y lo que sigue es una posición tomada, apoyada en algunos papers. Muchas veces los sistemas distribuidos arrancan con la definición de que un sistema distribuido es uno formado por muchos componentes, pero donde ese hecho está escondido: el sistema se ve como uno solo, y los componentes internos no se ven desde afuera. Es casi la definición de sistema con la que empezamos esta lección, aplicada a los sistemas en general y no a los distribuidos en particular.

[FIGURA: una persona que mira el sistema distribuido desde afuera y lo ve como un todo, con sus nodos internos apenas insinuados adentro — notas pág. 3 / pizarra pág. 8]

De ahí surge algo importante: si exageramos mucho con esa transparencia e ignoramos los problemas que tiene la red, todo se nos complica. Y hay un caso histórico que lo muestra.

Esto es lo que querían lograr en los ochenta. Google, Amazon y compañía empezaron a dedicarse a esto principalmente a partir del año 2000, y ahí empezaron a hacer las cosas con diseños menos transparentes, donde se notaba que cuando uno llamaba a una API estaba llamando a la de un sistema distribuido. En los ochenta la ambición era la contraria: hacer un sistema distribuido, pero que no se supiera que estaba distribuido, que la gente pensara que era uno solo y local.

NFS, el Network File System, fue uno de esos intentos. Era para compartir archivos: uno tenía un servidor donde estaban los archivos, el famoso servidor de películas que tenían antes las empresas, por ejemplo.

Pero la parte esencial del diseño, al menos en las primeras versiones, era que el Network File System se montaba como si fuera un file system más dentro del virtual file system, en este caso de Linux, aunque cabe dudar de que Linux existiera en esa época. Es decir, uno montaba el NFS igual que montaba ext4, o NTFS, o FAT.

[FIGURA: la arquitectura de NFS — los procesos del cliente sobre el virtual file system, que deriva hacia el file system local o hacia el cliente NFS, y de ahí por la red hacia el servidor NFS y su propio disco — pizarra pág. 10]

Y lo que terminaba pasando era que cuando todo funcionaba bien, funcionaba bien. Pero aquí está el punto: ese link que une al cliente con el servidor es justamente un enlace de los que veníamos hablando, una de las tres abstracciones. Es una red. Y a veces la red se rompía, se desconectaba, o lo que fuera. La transparencia exagerada de este diseño hacía el resto: una aplicación normal, diseñada para el file system local, si le ponían debajo uno que de vez en cuando fallaba, perdía mensajes o se demoraba sin aviso, funcionaba mal.

Había dos formas en que esto podía tolerar los fallos. Una era fallar directamente y empezar a tirarle errores al proceso. Y conviene ver por qué eso es grave: normalmente, cuando uno escribe en un file system y recibe un error de escritura, es que algo salió muy mal —se quemó el disco, se rompió—, o en el mejor de los casos se acabó el espacio. Uno tiene que manejar el código de error de `write` porque es lo correcto; en la práctica, si `write` devuelve un código inesperado, el problema es serio. Con el Network File System esos códigos pasaban a ser casi la norma, porque lo que había abajo era una red que a veces respondía lento y a veces daba timeout. La otra forma de evitar esos errores era peor todavía: que el NFS se bloqueara hasta poder mandar el mensaje. Ahí la idea estaba bien, salvo por un detalle: si el servidor se apagaba y nunca volvía, el programa se quedaba trabado para siempre.

¿Cuál era el problema de todo esto? No un detalle de implementación, sino que exageraron con la transparencia. Tomaron una interfaz, el virtual file system, que asumía ciertas cosas sobre lo que tenía abajo —ciertas cosas de latencia, que enseguida vamos a enumerar— y le pusieron un sistema distribuido debajo. Por eso no tuvo mucho éxito. Vamos a ver que las formas modernas de hacer sistemas distribuidos de alguna manera saben que se están comunicando con algo remoto, y manejan explícitamente los errores que pueden aparecer.

Hay un paper, escrito por Jim Waldo y sus colegas en los laboratorios de Sun, que dice básicamente por qué no se puede exagerar con la transparencia al nivel del NFS —de hecho, el ejemplo del NFS sale de ese paper—. El fondo del argumento es que hay limitaciones físicas que la red impone, y que no se dejan esconder del todo detrás de una interfaz. Estos enlaces tienen cuatro características indeseables que no podemos ignorar, y son exactamente las cuatro que el paper enumera.

*[Nota: *A Note on Distributed Computing*, de Jim Waldo, Geoff Wyant, Ann Wollrath y Sam Kendall, Sun Microsystems Laboratories, informe técnico SMLI TR-94-29, noviembre de 1994. Las cuatro que enumera son latencia, acceso a memoria, concurrencia y fallas parciales.]*

La primera es la latencia. En general las redes son más lentas que escribir directamente en el disco, pero lo que más importa no es tanto que sean lentas sino que tienen mucha varianza. Los links dentro de un data center son muy rápidos, solo que no son tan constantes como escribir en un disco. Depende de si un router se rompió, de si pasó algo raro, o de si el host al que nos queremos conectar está cerca o lejos —y en general ni siquiera sabemos dónde está físicamente— y tiene que dar muchos saltos. Y por eso, para un diseñador, es mucho más difícil asumir garantías sobre cuál es un timeout apropiado. Si ponemos un timeout de 10 milisegundos estamos muy justos: muchas veces la red va a tardar más por una cuestión perfectamente normal, y vamos a recibir un error que no corresponde a ninguna falla. Cuán justos estamos se ve poniendo números. La luz viaja por una fibra óptica a unos doscientos mil kilómetros por segundo, y de Buenos Aires a Virginia hay unos ocho mil kilómetros; el ida y vuelta, entonces, no puede bajar de ochenta milisegundos, y eso suponiendo que el cable va derecho y que ningún equipo intermedio se toma un instante para pensar. Con un timeout de diez milisegundos, ninguna llamada a otro continente llegaría jamás a tiempo: estaríamos declarando caído un servidor que funciona perfectamente, por pedirle algo que la física no permite. Si en cambio lo ponemos demasiado largo, el precio es el opuesto: cuando algo efectivamente falle, muchas aplicaciones se van a volver lentas.

La segunda es el memory access, y es igual de clave. Cualquier intento de ignorar el problema y suponer que podemos compartir memoria entre dos sistemas que no están físicamente en la misma máquina nos va a llevar por mal camino. Si no es la misma memoria, cuando la tratemos de compartir va a resultar lento y van a aparecer errores de concurrencia.

La tercera son las fallas parciales, y pesan especialmente en los sistemas grandes: las cosas fallan constantemente, la red falla, fallan los routers, fallan los discos. En una máquina física que está toda junta la probabilidad de que las cosas fallen es relativamente baja; una computadora puede pasar años sin fallar, justamente porque es una sola pieza. Pero si tuviéramos mil computadoras, por una cuestión de probabilidad alguna estaría fallando constantemente. Y conviene hacer la cuenta, porque el resultado no es intuitivo: si cada máquina aguanta tres años sin romperse —que es una vida razonable y hasta modesta—, mil máquinas juntan trescientas treinta y tres roturas por año, es decir casi una por día. La misma pieza de hardware que individualmente parece indestructible se convierte, multiplicada por mil, en una falla diaria.

La cuarta es la concurrencia. Necesariamente todas las cosas van a ejecutarse concurrentemente: cada uno de estos nodos tiene un procesador propio y está siempre haciendo cosas. Y la concurrencia, combinada con el memory access, nos saca algo que antes nos venía muy bien: los locks basados en memoria compartida. Los mutexes, los semáforos, todas esas herramientas, si uno se mete a ver cómo están hechas, se basan en poder compartir memoria: terminan apoyándose en alguna operación atómica del procesador, del tipo de la que suele llamarse CAS, por compare-and-swap —comprobar un valor de memoria y fijarlo—, diseñada para que si hay varios procesadores solamente uno pueda ejecutarla atómicamente. Como ahora los procesadores están separados, vamos a tener que recurrir a otros mecanismos para implementar la funcionalidad que tenían los locks. Una transacción en una base de datos ya no va a ser tan fácil, y por eso vamos a dedicarle una clase entera a ver cómo funcionan las transacciones.

---

## 3. La organización cliente-servidor

Cambiamos ahora de tema y pasamos a algo mucho más concreto: el elefante en la habitación, que es la organización cliente-servidor. Muchas veces la vamos a llamar cliente-servicio, que es como la nombra el libro del MIT, para diferenciarla un poco de la noción de cliente y servidor a nivel de sockets. Lo primero es dejar de pensar en TCP/IP: esto es distinto.

El énfasis, en esta organización, está puesto en otra parte: en que hay una asimetría entre estos dos nodos. El cliente sigue siendo el que inicia la comunicación, es cierto, pero la definición que nos interesa es más semántica, casi filosófica: no es el cliente porque inicie la conexión TCP, sino porque es el que *necesita algo* que le puede proveer el servicio del otro lado. Y el servidor le responde —o, para ser precisos, no necesariamente le responde, pero le hace algo.

Esos dos mensajes tienen nombre propio, y son términos que van a reaparecer a lo largo de la materia: el mensaje que el cliente le manda al servidor se llama **request**; el mensaje con el que el servidor le contesta se llama **response**. Las definiciones no son tan estrictas: no necesariamente tiene que haber siempre un response con contenido, y a veces es apenas un "okay, lo recibí".

La diferencia con el cliente y el servidor de TCP es sutil, y por eso mismo confunde. El cliente de TCP es el mismo cliente del que estamos hablando ahora, y el servidor de TCP es el mismo servidor: no estamos apuntando a otras máquinas ni a otros roles. Lo que se agrega es la asimetría.

La asimetría se ve mejor por contraste con los sistemas peer to peer, donde todos son compañeros entre sí, todos comparten información y a lo sumo alguno obtiene temporalmente un rol. El ejemplo es Raft, un protocolo esencialmente peer to peer: todos los nodos pueden actuar de cualquier cosa, y ninguno tiene información más privilegiada. En cliente-servidor la situación es distinta: el servidor tiene algo y el cliente tiene otra cosa.

[FIGURA: a la izquierda, cliente y servicio unidos por un request de ida y un response de vuelta; a la derecha, tres nodos en triángulo con flechas en todos los sentidos, rotulados peer to peer y Raft — notas pág. 4 / pizarra pág. 11]

Un ejemplo pequeño alcanza para ver la mecánica completa, y de paso introduce una convención de dibujo que vamos a usar varias veces: el diagrama de tiempo. El tiempo va de arriba hacia abajo, hay una línea para la máquina cliente y otra para el servidor, y los mensajes se representan con flechas.

El servicio del ejemplo es un servidor de tiempo: lo único que hace es decir la hora que es. Cabe preguntarse por qué un cliente le preguntaría eso a otra máquina en lugar de mirar su propio reloj, y la respuesta es que no confía en su reloj y quiere un reloj global. Y ahí hay una advertencia que anticipa buena parte de la materia: tener un reloj global es una cuestión polémica, porque no se puede hacer.

El cliente quiere calcular cuánto tarda la ejecución de una función. La secuencia es esta: manda un `get time` y el servidor le responde con el tiempo; ejecuta la función; vuelve a mandar un `get time` y el servidor le responde de nuevo; y hace la resta. Eso le da la duración de la función, más un pequeño excedente que para el ejemplo no importa.

[FIGURA: diagrama de tiempo del servidor de tiempo — el tiempo corre hacia abajo, una línea para el cliente y otra para el servicio, el primer get time con su respuesta, la ejecución de la función en el medio, y el segundo get time con la suya — notas pág. 4 / pizarra pág. 13]

Implementarlo en abstracto no lleva mucho: alcanza con un pseudocódigo que después podría escribirse en cualquier lenguaje.

```text
Client program

 1  procedure MEASURE (func)
 2      SEND_MESSAGE (NameForTimeService, {"Get time", CONVERT2EXTERNAL(SECONDS)})
 3      response ← RECEIVE_MESSAGE (NameForClient)
 4      start ← CONVERT2INTERNAL (response)
 5      func ()                          // invoke the function
 6      SEND_MESSAGE (NameForTimeService, {"Get time", CONVERT2EXTERNAL(SECONDS)})
 7      response ← RECEIVE_MESSAGE (NameForClient)
 8      end ← CONVERT2INTERNAL (response)
 9      return end - start

Service program

10  procedure TIME_SERVICE ()
11      do forever
12          request ← RECEIVE_MESSAGE (NameForTimeService)
13          opcode ← GET_OPCODE (request)
14          unit ← CONVERT2INTERNAL (GET_ARGUMENT (request))
15          if opcode = "Get time" and (unit = SECONDS or unit = MINUTES) then
16              time ← CONVERT_TO_UNITS (CLOCK, unit)
17              response ← {"OK", CONVERT2EXTERNAL (time)}
18          else
19              response ← {"Bad request"}
20          SEND_MESSAGE (NameForClient, response)
```

Del lado del cliente, la línea 2 es la función del socket: `SEND_MESSAGE` es el `send`, y recibe dos cosas. La primera es el nombre del canal, que en la práctica sería un file descriptor. La segunda es el mensaje, y ahí está lo que importa: lleva adentro el nombre de la función que queremos ejecutar del otro lado, `"Get time"`. Lo acompaña un parámetro, la unidad en la que pedimos el tiempo, y el servicio la valida: la línea 15 exige que la operación sea la que espera y que la unidad sea segundos o minutos, y si algo de eso falla contesta `"Bad request"`. El ejemplo usa además dos nombres de canal distintos, uno para cada sentido, un detalle que vamos a revisar más adelante.

Después de mandar hay que quedarse a la espera de la respuesta, y eso es la línea 3: `RECEIVE_MESSAGE`, que sería un `read` del socket. Y cuando llega todavía falta la línea 4: hacer una conversión. Esos bytes hay que transformarlos en un tiempo, en algo con lo que el programa pueda operar, que aquí significa poder restarlo. Vale la pena enfatizar las tres, porque se repiten siempre: hubo que mandar un mensaje, hubo que quedarse esperando la respuesta, y hubo que convertir lo que llegó. Y una cuarta, la que más va a pesar: toda esa secuencia hay que repetirla, entera, para la segunda medición. Las líneas 6, 7 y 8 son idénticas a las 2, 3 y 4, y lo único que cambia es dónde se guarda el resultado.

Esa función de conversión que aparece cuatro veces en un programa tan corto tiene nombre propio: en la jerga se lo suele llamar marshalling, y también serializar. Consiste en tomar un objeto de más alto nivel —un struct, un objeto, prácticamente cualquier estructura del lenguaje— y transformarlo en un stream de bytes. La razón es la que ya conocemos: por los sockets uno manda bytes, como si fuera un archivo. Del otro lado se recorre el camino inverso y se reconstruye algo que el programa pueda usar, que es lo que hacen las llamadas a `CONVERT2INTERNAL`.

---

## 4. El web server real: HTTP, load balancers y escalado

### HTTP y la demo con las DevTools

El servidor de tiempo muestra la mecánica completa, pero es un ejemplo abstracto y un poco raro. Conviene entonces mirar uno real, y ese ejemplo es HTTP.

Aquí el cliente es el browser que cada uno tiene delante: Chrome, Safari, Firefox. Y el servidor puede ser Apache, o Nginx, o alguno de los otros servidores disponibles. Lo interesante es que los dos mensajes se llaman exactamente como los veníamos llamando: el request se llama request y el response se llama response. Aquí no hubo que inventarles nombres distintos, porque el protocolo ya los usa.

[FIGURA: el cliente —Chrome, Safari— y el servidor —Apache, Nginx— unidos por un request de ida y un response de vuelta — notas pág. 5 / pizarra pág. 14]

Ese request y ese response no hay que imaginárselos: quien haya trabajado en aplicaciones seguramente ya los vio, y quien no, puede reproducirlo sobre cualquier página, incluida la de la materia. Abriendo las herramientas de desarrollador del browser —las DevTools— hay una pestaña llamada Network, y ahí aparece en vivo todo lo que está haciendo la red: todos los requests y todos los responses. Esos paquetes se pueden filtrar por documentos, y eligiendo uno cualquiera —el calendario de la materia, por ejemplo— la herramienta muestra cómo fue el request y cómo fue el response.

Lo que aparece al abrir uno son, principalmente, unos headers que se mandan con el request y unos headers que se reciben con el response, y después el contenido de lo que el servidor nos mandó. La herramienta lo presenta de una manera de alto nivel y ordenada; pero lo que está pasando por debajo es una comunicación cliente-servidor de las que veníamos describiendo.

El protocolo HTTP es una mezcla de texto con binario. Los headers son lo primero que se manda, y después va el texto; todo eso se le manda al servidor y el servidor responde. Por lo menos HTTP/1 funcionaba así —hoy hay una versión más moderna—: uno manda un request y le responden, manda otro y le responden de nuevo. Y ese es el ejemplo más típico de cliente y servidor.

Todo eso que la herramienta muestra desplegado —los headers, y los parámetros de un formulario si el cliente le hubiera mandado alguno— es el mensaje de request, y ahí cierra algo que dijimos al principio. No son piezas sueltas que viajan por separado: se manda todo junto por el socket. Y lo que el otro nos responde, con el contenido entero de la página y sus headers arriba, es el mensaje de response. No hay una forma cómoda de verlo así, tan de bajo nivel, porque la herramienta está justamente para no mostrarlo de esa manera; pero es exactamente eso: un mensaje que va y un mensaje que vuelve.

Mirar esto una vez es útil en la vida en general, porque HTTP es de los protocolos que más se usan para implementar aplicaciones. Más adelante vamos a hablar de REST, que es cómo usar HTTP para hacer otro tipo de comunicaciones. Pero por ahora HTTP nos interesa solamente como ejemplo básico de un cliente y un servidor.

### La arquitectura real y su escalado

Lo que veníamos describiendo es la versión simplificada. La página de la facultad, evidentemente, no está alojada en una computadora hogareña, de esas que funcionan con el gabinete abierto para que no se recalienten. Está en un servidor real, un servidor de GitHub, y ese servidor no es un servidor único: es, él mismo, un sistema distribuido. Miremos entonces cómo funcionan estas cosas en la vida real, aunque lo que sigue sea una anticipación de lo que vendrá más adelante.

Lo que típicamente tiene una arquitectura de estas es, en vez de un único servidor HTTP, un escalamiento horizontal: muchos de esos servidores, cada uno con una copia de la página. Del otro lado está el cliente, que es quien se quiere conectar, y entre medio está internet, con sus redes, su TCP y todo lo demás. Aparece naturalmente la pregunta de cómo se hace para llegar a una de esas máquinas en particular, ahora que son varias.

La respuesta habitual es que hay una máquina especial, que corre un sistema diferente del de las otras, y que es la que recibe la conexión. Vale la pena ser preciso: el socket, en realidad, es entre esa máquina especial y el cliente. La conexión TCP se establece entre esas dos puntas, y no entre el cliente y el servidor que finalmente lo va a atender. Esa máquina, una vez que tiene la conexión, elige una de las máquinas de atrás —por ejemplo, al azar— y le manda el pedido. Ese es el ejemplo típico de lo que se llama un **load balancer**, un balanceador de carga.

[FIGURA: el cliente que entra por internet, el load balancer que recibe la conexión, los servidores HTTP detrás de él, y la base de datos a la que todos consultan — notas pág. 5 / pizarra pág. 14]

El nombre suele venir cargado de más. Si bien los balanceadores de carga suelen ser máquinas que vende Cisco y por las que se paga muy caro, desde nuestro punto de vista no dejan de ser simplemente un nodo especial dentro del sistema distribuido, cuya única función es redirigir tráfico de un lugar para otro.

Ese nodo, generalmente, soporta muchísimas conexiones, y la razón es que no tiene que hacer mucho más que retransmitir pedidos. Los otros, en cambio, tienen que tener un file system, leer las cosas del file system, cargar la página, implementar el protocolo HTTP y mandárselo al cliente. Como el balanceador hace muchísimo menos, y por lo tanto lo hace mucho más rápido, suele soportar muchas más conexiones que cualquiera de las máquinas que tiene detrás. Y esto que acabamos de dibujar es un ejemplo de escalamiento horizontal.

Si la página de la facultad tuviera un formulario que hay que llenar y guardar, lo que se suele hacer es poner la base de datos aparte. Todos esos servidores web tienen la información estática de la página, y cada uno, cuando necesita acceder a la información, se conecta a la base de datos y le manda una query en SQL; la base la procesa y le responde. Esa base de datos es, en sí misma, otro nodo dentro del sistema.

Si queremos hilar más fino, se ve enseguida que algo quedó a medio hacer. Escalamos horizontalmente la parte de los servidores web, sí, pero tenemos una única base de datos: si eso se rompe, se rompe todo. Y en este ejemplo un balanceador delante de la base no tendría sentido, porque hay una sola; todo el mundo tiene cargada su dirección y se conecta directamente. Así que hace falta alguna forma de escalar también la base de datos.

Una de esas formas es una estructura que se llama master-slave. A la base de datos original se le ponen réplicas: a la original se la suele llamar master, y a las otras, slaves o readers. La regla es fácil de enunciar: siempre que uno quiere escribir tiene que escribir en el master, y siempre que uno quiere leer puede leer del master o de cualquiera de las otras. Y para leer de las otras se puede poner un segundo load balancer, que recibe las consultas del clúster de servidores web y las reparte entre las réplicas disponibles.

[FIGURA: el master con las flechas de replicación hacia sus tres readers, y un segundo load balancer que reparte las lecturas entre ellos — notas pág. 5 / pizarra pág. 14]

Esa no es la única forma de balancear la carga cuando uno tiene varios nodos replicados. Otra es que haya alguna máquina que le inyecte a cada cliente la lista completa de las réplicas que existen, de manera que cada uno elija a cuál quiere ir sin pasar por ningún balanceador. Son ejemplos, nada más: hay muchas formas de hacer todo esto.

Aparece aquí una pregunta natural, que apunta a cómo están armadas casi todas las aplicaciones de hoy. Si en lugar de una página con un solo servicio tuviéramos varios microservicios —uno de formularios, otro para los trabajos prácticos—, ¿alcanza con un único load balancer que reparta el tráfico entre todos, o cada microservicio necesita el suyo? Antes de contestar, una aclaración sobre el nombre: la base de datos del dibujo no es *micro* en ningún sentido, porque una base de datos es una pieza grande, y el prefijo no nos dice demasiado. Lo importante es que sean servicios separados, que podamos ir escalando de manera independiente uno del otro.

Con eso dicho, la estrategia es parecida a la que venimos describiendo. Cada servicio expone típicamente una forma de acceder a él, y esa forma suele ser un load balancer; y del load balancer para adentro es una caja negra, que internamente puede tener muchos componentes conectados de las maneras más distintas. Es un árbol que va creciendo. Pero hay una precisión que importa más que la respuesta misma: cuando decimos que un servicio "tiene que tener un load balancer", el load balancer es apenas un ejemplo de cómo implementar la interfaz. Lo que vimos al principio de todo es que un sistema tiene que tener una interfaz por la cual se accede, y que uno no accede directamente a los nodos sino a través de ella; esa interfaz podrían ser APIs. Y el load balancer no es la única forma de acceder.

De hecho, ni siquiera hay que suponer que el balanceo vive en una máquina dedicada. A veces el balanceador está en el cliente mismo: cada cliente lleva incorporada una especie de balanceador local que conoce a todo el mundo y les distribuye el tráfico directamente. A veces son clientes muy básicos, que lo único que hacen es mandar un request y dejar que otro lo distribuya; a veces son clientes con bibliotecas grandes, que toman decisiones sobre cómo rutear el tráfico. Ese balanceador puede ser una biblioteca que uno compila junto con el programa, o —si se trabaja con containers— un sidecar. Hay muchas formas, y se están usando todas; por eso no hay una única respuesta, y si la hubiera no tendríamos materia.

Sobre las máquinas que están detrás del balanceador hay una pregunta razonable: esas instancias, ¿son todas la misma? Exactamente eso son, y tienen que serlo, porque el load balancer no toma decisiones complejas: elige una al azar, le manda el pedido, y esa responde. Una página estática como la de la materia funciona perfectamente con ese esquema.

Y con eso llegamos al punto que hay que retener: la esencia está en si el balanceo de carga se hace sobre algo que tiene estado o sobre algo que no lo tiene. Si los nodos del medio no tienen estado —**stateless** se le suele decir a ese tipo de nodos—, es muy sencillo ponerles un load balancer adelante y elegir cualquiera al azar. Las bases de datos son muchísimo más complicadas, porque una base de datos es la antítesis de un nodo stateless: existe justamente porque tiene un estado. Ahí no podemos simplemente poner más bases al lado de la primera, porque si guardamos un dato en una y después lo leemos de otra, obviamente ese dato no va a existir ahí. Por eso hay que hacer algo intermedio, como escribir siempre en la misma —el master— y que esa después se lo vaya mandando a las demás. Si no tiene estado es muy sencillo; si tiene estado es, prácticamente, el 50 % de la materia, porque los sistemas de storage son interesantes precisamente por eso: por cómo escalamos sistemas que tienen mucho estado adentro. De cómo hacer un web server prácticamente no vamos a hablar, porque eso ya se aprendió.

Master y slave son los nombres tradicionales, pero más adelante los vamos a ver con una denominación un poco más elegante: **primary** y **backup**. El primary es el que les manda las actualizaciones a los backups; en el primary uno escribe o lee, y de los backups solamente lee. Y los backups, esos sí, se pueden expandir horizontalmente.

### Qué base de datos: Mongo, Aurora y NoSQL

Desde otras materias llega una curiosidad. En arquitectura se plantea a veces que un sistema muy grande hay que resolverlo con MongoDB. Y uno se imagina entonces el esquema completo: cada instancia de la aplicación escalando horizontalmente, y cada una apuntando a un clúster distinto de MongoDB. ¿Es así como se resuelve?

Planteado así, el caso ya es muy específico, porque MongoDB es la implementación de una base de datos en particular. Lo que importa es reconstruir la decisión que hay detrás. La situación es esta: tenemos una base de datos relacional en una única máquina que no nos está alcanzando, y hay que pensar alguna forma de tener un sistema que escale horizontalmente. A partir de ahí se abren dos caminos.

Uno es seguir siendo relacionales, y ahí aparece Aurora, que es uno de los papers que vamos a ver más adelante justamente por eso: es algo intermedio entre una base relacional y una distribuida. El otro camino es pasarse a un sistema de storage completamente diferente, de los que se suelen llamar **NoSQL**. El nombre es una antidefinición: se define a partir de lo que no es. Son sistemas de storage distintos, con menos garantías, pero mucho más fáciles de distribuir.

Ahí está el criterio de fondo: si le sacamos algunas restricciones al problema, se nos amplía el mundo de lo que podemos usar. Si nos olvidamos de las transacciones que nos dan las bases relacionales y de la flexibilidad que tiene SQL, y podemos convivir con eso, se abren otras opciones más fáciles de escalar. Porque una base relacional es clásicamente difícil de escalar: no hay muchas más formas que esas réplicas que ya vimos, o alguna variante. Inclusive Aurora, cuando lo veamos, va a mostrar que una de las formas de escalarlo es justamente con réplicas.

*[Nota: *Amazon Aurora: Design Considerations for High Throughput Cloud-Native Relational Databases*, de Verbitski et al., SIGMOD 2017. En el cuatrimestre grabado Aurora queda como anticipo: vuelve a mencionarse en la clase 4, a propósito de lo que hace con el log de la base de datos, pero no llega a tratarse como paper propio.]*

Conviene no extenderse demasiado —además hay quienes todavía no cursaron bases de datos—, pero el razonamiento viene por ahí. Hay que pensar en términos de sistemas y de qué propiedades tiene cada uno. En este ejemplo, MongoDB tiene más facilidad para escalar horizontalmente que una base relacional. Por qué MongoDB y no DynamoDB ya es una discusión más complicada, porque las propiedades de esos dos sistemas empiezan a parecerse, sobre todo comparadas con las de Postgres, que sería el caso relacional.

---

## 5. RPC y las semánticas de entrega

### De la terna repetida al stub

El pseudocódigo del servidor de tiempo dejó un cabo suelto. En el programa del cliente el mensaje se manda a un canal y la respuesta se recibe de otro: `NameForTimeService` para la ida y `NameForClient` para la vuelta. A primera vista tendría que ser el mismo nombre, y la asimetría desconcierta. La explicación es que el ejemplo asume que el canal no es bidireccional, y por eso abre dos. En TCP, típicamente, los canales sí son bidireccionales, y el segundo nombre no haría falta. Es una particularidad del ejemplo y podemos dejarla de lado.

Lo que no es una particularidad del ejemplo, y que en cambio resulta prácticamente inevitable, es la terna de operaciones que aparece cada vez. Decir "siempre" sería demasiado, pero muy frecuentemente los canales de comunicación se van a usar de una forma muy particular: mandamos un mensaje, recibimos un mensaje, y lo deserializamos para saber qué contenido tiene. Eso se repite infinitas veces, cada vez que queramos que un componente se comunique con otro.

¿Y por qué vamos a estar haciendo eso una y otra vez? Porque esa secuencia se parece bastante a la forma que ya tenemos de llamar a un procedimiento. Cuando uno llama a un procedimiento, llama a una funcionalidad; esa funcionalidad hace algo y devuelve un valor. Son los parámetros que se le pasan, más el nombre del procedimiento, más la respuesta: exactamente las mismas tres piezas.

Eso es tan común que existe una solución para poner encima de los sockets sueltos, y esa va a ser la primitiva principal que vamos a usar durante toda la materia. Prácticamente nunca vamos a escribir sockets directamente: vamos a usar en cambio algo que se llama **remote procedure call**, o RPC. El estilo request-response es tan común que directamente recibió ese nombre propio. A veces no está del todo explícito que algo sea RPC, pero conceptualmente casi siempre termina siéndolo.

El origen de RPC está en los años ochenta, y responde otra vez a la ambición de agregar transparencia: querían que una llamada a un procedimiento local se pudiera reemplazar por una llamada a uno remoto, y que funcionara igual. Es exactamente la misma ambición que produjo el Network File System. RPC se sigue usando muchísimo, pero ya no se enfatiza tanto aquella transparencia, porque hay problemas que emergen de ahí.

¿Qué cambia respecto de lo que teníamos hasta ahora? Lo que se hace es separar. Todo esto vendría a ser la capa end to end, pero dentro de ella podemos imaginar a su vez dos capas. Arriba está la aplicación que uno escribe. Abajo está la capa de RPC, que le esconde a uno toda la interacción con los sockets. Más abajo todavía están los sockets, donde queda metida también la capa de transporte, y por debajo la red. Introducimos entonces una capa intermedia, y esa capa resuelve el problema de las comunicaciones.

[FIGURA: la aplicación arriba y la capa de RPC abajo, las dos dentro de la capa end to end, con la llave del middleware sobre la de RPC; más abajo los sockets y la red — pizarra pág. 15]

Este es uno de los tantos ejemplos de lo que se suele llamar el **middleware** de los sistemas distribuidos, una palabra que era muy popular en los noventa y que ya está un poco en desuso. Conviene desambiguarla, porque quienes escriben aplicaciones con Node y Express también tienen middlewares, y no son los mismos. Aquí el middleware era más bien una capa intermedia, porque resolvía exclusivamente problemas de comunicación y de acceso a un sistema distribuido, y era lo que proveía transparencia hasta cierto punto. El término, de todos modos, no termina de convencer: es tan amplio que no dice nada. Resulta preferible decir directamente que vamos a usar RPC.

El truco de RPC fue poder generar esa parte de manera reutilizable, de modo de no tener que programar nosotros mismos esa secuencia de tres operaciones cada vez. Queremos que lo que veamos tenga la interfaz de un procedimiento común, aunque por debajo esté ocurriendo algo completamente distinto.

La forma en que típicamente se hace esto, desde los ochenta hasta la actualidad, es generar un **stub**. Un stub es una pieza que representa a la función, pero donde la función en realidad no está. Desde nuestro código de aplicación vamos a ver una función común, con todo el aspecto de una función común: en el ejemplo se llama `GET_TIME`. Pero cuando la llamemos, y siendo que la implementación real vive en el servidor remoto, no vamos a estar llamando a esa implementación sino a un stub: una especie de proxy, un sustituto que está ahí en el medio. Lo que ese stub hace es el marshalling de los parámetros: toma los parámetros y el nombre de la función, y se los manda por el socket a otro stub que está del otro lado. Ese segundo stub los desarma, los extrae, y es él quien termina llamando a la implementación real. La función hace lo que tiene que hacer y devuelve algo; el stub del servidor captura ese resultado y se lo devuelve al que había llamado. Es, en definitiva, un truco: pareciera que la función está implementada de este lado, y en realidad está del otro.

[FIGURA: cliente y servicio, cada uno con su aplicación arriba y su stub abajo, y el request y el response cruzando de un stub al otro — notas pág. 6 / pizarra pág. 16]

En los ochenta se enfatizaba mucho que el engaño fuera total, igual que en el caso del NFS: quien llamaba a `GET_TIME` no sabía que la función vivía en otro lado. Y por los mismos problemas que allí, eso podía generar problemas. El modelo se sigue usando hoy, pero el cliente sabe que está llamando a algo que vive en otro lugar. Más que una forma de esconder la distribución, es una forma de acceder a un servidor remoto sin tener que programar uno mismo el socket y el marshalling, que es la parte engorrosa.

Así termina viéndose el código, sobre el mismo ejemplo del servidor de tiempo, ahora escrito con stubs.

```text
Client program

 1  procedure MEASURE (func)
 2      start ← GET_TIME (SECONDS)
 3      func ()                          // invoke the function
 4      end ← GET_TIME (SECONDS)
 5      return end - start
 6
 7  procedure GET_TIME (unit)            // the client stub for GET_TIME
 8      SEND_MESSAGE (NameForTimeService, {"Get time", unit})
 9      response ← RECEIVE_MESSAGE (NameForClient)
10      return CONVERT2INTERNAL (response)

Service program

 1  procedure TIME_SERVICE ()            // the service stub for GET_TIME
 2      do forever
 3          request ← RECEIVE_MESSAGE (NameForTimeService)
 4          opcode ← GET_OPCODE (request)
 5          unit ← GET_ARGUMENT (request)
 6          if opcode = "Get time" and (unit = SECONDS or unit = MINUTES) then
 7              response ← {"ok", GET_TIME (unit)}
 8          else
 9              response ← {"Bad request"}
10          SEND_MESSAGE (NameForClient, response)
```

Comparadas las dos versiones, lo que antes era una función que en el medio tenía que mandar, esperar y convertir ahora se ve como si fuera una llamada local. Las líneas 1 a 5 del programa cliente son una función común y corriente. Todo lo que antes estaba a la vista —el send, el receive, la conversión— quedó encapsulado en las líneas 7 a 10, que son el stub del cliente. Del otro lado ocurre lo simétrico: el programa del servicio es el stub del servicio.

Alguien tiene que escribir esos stubs, y si hubiera que escribirlos a mano para cada función, buena parte de la ganancia se perdería. La clave, y lo que hace que RPC sea usable en la práctica, es que los stubs se generan automáticamente.

### gRPC en la práctica, y por qué no REST

El ejemplo concreto va a ser la forma en que lo implementa Google en el lenguaje Go, y es además lo que vamos a usar en el primer trabajo práctico. La herramienta se llama **gRPC**. Uno tiende a leer la G como la inicial de Google, que efectivamente es quien lo inventó, pero el propio proyecto se encarga de desmentirlo: la sigla se lee como *gRPC Remote Procedure Calls*, en una definición circular, y la G cambia de significado en cada versión que publican.

*[Nota: El repositorio del proyecto mantiene el archivo `doc/g_stands_for.md` con la lista completa: en la versión 1.0 la G era por *gRPC*, en la 1.1 por *good*, en la 1.2 por *green*, en la 1.3 por *gentle*, y así sucesivamente.]*

Tanto el programa del cliente como el del servidor tienen sus particularidades, pero lo más llamativo aparece antes que los dos. La especificación del protocolo no vive adentro del código: va en un archivo aparte, que en este ejemplo se llama `time.proto`. Ahí adentro se define un **servicio** —así se llama—, con el nombre que uno quiera, y dentro de ese servicio el nombre de cada función que se quiera poder ejecutar, junto con el tipo de lo que recibe y el tipo de lo que devuelve. En el servidor de tiempo, el pedido no lleva ningún parámetro, porque es simplemente un get; y la respuesta lleva justamente el tiempo. Ese archivo es lo que une todo con todo.

[CÓDIGO PENDIENTE: el archivo time.proto con la definición del servicio, y los programas de cliente y servidor en Go que usan los stubs generados]

Hasta aquí no hay una sola línea de código Go. El `.proto` no es un programa, es una especificación, y una especificación no se ejecuta. Por eso, en algún momento hay que llamar a una herramienta especial que tome ese archivo y lo transforme en código Go propiamente dicho; en el ejemplo eso se dispara con un `make gen`. Y de esa herramienta hay una implementación para cada lenguaje: del mismo `time.proto` se puede generar código Go, código C o código Java.

Al ejecutar ese comando aparece un archivo nuevo. Lo primero que dice, en su primera línea, es que es código generado por gRPC y que no hay que modificarlo, porque cualquier cambio se pierde y puede romper el sistema. No tiene mucho sentido leer sus detalles —ni siquiera resulta cómodo navegarlo—, pero sí importa saber qué es: ese archivo es el stub, una biblioteca que generamos nosotros mismos y que implementa la especificación que definimos en el `.proto`.

Del lado del cliente, entonces, lo que hay que hacer es importar ese código generado, abrir una conexión con el servidor y, con esa conexión, generar un objeto cliente. Después se llama al método y con eso alcanza: a partir de ese momento uno se despreocupa del resto, el objeto responde, se conecta internamente con el remoto y resuelve el resto.

El servidor es un poco más complicado. Ahí hay que implementar esas funciones, las que declaramos en el `.proto`, y después pasárselas de alguna forma al código generado. Como Go no tiene clases, las implementaciones se meten en un **struct**, y ese struct se le pasa a `RegisterTimeServiceServer`, que también es código generado. Es la operación simétrica a la del cliente: al stub se le conectan las cosas implementadas por nosotros, y así funciona.

Lo que hay que escribir uno mismo son tres piezas: el `time.proto`, que define la interfaz; el código principal del cliente; y el código principal del servidor. Toda la parte tediosa —usar el socket, serializar y deserializar— la resuelve automáticamente gRPC, y ese reparto es el punto de todo esto. Y no es la única herramienta que trabaja así.

¿Por qué usaríamos RPC, con todo este aparato encima, y no REST, más allá de la diferencia de velocidad? Lo primero es desarmar la premisa, porque la velocidad no es el problema aquí: REST se podría usar tranquilamente.

La diferencia real es otra. REST es mucho más rígido, en el sentido de que no permite definir métodos propios. En REST hay básicamente cuatro o cinco métodos —`GET`, `POST`, `PUT`, todas esas cosas—, y sobre eso hay que inventar algunos paths que representen las operaciones que uno puede hacer. Eso viene bien cuando lo que tenemos está implementado sobre un servidor HTTP que no podemos modificar demasiado. Pero cuando tenemos control sobre todos los nodos del sistema —que es exactamente la situación de un trabajo práctico— resulta mucho más claro, semántica y conceptualmente, hacerlo del otro modo.

El servidor de tiempo, hay que admitirlo, es un mal ejemplo para mostrar esa diferencia, porque es REST-friendly: alcanzaría con hacer un `GET` al path del tiempo. El ejemplo que sí la muestra es una operación rara. Supongamos que queramos iniciar una máquina. En REST eso típicamente se resuelve con un `POST` y un path, con el método por un lado y el path por otro; con RPC uno simplemente lo diseña como si fuera una función normal, y encima la puede documentar como tal.

Hay además una ventaja técnica menor: como gRPC es binario, tiene el beneficio de ser un poco más rápido. Pero no diríamos que la velocidad es el argumento: a menos que haya que enviar grandes volúmenes de datos por la red, no se nota. Lo importante está a nivel del programador. No hace falta pensar cómo adaptar cada operación a lo que sería una interfaz REST: directamente se escribe el servicio, se escribe la interfaz como uno la quiere escribir. Y esas son procedimientos, que son mucho más flexibles que los métodos que ofrece REST.

Cuando más adelante veamos REST vamos a comprobar que con él se suele poder hacer lo mismo, pero forzando un poco la semántica: si la operación es para controlar una máquina, hay que decir `POST` a pesar de que no se está posteando nada. REST se inventó para otra cosa.

Y sin embargo, como en la práctica hay margen para la flexibilidad, muchas veces se usa REST de todos modos, porque es más conveniente: porque ya tenemos un servidor HTTP y no queremos instalarle encima uno de gRPC. En particular se usa mucho cuando la comunicación va a través de internet. En un Chrome no podemos instalarle un stub generado por nosotros apuntando a un servidor remoto; REST es más fácil, porque el browser ya implementa directamente ese protocolo.

Ahí está, dicho al revés, la dificultad de gRPC: el cliente tiene que generar la biblioteca, insertarla con los mecanismos del lenguaje y compilarla. Y eso es justamente lo que no se puede hacer con Google Chrome, ni con Safari, ni con ninguno de los browsers disponibles.

### Por qué RPC no puede ser transparente

Si bien en los ochenta se pretendía que una llamada remota fuera completamente transparente, no puede serlo, y hay dos razones. Es el mismo fracaso de ambición del Network File System.

La primera es breve y casi obvia: hay más latencia. No es lo mismo llamar a un procedimiento local que a uno que está en otra máquina, y son los mismos problemas que ya enumeramos.

La segunda es la importante. Aparecen nuevas formas de falla: las cosas pueden fallar de otra manera. Normalmente, cuando uno llama a un procedimiento, si algo falla, falla en el procedimiento. Aquí, en cambio, puede fallar de una forma muy molesta.

Normalmente uno hace el request y el otro le responde. Pero pueden pasar varias cosas. Una es que el request no llegue al servidor. La otra es que llegue, pero que no vuelva la respuesta. Una se rompe cuando estamos mandando; la otra se rompe cuando el otro está respondiendo.

[FIGURA: cliente y servidor con las dos flechas tachadas — la de ida, el request que no llega al servidor, y la de vuelta, la respuesta que no vuelve — notas pág. 6 / pizarra pág. 17]

Parece una sutileza, pero no lo es, porque desde nuestro punto de vista —somos el cliente— no hay una forma fácil de diferenciar una de la otra. En los dos casos observamos exactamente lo mismo: mandamos un request y no nos llegó nada. Puede ser que nunca haya llegado al servidor; o que sí haya llegado, que se haya ejecutado allá —bien o mal, eso tampoco lo sabemos— y que lo que falló haya sido la respuesta.

Más allá de si la operación funcionó o falló del otro lado, estos son problemas del enlace, de la capa de comunicación. Y no alcanza con elegir bien la capa de transporte. Incluso con TCP, que garantiza la entrega, puede fallar la conexión, se nos puede romper el socket y desconectarse. Y entonces no sabemos si lo que queríamos hacer llegó y se terminó ejecutando, o si nunca llegó.

A esta altura uno ya estará pensando formas de solucionarlo. De eso se trata lo que viene.

### Las tres semánticas de entrega

Esa imposibilidad de distinguir un request que se perdió de una respuesta que se perdió es la que da lugar a lo que vamos a llamar **semánticas de entrega**. Hay tres, básicamente, y lo que las distingue es qué podemos afirmar cuando la llamada termina.

*[Nota: La clasificación viene de la literatura fundacional de RPC. La primera taxonomía sistemática está en la tesis doctoral de Bruce Jay Nelson, *Remote Procedure Call* (Carnegie Mellon, 1981; publicada también como informe de Xerox PARC, CSL-81-9), cuya sección 2.2.2 se titula justamente "Call Semantics" y enumera bastante más de tres casos: *exactly-once*, *last-one*, *last-of-many*, *at-least-once*, *crash semantics*. Un trabajo paralelo de Alfred Spector, *Performing remote operations efficiently on a local computer network* (CACM 25(4), 1982), llegaba a distinciones parecidas del lado de los mensajes. La reducción a los tres nombres que usamos acá es la que hacen Saltzer y Kaashoek en el capítulo 4 del libro que seguimos. Vale la pena notar que Nelson perseguía *exactly-once* por la misma ambición de transparencia que produjo el Network File System, y que la implementación real que hizo después con Andrew Birrell en Xerox —*Implementing Remote Procedure Calls*, ACM TOCS 2(1), 1984— terminó ofreciendo garantías más débiles.]*

La primera se llama **at-least-once**, al menos una vez. El escenario es el mismo diagrama anterior: del lado del cliente, la aplicación arriba y el stub abajo; del lado del servidor, el stub abajo y la aplicación arriba. Una forma de recuperarse ante ese tipo de problemas —siempre desde la perspectiva del cliente, que mandó algo y no está obteniendo respuesta— es hacer **retry**. Y lo hace el stub automáticamente: la capa de gRPC manda un request, no recibe respuesta, lo vuelve a mandar, y así insiste hasta que el otro responde.

[FIGURA: cliente y servidor, cada uno con su aplicación y su stub, unidos por varias flechas paralelas que representan los reintentos, con el timer del lado del cliente — notas pág. 7 / pizarra pág. 17]

Todo esto ocurre a nivel de la capa de gRPC. Cuando uno compila la biblioteca tiene que saber qué comportamiento va a tener, si va a hacer retries o no, porque a fuerza de insistir el pedido termina pasando eventualmente. Quizá pase un tiempo y, después de un timeout, el stub desista y avise que no pudo entregar el pedido. Pero en principio, una forma de recuperarse es esa: insistir.

¿Cuál es el problema que introduce el retry? Que el servidor tiene que estar preparado para que un mensaje pensado para hacer un pedido le llegue múltiples veces. Y hay una observación fina: si bien TCP es un canal confiable, cuando hacemos retry la duplicación la estamos introduciendo nosotros, desde el lado del cliente. No es la red la que está duplicando: somos nosotros.

El razonamiento hay que seguirlo hasta arriba de todo, hasta la aplicación, porque es ahí donde se paga la cuenta. Si le mandamos muchos requests y se van perdiendo en el camino, no llegan. Pero si lo que estaba fallando eran las respuestas, entonces todos esos retries sí le llegaron al servidor, y eso se traduce en que el stub le entrega varias veces el mismo mensaje a la aplicación que tiene arriba. Esa aplicación tiene que poder soportar que un mensaje le llegue muchas veces y seguir funcionando bien.

Eso quiere decir que la operación tiene que ser **idempotente**. Una operación idempotente es, básicamente, una que si se ejecuta una vez, o dos, o mil veces, da el mismo resultado.

El ejemplo típico es borrar un archivo, aunque mirado con cuidado hay que afinarlo. Si uno hace un delete de un archivo que no existe y eso devuelve un error, técnicamente no es idempotente: la primera vez funciona y la segunda devuelve error. No rompe nada, pero no es exactamente lo mismo. Ahora bien, si el delete no falla cuando no encuentra el archivo, y teniendo en cuenta que su objetivo es en definitiva que ese archivo no exista más, entonces sí tenemos una operación idempotente de verdad: un cliente puede mandar delete catorce veces y no pasa nada.

El anti-ejemplo es una transacción bancaria. Supongamos que alguien nos transfiere doscientos mil pesos y que el sistema funciona mal y reintenta la operación. Entonces, en vez de acreditarnos doscientos mil pesos, genera dinero de la nada y termina acreditándonos un millón. Ese millón, además, dice exactamente cuántas veces se ejecutó la operación: cinco. El stub reintentó cuatro veces sobre un pedido que ya había llegado, y cada reintento sumó doscientos mil pesos que nadie transfirió. Sumar a una cuenta, obviamente, no es una operación idempotente. Lo importante es que estamos ante una propiedad de la capa de gRPC, y hay que saber cuál es para poder diseñar correctamente lo que va arriba.

La segunda forma de resolver el problema se llama **at-most-once**, a lo sumo una vez, y es mucho más simple que su nombre. El esquema es el mismo: se manda el pedido, falla por lo que sea, no se obtiene respuesta, y no se reintenta. Es, simplemente, decir "no retry".

[FIGURA: los mismos dos nodos unidos por una sola flecha, sin reintento — notas pág. 7 / pizarra pág. 17]

Por qué se llama así merece un poco de cuidado, porque el nombre describe lo que podemos afirmar y no lo que hacemos. Si el stub responde OK, tenemos la seguridad de que el servidor lo ejecutó una sola vez, y nada más que una vez. Si el stub responde un error de comunicación, en cambio, no podemos garantizar nada: puede que se haya ejecutado una vez, o cero veces. El error no nos dice nada; el OK sí. De ahí el "a lo sumo": nunca más de una vez, quizá ninguna.

¿Y qué se hace entonces cuando llega un error de comunicación? Se puede hacer un retry, pero a nivel de la aplicación: la aplicación se lo vuelve a pasar al stub, y entre las dos aplicaciones se entienden en que eso es un retry y lo manejan como corresponda. La capa del stub, por su parte, no asume nada.

Todo esto en general no es tan difícil, pero tampoco es tan automático como parece, y hay aquí una sutileza. Si la comunicación de abajo fuera UDP, la red misma podría duplicar mensajes, y podría llegar varias veces el mismo mensaje y ejecutarse varias veces, sin que nadie del lado del cliente haya reintentado nada. Por eso con UDP no se puede implementar at-most-once: aquí hay que usar TCP. Es exactamente la decisión que tomábamos al principio, cuando armábamos el socket en C y elegíamos `SOCK_STREAM` y no `SOCK_DGRAM`. Ahí parecía una flag más; aquí se ve para qué servía. Es el ejemplo que habíamos prometido de por qué el diseñador de un sistema distribuido tiene que conocer la capa de transporte, y decidirla.

Sobre el gRPC que vamos a usar en el trabajo práctico, todo indica que esta es la semántica que trae por defecto: intenta mandar el pedido una vez y, a menos que uno lo configure, no hace retry automáticamente. Los retries hay que hacerlos de forma controlada. At-least-once, del otro lado, es algo que se activa.

*[Nota: Efectivamente, en gRPC los reintentos vienen deshabilitados y se habilitan declarando una `retryPolicy` en la configuración del servicio, donde se fijan la cantidad máxima de intentos, los tiempos de espera entre uno y otro y los códigos de estado que ameritan reintentar.]*

Queda la tercera, **exactly-once**, exactamente una vez, que es la más simple de enunciar y ni siquiera necesita dibujo. Si el stub responde OK, se mandó una vez y nada más que una vez. Si el stub responde error, tenemos la seguridad de que no se mandó ninguna vez.

Con las tres sobre la mesa, esta misma clasificación aparece en otros lados con otros nombres. MQTT, el protocolo de mensajería que se usa en dispositivos de internet de las cosas, ofrece tres niveles de calidad de servicio —sus *QoS*—: el nivel 0 es at-most-once, el nivel 1 es at-least-once y el nivel 2 es exactly-once. Es la misma taxonomía con otra etiqueta, y conviene reconocerla cuando aparece disfrazada.

*[Nota: Los tres niveles están definidos en la especificación de MQTT. Con una salvedad que el paralelo con RPC no tiene: en MQTT el mensaje hace dos viajes, del publicador al broker y del broker al suscriptor, y el nivel de calidad de servicio se aplica a cada tramo por separado, de modo que pueden ser distintos.]*

Volviendo entonces a exactly-once: es el caso ideal, y por lo tanto es imposible. Imposible en sentido estricto. Podemos aproximarnos bastante, y de hecho es lo que se hace en general, usando las dos semánticas anteriores y algunos trucos. Pero garantizarlo, garantizarlo, nunca lo vamos a poder hacer. La razón es la separación física de las máquinas: uno le manda un request a la otra máquina y, en ese instante, el data center sufre una falla catastrófica. La operación se ejecutó, pero nunca vamos a obtener la respuesta, así que no podemos garantizar nada. Si el otro no responde, no hay exactly-once posible.

*[Nota: Por eso Martin Kleppmann, en el capítulo 11 de *Designing Data-Intensive Applications*, escribe que a este principio "se lo conoce como exactly-once semantics, aunque **effectively-once** sería un término más descriptivo". El argumento es el mismo que estamos por hacer: reintentar significa que un pedido puede llegar y procesarse muchas veces, y lo único que se consigue que ocurra una sola vez es el efecto observable. La frase la acuñó Viktor Klang en 2016, y su formulación es casi una receta: *effectively-once* es lo que se obtiene combinando at-least-once con operaciones idempotentes. Es literalmente lo que hacemos en lo que sigue con el idempotency id.]*

Ahora bien, esos casos son poco frecuentes, así que en general se puede lograr algo suficientemente parecido. Una forma es apoyarse en at-least-once y, si la función del servidor no es idempotente por naturaleza —una transacción, por ejemplo—, introducirle la idempotencia nosotros.

El ejemplo concreto de cómo se hace eso —que es una de las tantas formas que hay, no algo para estudiar de memoria— es el siguiente. A nivel de la aplicación, y sobre una capa de abajo que es at-least-once, mandamos el request con la operación —digamos, agregar dinero— y con la suma, y le agregamos un tercer campo: un número generado que se llama **idempotency id**.

[FIGURA: el cliente con su capa at-least-once mandando tres veces el mismo pedido, y el servidor con su aplicación y un storage persistente al costado donde registra los identificadores ya procesados — pizarra pág. 18]

La mecánica es esta. La aplicación le manda el pedido a la capa de abajo, y esa capa se lo manda al otro las veces que quiera; hace muchísimos retries. El servidor puede recibir el mismo mensaje muchas veces, igual que antes. Pero la aplicación del servidor mantiene un **storage persistente** de esos idempotency ids. Entonces, si recibe varias veces un mensaje con el mismo idempotency id —y siempre va a ser el mismo, porque quien está haciendo los retries es la capa de abajo, sobre el mismo pedido original—, ejecuta uno e ignora todos los demás.

Esos retries, además, los podemos hacer nosotros mismos, mandando el mismo mensaje varias veces con el mismo idempotency id. No hace falta que la capa de abajo sea at-least-once: puede ser la otra semántica, y los retries los hace la aplicación directamente.

Eventualmente el pedido pasa. Y cuando pasa sabemos que, a pesar de haber mandado muchos requests y de no haber obtenido respuesta, si llegaron todos y se procesaron todos, la operación se ejecutó una sola vez, porque la aplicación se encargó de no ejecutar varias veces lo mismo. Es una de las técnicas que se usan para volver idempotente una operación que no lo es, valiéndose de un storage persistente. Y esta clase de técnicas es lo que vamos a ver durante el resto de la materia.
