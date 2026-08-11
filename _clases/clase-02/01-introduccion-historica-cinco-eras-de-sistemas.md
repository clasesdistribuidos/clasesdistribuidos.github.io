---
title: "1. Introducción histórica: cinco eras de sistemas distribuidos"
parent: "Clase 2 — MapReduce"
nav_order: 1
---

# 1. Introducción histórica: cinco eras de sistemas distribuidos
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


MapReduce es un nombre con el que probablemente ya nos hayamos encontrado antes de llegar a este punto. La forma habitual de presentarlo es como modelo de programación: se escribe una función map y una función reduce, y a veces se las ejecuta localmente, sobre una sola máquina. Ese enfoque es legítimo y es útil, y probablemente sea el que ya conocemos. Lo que aquí nos proponemos es complementarlo, porque deja fuera el interior del sistema, y es justamente cómo funciona por dentro lo que queremos entender.

De todos modos vamos a repasar de manera general el modelo de programación de MapReduce, para partir de una base común; pero el objetivo está en otro lugar, en la maquinaria que hace que ese modelo se pueda ejecutar sobre un conjunto grande de máquinas.

Y antes de ese repaso conviene dar un paso todavía más atrás y hacer una introducción histórica, una cronología general de los sistemas distribuidos. Es lo que explica por qué MapReduce existe y cuándo surgió. Vamos a recorrer cinco eras, y MapReduce va a aparecer en el lugar que le corresponde: como respuesta a una pregunta que alguien se estaba haciendo en ese momento y no antes.

## Era 1: los fundamentos teóricos (70s–80s)

El campo de los sistemas distribuidos, cuando todavía no se llamaba así, surge de problemas teóricos. No de un producto ni de una necesidad comercial: de problemas que empezaron a encontrar los primeros científicos que trabajaban con redes. El período que nos interesa son los años 70, ya bien avanzados, y los 80.

La figura central de esa era es Leslie Lamport, y lo más simple es presentarlo por algo que quizás nos resulte más familiar que sus aportes a los sistemas distribuidos: inventó LaTeX, la herramienta con la que los científicos escriben sus papers. También inventó TLA+, un lenguaje para especificar sistemas, y escribió sobre eso un libro que se llama *Specifying Systems* y que está disponible gratuitamente en internet. TLA+ es, en el fondo, un mecanismo para comprobar que un sistema distribuido es funcionalmente correcto. Estuvo cerca de entrar en el programa de esta materia y quedó fuera porque nos alejaba demasiado del tema central, pero conviene saber que existe.

Lamport era matemático y además tenía conocimiento de física y de la teoría de la relatividad. De ahí surgió una de sus primeras observaciones, que él mismo relató en una entrevista: algo que ocurre en la teoría de la relatividad —la imposibilidad de sincronizar relojes— también ocurría en los sistemas distribuidos.

{: .nota }
> La relatividad especial establece que no hay un orden total invariante de los eventos en el espacio-tiempo: dos observadores distintos pueden discrepar sobre cuál de dos eventos ocurrió primero, y lo único que queda es un orden parcial en el que un evento precede a otro si puede afectarlo causalmente. Es exactamente esa estructura la que Lamport trasladó a los sistemas distribuidos. La referencia completa es Leslie Lamport,* Time, Clocks, and the Ordering of Events in a Distributed System*, Communications of the ACM, vol. 21, n.º 7, julio de 1978, pp. 558-565.

Dos relojes quieren ponerse en hora uno respecto del otro y solo pueden comunicarse mediante mensajes. El primero le envía al segundo la hora que tiene, y cuando ese mensaje llega, el segundo no sabe cuánto tardó en el camino: puede ser que el primer reloj ya se haya desactualizado y que la hora recibida sea una hora vieja. Puede pedir confirmación, pueden intercambiar mensajes indefinidamente, y la sincronización exacta de los dos relojes no se va a poder lograr.

