---
title: "1. Comunicación indirecta"
parent: "Clase 13 — Sistemas de mensajería"
nav_order: 1
---

# 1. Comunicación indirecta

El tema de esta clase son los sistemas de mensajería, que durante muchos años se conocieron como *message-oriented middleware*, o MOM. Es un nombre viejo —enseguida vamos a ver por qué cayó en desuso—, pero es el que aparece en la bibliografía clásica. Nosotros los vamos a llamar sistemas de mensajería. El tema es además de un nivel más alto que el de las clases anteriores: en lugar de desmenuzar un algoritmo, vamos a ver primero cómo se usan estos sistemas y después, a grandes rasgos, un par de implementaciones.

Una advertencia sobre el paper de Kafka, que es la lectura de esta clase. No entra en profundidad en los detalles de implementación —la replicación, por ejemplo, no está ahí sino en otro paper—. Su valor es otro: al principio hace muchas referencias a sistemas similares, y eso lo vuelve un buen mapa del terreno. Es también uno de los papers más accesibles de la materia.

{: .nota }
> El paper es Jay Kreps, Neha Narkhede y Jun Rao, «Kafka: a Distributed Messaging System for Log Processing», NetDB'11 —6th International Workshop on Networking Meets Databases—, Atenas, 12 de junio de 2011. Varios gestores bibliográficos lo citan con el venue equivocado, atribuyéndolo a la conferencia DEBS; el «6th» corresponde al workshop NetDB. La replicación, efectivamente, no está ahí: se describe en Jun Rao, «Intra-cluster Replication in Apache Kafka», LinkedIn Engineering blog, 3 de febrero de 2013, que es la fuente de la figura de tolerancia a fallas de la sección 7.

Empecemos con un ejemplo: un sistema de información financiera. Una institución que compra y vende acciones —lo que en la jerga del mercado se llama un *broker*— quiere acceder a la información del NASDAQ: precios, transacciones, todo el flujo que se mueve mientras el mercado está abierto. Vamos a llamarla «el banco», porque *broker* va a aparecer en esta clase con otro significado preciso y no queremos superponer sentidos.

Con lo que sabemos hasta aquí, la solución es clara. El NASDAQ expone un endpoint, un RPC, y el banco lo llama: ¿cuánto vale la acción de Google en este momento? Recibe el valor y sigue con lo suyo. Pero ese valor cambia todo el tiempo, y el banco no quiere una foto sino la serie, para ir armando el gráfico del precio. Por eso esa llamada se acompaña en el dibujo de un reloj: el banco hace polling, vuelve a preguntar periódicamente por todas las acciones. Eso funciona, y muchos sistemas funcionan exactamente así.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    comunicación directa — rectángulos NASDAQ y BANCO unidos por un arco rotulado &quot;RPC&quot; arriba y &quot;PERIÓDICO / POLLING&quot; abajo, con la flecha entrando al NASDAQ
    <span class="figura-ref">notas pág. 1 / pizarra pág. 1</span>
  </figcaption>
</figure>

Ahora los números, que muestran hasta dónde llega ese diseño. De lo que en el mercado se llama *símbolo* —el identificador de cada instrumento que cotiza— el NASDAQ tiene unos cinco mil setecientos: además de Google hay 5699 más. Y pasan entre sesenta y setenta millones de transacciones por día. Si el banco quiere información actualizada al segundo, tiene que consultar al NASDAQ constantemente, y no por un símbolo sino por los cinco mil setecientos.

{: .nota }
> Los dos números salen del Daily Market Summary de Nasdaq Trader, que es la fuente primaria y los publica juntos. En las últimas ruedas disponibles el volumen fue de 66 a 77 millones de operaciones diarias, así que el «entre sesenta y setenta millones» de la clase es correcto como orden de magnitud y queda apenas por debajo del rango actual. La cifra de símbolos merece una aclaración, porque hay tres conteos distintos y solo uno es comparable con el de operaciones: los valores **negociados** en un día son unos 5.700 —el que usamos aquí, porque sale del mismo reporte—, los **listados** en el Nasdaq Stock Market son unos 5.565, y los símbolos **negociados en el mercado Nasdaq** incluyendo los que cotizan en NYSE y en las bolsas regionales son más de 13.000. El reporte cuenta además las operaciones sobre valores listados en Nasdaq ejecutadas en cualquier venue, no las ejecutadas en el exchange de Nasdaq ni el total del mercado accionario estadounidense, que es bastante mayor.