Ese fue uno de los primeros problemas que identificó Lamport, y uno de los tantos. La conclusión que extrajo orienta el resto de la materia: si los tiempos absolutos son inalcanzables, no son lo importante. Vamos a ver que muy pocos sistemas distribuidos se apoyan en relojes de tiempo real. Lo que importa mucho más es otra cosa: qué ocurre primero y qué ocurre después.

La pregunta fundamental de la era la planteaban, principalmente, matemáticos: no había todavía aplicaciones prácticas empujando, sino personas que pensaban el problema en abstracto. La pregunta es cómo hacer para coordinar distintos procesos cuando hay dos recursos que no se pueden compartir. Uno es la memoria. El otro es el reloj. Ninguno de los dos está compartido en un sistema distribuido. Cómo se sincronizan entonces esos procesos, y qué problemas surgen a partir de eso, no lo vamos a resolver de una vez: a lo largo del curso vamos a ir viendo muchas técnicas que los mitigan.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    los dos recursos que un sistema distribuido no comparte — memoria y reloj tachados — y lo que de ahí se deriva: relojes de Lamport, relojes vectoriales, causalidad
    <span class="figura-ref">pizarra pág. 1</span>
  </figcaption>
</figure>

Entre los resultados que se descubrieron en esta época —no todos por Lamport— hay tres que vale la pena nombrar desde ya. El primero son los relojes de Lamport, que están más o menos por la mitad del programa de la materia, y junto con ellos los relojes vectoriales. Aquí hay que evitar una confusión que el nombre invita: no vamos a solucionar el problema de tener un reloj global para todo el sistema. La palabra "reloj" hace referencia a un mecanismo para asegurar con certeza que un mensaje que se encuentra en algún nodo ocurrió después que otro mensaje que se encuentra en otro nodo. Es un orden relativo, no absoluto. Y lo que se trata de resolver con eso tiene nombre: la causalidad.

{: .nota }
> Los relojes vectoriales no son de Lamport, y por eso la aclaración de que no todo lo de esta era salió de él. Los desarrollaron de forma independiente y sin conocer el trabajo del otro Colin Fidge —*Timestamps in Message-Passing Systems That Preserve the Partial Ordering*, 1988— y Friedemann Mattern —*Virtual Time and Global States of Distributed Systems*, 1989—. La diferencia técnica con los relojes de Lamport es la que los motiva: un reloj de Lamport captura una condición necesaria de la causalidad, mientras que un reloj vectorial captura la implicación en los dos sentidos. Los vamos a ver en detalle más adelante en la materia.

El segundo resultado —este sí formalizado por Lamport— es la máquina de estados replicada, que también se nombra como máquina de estados distribuida y que vamos a ver en detalle la clase que viene. La idea es muy simple, y va a ser importante cuando lleguemos a los sistemas de storage y a la pregunta de cómo se obtiene ahí tolerancia a fallas. Una forma de tenerla es contar con réplicas: en vez de una base de datos, dos bases de datos iguales, con los mismos datos.

¿Y cómo logramos que haya dos bases de datos que sean iguales? Consideremos que una base de datos es una máquina de estados, algo así como un autómata finito: un objeto en el que, a partir de un evento, se sabe a qué otro estado va a pasar. Si eso es cierto, y si le enviamos los eventos en el mismo orden a dos de esas máquinas, siempre nos va a quedar el mismo estado final.

Se entiende mejor con un ejemplo, porque esta propiedad la tienen muchísimas cosas además de una base de datos. Pensemos en nuestra propia cuenta bancaria. Si retrocedemos un mes y partimos del saldo que teníamos entonces, y después tomamos todas las transacciones del último mes y las aplicamos en el mismo orden en que ocurrieron, vamos a llegar exactamente al saldo que tenemos ahora. ¿Por qué funciona? Porque aplicamos las mismas operaciones en el mismo orden, y porque cada operación es determinista. Cuando se acreditan 200 pesos en una cuenta no interviene ningún número aleatorio: sumar es determinista, siempre produce el mismo resultado.

Planteémoslo con dos máquinas, A y B, y una secuencia de operaciones —pocas, para simplificar el dibujo: a, b, c y d—. Se las aplicamos a A en ese orden. Si a la otra máquina le aplicamos las mismas operaciones y en el mismo orden, el resultado final de A y el de B va a ser el mismo. Ahí, en la palabra "orden", empieza a aparecer el concepto que veníamos viendo un poco más arriba con los relojes lógicos.

Y con eso, aparentemente, resolvimos la replicación. Pero lo que hicimos en realidad fue trasladar el problema a otro lugar: al orden. Porque ahora la pregunta es cómo hacemos para que llegue exactamente el mismo orden a las dos máquinas.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    dos máquinas A y B recibiendo la misma tira de operaciones a, b, c, d en el mismo orden, y la pregunta por el orden que lleva a consenso → Paxos → Raft
    <span class="figura-ref">pizarra pág. 1, fig. 1</span>
  </figcaption>
</figure>

Una respuesta inmediata: que haya una única máquina encargada de definir el orden. Puede tener un log de operaciones, y eso es lo que les va enviando a las dos réplicas, en el orden en que lo tiene registrado. Y funciona. El problema es que ahí trasladamos el problema de la replicación a esa única máquina: si esa falla, falla todo. Como se ve, la cuestión no es tan sencilla.

Lo que hay que hacer es otra cosa: hace falta un pequeño algoritmo para que las dos máquinas se pongan de acuerdo entre ellas sobre cuál es la siguiente operación. Si en un momento dado hay varias operaciones posibles, esas dos máquinas tienen que acordar cuál es la que sigue. Ese es el problema de consenso, el tercero de los resultados que salen de esta era: muchas máquinas, y cómo se ponen de acuerdo en un valor.

Bastante más tarde, hacia fines de los 80, Lamport propuso un algoritmo que resuelve el problema de consenso y que se llama Paxos. Paxos es notablemente difícil de entender: tiene toda una historia alrededor de esa dificultad. Y sin embargo el problema que resuelve es central.

{: .nota }
> La fecha conviene aclararla, porque la referencia que se cita habitualmente es de casi diez años después. Lamport escribió el algoritmo y lo publicó como reporte técnico del DEC Systems Research Center —*The Part-Time Parliament*, SRC Research Report 49— y lo mandó a Transactions on Computer Systems en 1989. Ahí empieza la historia: el paper presenta el algoritmo como una alegoría sobre los legisladores de la antigua isla de Paxos, y las reseñas fueron hostiles —una de ellas, según Lamport, era una diatriba contra el uso del humor en un paper científico—. Lo volvió a mandar en 1995 y salió publicado recién en 1998, en ACM Transactions on Computer Systems, vol. 16, n.º 2, pp. 133-169. O sea que el algoritmo es de fines de los 80, como dice la cronología, y la publicación es de fines de los 90.

Cuando se trabaja lo suficiente con sistemas distribuidos, tarde o temprano se llega a que en algún lugar hay que resolver que varias máquinas se pongan de acuerdo en algún valor.

Podríamos entonces implementar Paxos, pero tiene dos problemas. El primero es que el consenso es de a un valor: tendríamos que hacer un Paxos para acordar la primera operación, otro Paxos para la segunda, y así sucesivamente. Hay formas de resolver eso, pero no resultan tan prácticas. El segundo problema es que Paxos es muy difícil de implementar. El caso favorable es sencillo; los casos complicados —los que aparecen cuando algo falla en el momento menos conveniente— son los difíciles.