Ahí aparece el dilema del polling, que no se resuelve eligiendo bien la frecuencia. Si el banco pregunta muy seguido, carga al NASDAQ con un tráfico enorme de consultas cuya respuesta casi siempre es que nada cambió. Si pregunta poco, pierde actualizaciones: entre dos consultas el precio pudo subir y bajar varias veces. Y ese tráfico se multiplica por cada banco del mundo que quiera lo mismo.

La cuenta de orden de magnitud dice hasta dónde llega el desperdicio. Un banco que consulta los cinco mil setecientos símbolos una vez por segundo hace 5.700 requests por segundo; cien bancos, 570.000. Del otro lado, setenta millones de transacciones por día repartidas en 24 horas dan unas ochocientas por segundo. Medio millón de requests por segundo para transportar ochocientas novedades: unos setecientos requests por novedad real. Y por banco: de los cinco mil setecientos símbolos que consulta cada segundo, a lo sumo ochocientos pueden haber cambiado, así que alrededor del 86 % de las respuestas le dicen que nada cambió.

El problema no es nuevo: existe desde que las computadoras se conectaron al sistema financiero, así que hay décadas de intentos de resolverlo.

Lo que se trató de hacer desde el principio es invertir el sentido de la flecha: en lugar de que el banco pregunte, que el NASDAQ avise cada vez que ocurre una transacción o cambia un precio. Eso es, en el fondo, lo que hacen los sistemas de mensajería. Pero hacerlo de forma directa tiene un obstáculo evidente: en el código del NASDAQ no puede estar hardcodeada la dirección de nuestro banco. Los bancos se agregan y se quitan con frecuencia, y no es razonable modificar el servidor cada vez que aparece un interesado.

Pongámosle nombre a los dos esquemas. Al del banco conectándose contra el NASDAQ lo llamamos comunicación directa. Al que vamos a construir ahora, comunicación indirecta, y es el término que organiza toda la clase.

En el medio ponemos una caja, un sistema intermedio. El NASDAQ ya no le manda nada a ningún banco: le manda todo a esa caja. Y los bancos —todos los que haya— se registran contra el intermediario con una operación que se suele llamar *subscribe*: decirle que se quiere empezar a escuchar actualizaciones de un cierto tipo. A partir de ahí, el intermediario les va mandando mensajes. Y «mensaje» no tiene exactamente el sentido que le dimos al hablar de protocolos en clases anteriores: estos son mensajes asincrónicos, que nadie pidió en ese instante.

La suscripción lleva un nombre que sigue alguna convención. Si al banco le interesan todas las acciones del NASDAQ, la llamada puede ser `subscribe("stocks.NASDAQ.*")`, del banco hacia la caja. Del otro lado, la flecha del NASDAQ a la caja es la operación complementaria, *push*, por donde entran los mensajes. Cada mensaje lleva también un nombre, específico: cuando la acción de Google pasa a valer cien, el NASDAQ hace `push("stocks.NASDAQ.GOOGL", 100)`.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    comunicación indirecta — NASDAQ → doble flecha &quot;CAMBIOS&quot; → MOM (rectángulo central) → BANCO1 / BANCO2 / BANCO3; del BANCO1 sale un arco &quot;SUBSCRIBE&quot; hacia el MOM y vuelve otro rotulado &quot;MSGS&quot;; a BANCO2 y BANCO3 llegan flechas &quot;MSG&quot;
    <span class="figura-ref">notas pág. 1 / pizarra pág. 1</span>
  </figcaption>
</figure>

Ahora sí la caja tiene nombre: es un MOM, *message-oriented middleware*. Si el sistema está literalmente en el medio, la palabra *middleware* se sugiere sola. Su razón de ser cabe en una línea: un MOM es una especie de distribuidor de mensajes. El nombre está muy en desuso, pero es el que identifica históricamente a esta familia de sistemas.