Por eso lo que vamos a estudiar con mucho detalle es otro algoritmo más moderno: Raft, de alrededor de 2014. Raft se inventó justamente para que el consenso sea más fácil de entender de lo que es en Paxos, y aun así va a ser el paper más difícil que tengamos que leer en toda la materia. Hace falta dedicarle una semana, leyéndolo un poco todos los días, para entender el algoritmo. Como todos estos algoritmos complicados, Raft está hecho de muchas piezas independientes que interactúan entre sí para que el conjunto funcione. La forma de leerlo es la que cada uno descubre por su cuenta: se piensa un caso de borde, se vuelve al paper, y ahí aparece la respuesta, con las razones por las que ese caso no rompe el algoritmo. Ese ida y vuelta es el trabajo, y con él vamos a tener una idea clara de lo difícil que es este problema.

Toda esta primera era es la parte más matemática de la materia y, aunque exija esfuerzo, resulta estimulante. Queda una advertencia antes de seguir: las eras que vamos a recorrer no son completamente independientes ni tienen límites nítidos. Se solapan. Paxos es de fines de los 80 y Raft es de 2014, de modo que las respuestas a las preguntas de esta primera era siguieron llegando cuando las otras eras ya habían pasado.

## Era 2: los intentos de transparencia (80s–90s)

Ya en los años 80 se puede decir que se pasó a cuestiones más prácticas, a sistemas que alguien efectivamente quiso construir y poner en funcionamiento. A esa etapa vamos a llamarla era dos, la de los intentos de transparencia, y si hay que ponerle fechas, va de los 80 a los 90.

La estrategia que perseguían quienes trabajaban en esa época se resume en una línea: tenemos una red, vamos a hacer un sistema distribuido, y hacer un sistema distribuido implica esconder la red. Que no se note lo que hay por debajo.

El primer ejemplo que vimos de ese programa, en la clase anterior, es el network file system. Ya vimos cómo funcionaba, con resultados desparejos: cuando funcionaba bien, funcionaba bien; cuando no, los problemas eran considerables.

El otro mecanismo que surgió en esta época, y con el que terminamos la clase anterior, son las remote procedure calls, RPC. Lo que se quería hacer inicialmente con una remote procedure call era que la red fuera completamente transparente: que quien la llama piense que está haciendo una llamada local, y nada más. Hoy la situación es otra, y es mejor. Nos beneficiamos de que llamar a un RPC sea sencillo, porque se parece a una llamada local, pero quien la llama sabe perfectamente que se trata de una API que está yendo a otro sistema. Por eso RPC es lo que mejor sobrevivió de una época en la que se trataba de esconder la red a toda costa: se quedó con la comodidad y abandonó el engaño.

Hay otra línea de trabajo interesante que surgió en esta época y que hoy tiene poca actividad: los sistemas operativos distribuidos. Hubo varios ejemplos famosos, o por lo menos famosos en su momento.

Uno era Amoeba, desarrollado por el equipo de Tanenbaum. Tanenbaum es un nombre que aparece en varios lugares: es el autor del libro de sistemas operativos, el mismo que había hecho MINIX, y el mismo que protagonizó el célebre debate con Linus Torvalds —la historia que se cuenta siempre en las primeras clases de sistemas operativos—. Ese Tanenbaum dirigía un equipo que intentaba construir un sistema operativo distribuido: un sistema operativo que pareciera estar por completo en la máquina propia, pero que en realidad estuviera repartido en muchas partes distintas.

Eso se abandonó por los mismos problemas que tenía el NFS: cuando fallaba, fallaba de formas difíciles de diagnosticar.

Hay, sin embargo, algo curioso. Hoy existen sistemas que se parecen a un sistema operativo distribuido y que a la vez son algo muy diferente. Se podría sostener que uno de estos orquestadores de data center —Kubernetes, por ejemplo— cumple algunas funciones de sistema operativo; y a la vez la objeción es inmediata, porque se trata de cosas distintas. Las dos lecturas se pueden defender.

Otro conocido de esta época es Plan 9, que sí quería ser un sistema operativo distribuido, y algunas de sus ideas quedaron y son interesantes. El nombre completo era Plan 9 from Bell Labs, y era un guiño a *Plan 9 from Outer Space*, una película antigua de Ed Wood. El proyecto en sí todavía se puede instalar y explorar, aunque está prácticamente inactivo; de todos modos, no quedó sin consecuencias.

{: .nota }
> Vale la pena decir cuáles son esas ideas que quedaron, porque una de ellas la usamos todos los días y otra la vamos a usar en este mismo trabajo práctico. **UTF-8** salió de ahí: Ken Thompson y Rob Pike lo diseñaron en 1992 justamente mientras convertían Plan 9 para que soportara Unicode en todo el sistema, lo implementaron durante el primer fin de semana de septiembre de ese año, y llegaron con eso a la reunión de la semana siguiente en la que X/Open lo eligió como formato de bytes de Unicode; hoy es la codificación dominante de la web. **9P**, el protocolo de Plan 9 para acceder a sistemas de archivos jerárquicos, está implementado en Linux y en el Windows Subsystem for Linux. La llamada `rfork`, que es la base de los threads livianos, se adoptó tal cual en los derivados de BSD y reapareció en Linux como `clone`. Y **Go**, el lenguaje de esta materia, lo diseñaron Robert Griesemer, Rob Pike y Ken Thompson: los tres habían trabajado en Plan 9, y buena parte de la simplicidad del lenguaje viene de esa experiencia.

Y toda esta serie de intentos de esconder la red fue refutada por un paper fundacional, del que hablamos la clase anterior: *A Note on Distributed Computing*, escrito por Waldo y otros en 1994. El argumento es directo: si todos estos intentos no están llegando a ningún resultado, no hay que tratar de esconder tanto la red. Dicho en una frase, lo que sostiene el paper es que no es una buena idea ignorar que hay una red por debajo, porque después aparecen todos los problemas.

{: .nota }
> *A Note on Distributed Computing*, de Jim Waldo, Geoff Wyant, Ann Wollrath y Sam Kendall, Sun Microsystems Laboratories, informe técnico SMLI TR-94-29, noviembre de 1994. Las cuatro características de la red que el paper enumera como imposibles de esconder —latencia, acceso a memoria, concurrencia y fallas parciales— son las que vimos en detalle en la clase anterior.

## Era 3: el middleware (90s)

Pasemos a los 90, donde los problemas ya son de otro tipo. Los 90 son la época de la computación corporativa: había muchas empresas cuyo funcionamiento se apoyaba fuertemente en tener sistemas, y del otro lado había otras —es la época de Microsoft y de IBM— que les vendían esos sistemas a las distintas empresas. El problema principal que se quería resolver ahí no era el volumen de datos. Big data no aparece en esta era: el término ni siquiera existía, es mucho más reciente, y en general no había tantos datos. Lo que había que resolver era la comunicación entre esos sistemas, cómo se comunica de manera distribuida un sistema con otro. Esta materia estuvo durante años influida por esta época y con el tiempo se fue corriendo hacia temas más modernos, pero la era del middleware sigue siendo una bisagra en la cronología, porque es donde se toma una decisión conceptual que no se revirtió nunca más.

La decisión es esta: se descarta la idea de que se pueda hacer un sistema donde toda esa red y toda esa comunicación estén completamente escondidas. En lugar de esconderlas, se las reconoce y se les da un lugar propio en el esquema. Arriba tenemos la aplicación, abajo tenemos la red, y en el medio ponemos una capa que se encarga de esas comunicaciones: el middleware. Porque eso es lo que middleware significaba en esta época, tomado literalmente: todo el software que estaba en el medio. ¿En el medio de qué? En el medio entre nuestra aplicación y la red, resolviéndonos todos esos problemas.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    las tres capas —aplicación, middleware y red— y las cuatro responsabilidades que el middleware absorbe: comunicación, discovery, transmisión de datos y manejo de errores
    <span class="figura-ref">notas pág. 2, fig. 1 / pizarra pág. 2</span>
  </figcaption>