El ejemplo se parece bastante a un sistema real: TIBCO, un middleware nacido a fines de los ochenta que fue el estándar de hecho de la mensajería financiera durante los noventa. Usaba una convención de nombres para los canales —de ahí sale el `stocks.NASDAQ.*`— y permitía wildcards para escuchar a la vez todos los canales que coincidían con un patrón. Por debajo, originalmente, no usaba TCP sino UDP: poco común hoy, pero razonable en un sistema cuyo trabajo era mandarle el mismo dato a mucha gente a la vez.

{: .nota }
> El producto es TIBCO Rendezvous, descendiente del TIB —The Information Bus—, desarrollado por Teknekron Software Systems a partir de 1986; el primer TIB en producción fue el de Fidelity en 1987, justamente para distribuir market data. La empresa TIBCO Software Inc. («The Information Bus Company») se funda en 1997. El mecanismo de nombres es tal cual se describe aquí: en Rendezvous los canales se llaman subjects, sus elementos se separan con puntos formando una jerarquía, y hay dos wildcards —`*` coincide con un elemento y `>` coincide con uno o más elementos finales—. Sobre el transporte, la evolución es más precisa que «usaba UDP»: arrancó con UDP broadcast y después migró a IP multicast, siempre con una capa propietaria de confiabilidad por encima.

Esta materia estuvo mucho tiempo orientada a este tipo de sistemas: hubo una época en que cursarla era básicamente estudiar MOMs, y el programa oficial todavía tiene muchas referencias a ellos. La terminología hoy se usa poquísimo; el concepto se sigue usando, solo que con otro nombre.

A la estructura que acabamos de dibujar —un servicio que le manda todo a una entidad central que lo distribuye a muchos interesados— se la llama *publisher-subscriber*, y lo que la caracteriza es justamente repartir a muchos. Más adelante la vamos a clasificar mejor y vamos a ver que no siempre es lo que queremos. Pero aquí es justo lo que buscábamos: que el NASDAQ distribuyera su información a cualquiera interesado en ella.

El ejemplo es típico de los noventa, cuando los MOMs se usaban mucho para integrar sistemas distintos, y la información financiera es el caso clásico. Recapitulemos la historia. En los ochenta los sistemas distribuidos estaban dominados por los RPCs. En los noventa aparecieron los MOMs, y con ellos se puso de moda la palabra *middleware* —inventada en 1968, pero que en los noventa se convirtió en un término comercial: todo se vendía como middleware de algo.

{: .nota }
> El 1968 se verifica en la fuente primaria. La palabra aparece en Peter Naur y Brian Randell (eds.), «Software Engineering: Report on a Conference sponsored by the NATO Science Committee», Garmisch, octubre de 1968, p. 23, en una intervención de Alex d'Agapeyeff, rotulando una capa de su «pirámide invertida»: control programs, service routines, middleware, application programs. Su middleware no es el nuestro: d'Agapeyeff llamaba así a la capa que había que reescribir a mano porque el software del fabricante «no servía, o era ineficiente o era inapropiado». La palabra es de 1968; el concepto de middleware distribuido, no.

En los dos mil esa terminología desapareció; se pusieron de moda los *application servers* y SOA, *service-oriented architecture*. Y en los dos mil diez apareció un término más familiar: microservicio.

De esa lista, lo único que tratamos con seriedad en la materia es el RPC, porque es una técnica que se usa muchísimo. Lo demás son términos de marketing sin demasiado interés técnico. Incluso microservicio, que hay que saber usar para comunicarse con otros profesionales: que un servicio sea micro o macro es ambiguo, no hay forma de decir dónde deja de ser micro. Lo que nos importa son las técnicas de abajo, no las etiquetas.

Hecho el descargo, corresponde decir lo otro: la idea del MOM se sigue usando muchísimo y es sumamente útil. Los sistemas de mensajería actuales son, junto con la base de datos, el primer recurso de quien empieza a armar un sistema distribuido. Es poco probable que a alguno de nosotros le toque implementar algo parecido a DynamoDB; es mucho más probable que use lo que vamos a ver hoy para resolver problemas concretos. Y el resto de la clase está armado alrededor de eso: ejemplos prácticos de cómo se usan estos sistemas para construir cosas más sofisticadas.

---