</figure>

¿Qué cuestiones resolvía el middleware? La comunicación, por empezar, que es lo que ya venimos nombrando. Después el discovery: nuestro sistema se quiere conectar con otro, y hay que averiguar cuál es y cómo se llama. Eso la aplicación no lo quiere resolver; lo que quiere es que alguien se ocupe por ella. Después la transmisión de datos. Y por último el manejo de errores, que en un sistema donde la comunicación pasa por una red es una responsabilidad enorme y no un detalle.

Había varios tipos de middleware en esta época, y algunos clásicos que fueron material de enseñanza habitual durante muchos años, hasta que el paso del tiempo los volvió anacrónicos. Uno de ellos era todo un framework de gran tamaño para la comunicación entre distintas aplicaciones, una especie de RPC complejo —la simplificación es fuerte y algún especialista podría objetarla, pero resulta útil—. Se llamaba CORBA, que quiere decir Common Object Request Broker Architecture, y era un estándar de uno de esos comités de estandarización. Simplificando otra vez, lo que CORBA proponía eran objetos distribuidos: llamar a métodos que estaban remotos. Hoy es difícil encontrarlo implementado; seguramente haya algún banco o alguna empresa que lo siga usando, pero no es algo que se encuentre en la práctica moderna.

{: .nota }
> El comité es el **Object Management Group** (OMG), un consorcio de la industria fundado en 1989 justamente para estandarizar la interoperabilidad entre sistemas de objetos. CORBA 1.0 salió en octubre de 1991 y traía el modelo de objetos, el IDL —el lenguaje de definición de interfaces— y las APIs para invocación dinámica, con un único mapeo de lenguaje, a C. La primera versión ampliamente difundida fue CORBA 1.1, de febrero de 1992. Fuente: la historia de CORBA publicada por el propio OMG.

¿Y Java RMI, dónde entra? La pregunta es natural, porque RMI también consiste en llamar a métodos remotos y parece lo mismo. La respuesta es que RMI está mucho más cerca de RPC que de CORBA. CORBA era todo un estándar amplio y complejo: había que instalar distintos componentes, servidores intermedios, toda una infraestructura alrededor. RMI, en cambio, es la forma en que Java resuelve el RPC, que es el concepto más general. Y ese concepto es lo suficientemente general como para abarcar bastante: incluso REST, conceptualmente y en algunos casos, se podría considerar una especie de RPC, porque en el fondo se trata de llamar a funciones que están en otro lugar, remotas. Conviene más quedarse con RPC como concepto que con cualquiera de sus implementaciones concretas, y RMI se ubica ahí, como una forma de eso.

El otro clásico de la era no es exactamente igual, porque no desapareció: se transformó y regresó. Se llama MOM, message oriented middleware. No es tan central hoy como en los 90, que fueron su época, porque ahora hay muchas otras alternativas; pero este tipo de sistemas se sigue usando en la actualidad, y eso es lo que hay que retener.

La idea es la siguiente. RPC es sincrónico: se llama al servidor remoto y quien llamó queda bloqueado hasta recibir respuesta. Es la versión bloqueante de una llamada, pero en un sistema distribuido: se lo llama y responde. La definición correcta de sincrónico es otra —que hay un tiempo acotado para responder—, aunque en la práctica lo que se observa es exactamente eso: se llama, se bloquea, responde. La alternativa es la comunicación asincrónica: se envía un mensaje y no se espera nada más, y después quien tiene que recibirlo lo recibe. Quien envía no espera, continúa con su trabajo.

{: .nota }
> La precisión sobre qué significa "sincrónico" es exacta y conviene retenerla, porque la palabra se usa en dos sentidos que es fácil confundir. Uno es el sentido coloquial de programación: la llamada bloquea. El otro es el sentido que tiene en la teoría de sistemas distribuidos, y es el que el apunte llama la definición correcta: un **sistema sincrónico** es aquel en el que hay una cota superior conocida para el retardo de los mensajes y para la velocidad de procesamiento de los nodos. Un **sistema asincrónico** es el que no tiene ninguna cota: un mensaje puede tardar arbitrariamente, y lo único que se garantiza es que eventualmente llega. La distinción no es una sutileza terminológica: casi todos los resultados de imposibilidad de la materia dependen de en cuál de los dos modelos estamos.

Muchas veces la semántica de la comunicación sincrónica —el comportamiento que nos provee el RPC— es mucho más fácil de razonar, porque generalmente lo que tenemos que hacer es enviar un pedido y esperamos una respuesta. La mayoría de las veces es así. Pero en muchos otros casos no necesitamos esperar esa respuesta: lo único que nos importa es enviar el mensaje y que alguien en el medio nos garantice que ese mensaje fue recibido y que eventualmente se le va a entregar al receptor que corresponde. La definición imprecisa de esto, que es también la más citada, es "envío un mensaje y me despreocupo".

Los message oriented middleware tenían algunas características, y la más importante era que eran persistentes. Si queríamos enviarle un mensaje a otro servidor y ese servidor estaba apagado por cualquier razón, el middleware lo guardaba, lo mantenía, y seguía intentando entregarlo, hasta que eventualmente lo lograba. El mensaje sobrevivía entonces a la ausencia del destinatario, y quien lo había enviado no se tenía que ocupar de reintentar nada. Esa persistencia era uno de los problemas que nos resolvía. Y también nos resolvía el discovery, porque el mensaje se enviaba al canal de mensajes sin saber realmente quién lo iba a recibir.

Todo esto lo vamos a estudiar más adelante en un contexto más actual, que es el de las colas de mensajes, dicho más explícitamente, y el de los sistemas de streaming. En la práctica ya no se dice tanto MOM: message oriented middleware es un término poco frecuente hoy. Pero estamos hablando del mismo tipo de sistemas, y la conclusión que importa es doble: se sigue usando, y además de que se sigue usando, es importante.

¿Puede gRPC funcionar de forma asincrónica, sin romper con el concepto? Hasta cierto punto. gRPC tiene un modo que se llama de streams: en vez de hacer una llamada y recibir una respuesta, se pueden enviar muchos requests y después también recibir muchas responses. Eso atenúa el bloqueo a la espera de una respuesta, que según el contexto puede ser costoso. Pero el límite es el mismo problema de antes: si quien lo recibe está caído, no nos podemos conectar, y entonces no le podemos enviar nada. El problema no desaparece.

Ejemplos más actuales de esta familia hay varios. SQS, que es el servicio que tiene Amazon para enviar mensajes. RabbitMQ. Kafka, que es un poco diferente pero que podríamos ubicar en la misma categoría. Y el de Google, que se llama Pub/Sub. Todos se siguen usando en la actualidad. gRPC tiene algo de esta semántica más asincrónica, más orientada a streams, pero nosotros vamos a usar más la otra, la de llamar a una función y recibir su respuesta, porque la de streams no está en RPC en general: es algo particular de gRPC.

## Era 4: la era web (2000s)

Llegamos a la era que más nos importa, la que vamos a llamar la era web, alrededor del año 2000. Lo que aparece aquí es la banda ancha, y con ella la posibilidad de que mucha gente genere mucha información muy rápido. Aparece internet, y aparecen las bases de datos gigantescas.

Con esos datos aparecen también las empresas que se dedican a trabajar con ellos, y lo que más vamos a ver en la materia son desarrollos que surgieron durante esta época. Vale nombrar ya los papers, aunque después los veamos en detalle, porque ubicarlos en el tiempo explica por qué existen. Google File System salió en 2003. MapReduce, que es el que vamos a ver hoy, en 2004; los dos son de Google, igual que BigTable, de 2006, que no cubrimos en la materia y queda como lectura para quien tenga la curiosidad. Y Dynamo, de 2007, que es de Amazon y que sí vamos a estudiar.

Todas estas empresas fueron las primeras que se encontraron con el problema. Hoy muchos de esos son problemas más o menos resueltos, y precisamente por eso nos interesa cómo hicieron para resolverlos la primera vez. Les tocó porque fueron las primeras que tuvieron que manejar cantidades gigantescas de datos, y las herramientas que existían en ese entonces no soportaban semejante volumen. Los sistemas distribuidos de ese momento estaban enfocados en otra cosa: en la comunicación entre sistemas distintos, en el mensaje sincrónico contra el asincrónico, en todos los problemas que acabamos de recorrer. No estaban pensados para escalar.

Y esta época sigue siendo la actual. Lo que resuelven hoy los sistemas distribuidos son problemas de escala: grandes volúmenes de datos, y la pregunta de cómo se los maneja.

## Era 5: el cloud computing (2006–hoy)

Y de ahí, casi sin corte, esto evoluciona al cloud computing. La idea es simple de enunciar: todas esas técnicas que las empresas desarrollaron en la era anterior para resolver sus propios problemas, empezar a venderlas como servicio. De manera análoga a como se vende la electricidad o el gas.

El ejemplo concreto es el storage. Hoy se puede alquilar capacidad en la web en lugar de comprar el hardware: el sistema de storage lo tiene Amazon y nosotros le pagamos por usarlo. Estas dos últimas eras, la era web y el cloud, son el recorte que estudia la materia, y son lo más relevante del momento.

De las eras anteriores vamos a ver algo, aunque no todo. De CORBA no vamos a ver nada. De MOM sí: en particular Kafka, los sistemas de streaming, y algo de SQS, que ya nombramos más arriba. Quizás no tanto cómo funcionan por dentro, pero sí cuál es la idea de cada uno.

Queda lo más interesante de toda esta cronología, que es justamente lo que la cierra. Cuando los equipos de estas empresas —Google, Amazon, Facebook— se propusieron resolver los problemas de escala, tuvieron que usar la teoría que habían desarrollado los otros, los de la primera era. Gran parte de esa teoría había quedado inactiva, y se retomó cuando hubo que resolver efectivamente la replicación de bases de datos enormes, o el consenso. Un indicio de ese resurgimiento es la fecha de Raft: aparece recién en 2014. Pasaron unos quince años hasta que volvió a surgir un algoritmo de consenso útil y práctico, y lo que lo impulsó fue esta necesidad.

Falta un matiz, y es el que explica por qué las fechas de los papers resultan algo engañosas. Estas empresas internamente habían llegado antes a desarrollos equivalentes, pero no los publicaron. Amazon tenía una versión interna de algo muy parecido a Raft.

{: .nota }
> De los sistemas internos concretos que había en Amazon antes de 2014 no hay documentación pública, pero la afirmación general está bien respaldada por dos casos que sí se publicaron. Google usaba Paxos en **Chubby**, su servicio de locks, y contó cómo fue implementarlo de verdad en *Paxos Made Live — An Engineering Perspective* (Chandra, Griesemer y Redstone, 2007); y **ZAB**, el protocolo de atomic broadcast de ZooKeeper, es de 2008. Los dos son anteriores a Raft y los dos estaban en producción. Hay además un antecedente que corrige la idea de los quince años de vacío: **Viewstamped Replication**, de la tesis doctoral de Brian Oki dirigida por Barbara Liskov (MIT, mayo de 1988), es un protocolo basado en líder que precede en cerca de un año a la primera publicación de Paxos, y es estructuralmente más parecido a Raft que Paxos — el propio paper de Raft lo reconoce como su pariente más cercano. O sea que lo que faltó durante quince años no fue un algoritmo de consenso que funcionara, sino uno pensado desde el principio para poder entenderse.

---
