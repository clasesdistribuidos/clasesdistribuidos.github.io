---
title: "3. Qué significa que un log esté más actualizado"
parent: "Clase 6 — Raft II"
nav_order: 3
---

# 3. Qué significa que un log esté más actualizado
{: .no_toc }

<details open markdown="block">
  <summary>En esta sección</summary>
  {: .text-delta }
- TOC
{:toc}
</details>


Quedaron dos deudas explícitas en la primera sección: dijimos que para votar a un candidato hay que verificar que su log esté más actualizado que el propio, y las dos veces aclaramos que la definición precisa vendría después. La noción que veníamos utilizando de manera informal ahora se enuncia con precisión, y después la vamos a aplicar sobre el ejemplo más complejo que trae el paper.

## La election restriction

La restricción tiene nombre propio, *election restriction*, y consiste en dos condiciones que se aplican en un orden que resulta significativo.

La primera: el término de la última entrada del log del candidato tiene que ser mayor que el término de la última entrada de mi log. Mayor, o más precisamente mayor o igual, porque si es igual todavía queda algo por decidir. La segunda condición resuelve ese caso: si los dos estamos en el mismo término, gana el log más largo, o de igual longitud.

Enunciado así, de manera escueta, confunde más de lo que aclara. Veamos un ejemplo de tres servidores, sin índices porque no son relevantes: lo único que importa son los términos. S1 tiene tres entradas, de los términos 5, 6 y 7; S2 tiene dos, de los términos 5 y 8; S3 tiene lo mismo que S2. El contraste es lo que interesa: S1 es el más largo, pero su última entrada es del término 7; los otros dos son más cortos, pero su última entrada es del 8.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-06/logs-567-y-58.png' | relative_url }}" alt="Logs 5 6 7, 5 8 y 5 8">
  <figcaption>
    <span class="figura-label">Figura</span>
    tabla de logs de S1, S2 y S3 con los términos `5 6 7` / `5 8` / `5 8`, sin índices
    <span class="figura-ref">notas pág. 3, fig. 1 / pizarra pág. 3, fig. 2</span>
  </figcaption>
</figure>

Supongamos que alguien era líder, que cayó, y que ahora los tres van a elegir uno nuevo. Si S2 se transforma en candidato, S1 responde afirmativamente porque el término 8 es mayor que el 7: primera condición, y con eso alcanza. Con S3 el 8 es igual al 8, así que la primera no decide nada; entra la segunda, y como los dos logs tienen la misma longitud —y con que sea igual alcanza—, S3 también responde afirmativamente. S2 puede ser elegido, y S3 también, porque está en la misma situación.

El que no va a poder es S1: los otros dos lo rechazan porque 7 es menor que 8. S1 nunca va a poder ser líder, a pesar de tener el log más largo de los tres.

Queda por ver cómo se llega a una situación así y por qué la regla tiene sentido. Al principio el sistema venía funcionando normalmente y S1 era el líder. En algún momento cae de manera repentina y se recupera de inmediato; al recuperarse recibe un request y lo coloca en su log, que es la entrada del término 6. Cae y se recupera nuevamente, se transforma otra vez en líder y coloca el 7. Por el momento no logró que nada progresara: esas dos entradas están solamente en él. Después cae otra vez, y alguno de los otros dos, no importa cuál, es elegido líder.

El razonamiento inmediato es equivocado, y vale la pena verlo caer. Podría pensarse que para que otro sea elegido, S1 tiene que permanecer caído un tiempo, porque de lo contrario se postularía y los otros dos lo rechazarían. Pero no hace falta: en un cluster de tres, con que lo vote uno solo ya alcanza. Uno lo rechaza, el otro lo vota, y con ese único voto ajeno se transforma en líder a pesar de que el otro esté en funcionamiento.

Y con eso ya estamos en el término ocho. ¿Cómo lo saben los nodos? Porque estuvieron intercambiando mensajes mientras votaban previamente, y esos mensajes les fueron informando el término.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-06/traza-cronologica.jpg' | relative_url }}" alt="Secuencia de fallas y elecciones que lleva a esos logs">
  <figcaption>
    <span class="figura-label">Figura</span>
    la traza cronológica de cómo se llega a esa tabla — S1 líder escribe el 6, falla, se recupera, vuelve a ser líder y escribe el 7, falla, y S2 es elegido líder en el término 8 con S3 actualizando su término; términos recuadrados, líneas verdes para &quot;líder/recuperación&quot; y rojas para &quot;falla&quot;
    <span class="figura-ref">notas pág. 3, fig. 2</span>
  </figcaption>
</figure>

¿Y qué implica esa situación? Que tenemos un 8 en dos lugares, y si un 8 está en dos lugares en un cluster de tres, ya está en mayoría. Puede ser que no se le haya avisado al cliente, pero de eso no tenemos ninguna garantía: puede ser que ese 8 haya sido comiteado, y si fue comiteado, no lo podemos eliminar.

Allí se advierte por qué el orden de las condiciones es el que es. Si la restricción fuera simplemente el log más largo, S1 podría transformarse en líder en este momento, y al hacerlo eliminaría esos dos 8 para colocar en su lugar un 6 y un 7. Lo grave es que eliminaría un 8 que ya estaba comiteado. Por eso primero va el término y después la longitud.

Queda una duda razonable: qué ocurre cuando hay dos candidatos esencialmente equivalentes, con el mismo término y todo lo demás igual; si el paper establece alguna prioridad, por ejemplo que gane el que envió primero. Lo importante no está allí, sino en que cualquiera puede ser candidato, que muchos son elegibles, que el resultado final del log va a ser diferente según cuál sea elegido, y que Raft va a seguir siendo correcto independientemente de quién gane, siempre que se respete la condición. Y la condición, enunciada desde la perspectiva del votante —que es como más conviene recordarla—, es esta: aquel a quien estoy votando no puede tener un término menor que el mío, y si los términos coinciden, no puedo tener yo el log más largo. Con esa condición todo funciona, y está demostrado.

## El ejemplo extenso del paper

Veamos ahora el ejemplo más extenso y complejo del paper: la figura 7. Un cluster de siete máquinas, lo cual es perfectamente válido. La máquina superior, el líder, cae, y quedamos con la configuración considerablemente enredada que el paper dibuja. Hay que analizarlo un buen rato para convencerse, pero se puede llegar a un desorden como ese.

Fijemos el estado, porque sin tenerlo presente nada de lo que sigue puede seguirse. Quedan seis máquinas y vamos a observar los índices 1 a 12. La que cayó tenía diez entradas: tres del término 1, dos del 4, dos del 5 y tres del 6. A tiene nueve: lo mismo, salvo que le falta la última, así que su última entrada es del término 6. B tiene cuatro: los tres 1 y un 4. C tiene once: todo lo de la máquina caída más una entrada adicional del término 6, cuatro 6 en total, con lo cual su última también es del 6. D tiene doce: hasta el índice 10 lo mismo que la caída, y después dos entradas del término 7. E tiene siete: tres 1 y cuatro 4. Y F, la inferior, tiene once, y son las que más se apartan del resto: tres 1, tres 2 y cinco 3, así que su última entrada es del término 3.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el estado inicial del ejemplo extenso — el cluster de siete con el líder caído arriba y los logs de A, B, C, D, E y F sobre los índices 1 a 12
    <span class="figura-ref">figura 7 del paper</span>
  </figcaption>
</figure>

La pregunta es cuál de esos seis podría ser elegido líder, y vamos a analizarlos uno por uno. Antes, la cuenta: con siete máquinas hacen falta cuatro votos, uno es el propio, así que tres máquinas lo tienen que votar a favor.

Empecemos por A. B vota a favor: su última entrada es del término 4 y la de A es del 6, así que la primera condición decide sin más trámite. Con C el caso se vuelve interesante, porque es la primera vez que la segunda condición interviene efectivamente. A primera vista parecería que también vota a favor, pero no: el término es el mismo, un 6 en los dos casos, y cuando coinciden vale el más largo. C tiene once entradas y A tiene nueve, así que lo rechaza. D también lo rechaza, y ese caso es directo: su última entrada es del término 7. E y F votan a favor, porque los dos tienen términos más antiguos. Tres votos ajenos: A podría ser líder.

¿Y qué ocurre cuando A se sincroniza con los demás? Por definición, todas sus entradas van a quedar comiteadas eventualmente. Pero también va a eliminar entradas: entradas de C, entradas de D, y todo lo de F, porque nada de eso coincide con su versión. Y aquí está el punto: ninguna de las que elimina estaba en un quórum, en una mayoría. En cambio no va a eliminar ninguno de los 4 ni ninguno de los 5, y para hacer bien esa cuenta hay que contar también a la máquina que cayó, porque su log existió. Eso significa que, en definitiva, no compromete nada.

La diferencia entre A y C es donde uno tropieza: parecen estar en la misma situación y no lo están. La condición se aplica primero una y después la otra. El votante vota a favor del candidato si este tiene un término mayor; pero si el término coincide, gana el que tiene el log más largo. Dicho a la inversa, que es como se aprecia mejor: mismo término, y si yo solicito el voto y el otro tiene el log más largo que el mío, va a rechazarme.

¿Y eso implica que uno tiene más entradas por comitear que el otro? Esa pregunta no tiene respuesta breve. La condición está demostrada matemáticamente y habría que analizarla con cuidado; lo que sí se puede afirmar es que, si se respeta, el que resulta elegido líder no puede eliminar nada que esté comiteado. La razón se advierte mejor por el absurdo, observando a F: tiene entradas del término 2 y del término 3 que aparecen solamente allí, en ningún otro lugar. Si la condición fuera solamente la longitud, F —con sus once entradas— se convertiría en líder y produciría un resultado catastrófico, eliminando todo lo que ya estaba comiteado.

Hay que admitir que demostrarlo cuesta: en algunos casos votan a favor y en otros en contra, y el resultado no se aprecia de un solo vistazo. Pero hay algo muy importante que extraer de la figura: no hay un único resultado posible, no hay un único líder posible. Varios pueden ser elegidos, y según quién sea, algunas entradas se eliminan y otras no. La garantía es que nunca se va a eliminar algo que ya había sido escrito en una mayoría; pero también se pueden escribir entradas que estaban en un solo lugar.

El caso de D lo muestra con claridad. La máquina de los 7 también puede ser elegida, y de hecho la vota todo el cluster sin excepción, porque su término es el mayor de la figura. Si D gana, va a reescribir buena parte del cluster: a una le coloca un 6 y un 7; a otra le elimina una entrada y le coloca un 7 y después otro 7; y a la inferior le elimina todo y le coloca la secuencia completa. Algunas máquinas que parecerían no poder ser líder pueden serlo y modificar todo lo demás. Y sin embargo, si se revisa todo lo que D escribió, en ningún lugar eliminó algo comiteado.

Observemos el mismo diagrama desde otro ángulo y preguntémonos cuáles entradas estaban comiteadas. Las tres primeras, las del término 1, están en todos los nodos. El 4 está en muchos lugares. Los dos 5 están en cinco máquinas. Y los dos 6 también alcanzan mayoría, y para esa cuenta hay que contar a la máquina que cayó. De los índices 1 a 9, entonces, todo está comiteado, y esas son las entradas que no podrían eliminarse nunca. Del índice 10 en adelante ya no hay garantía alguna.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el mismo ejemplo con la línea que marca las entradas comiteadas — los índices 1 a 9, contando el log de la máquina caída para la cuenta de mayorías; del 10 en adelante, sin garantía
    <span class="figura-ref">figura 7 del paper</span>
  </figcaption>
</figure>

Cualquiera que resulte elegido líder y modifique los otros logs nunca va a poder tocar esas entradas marcadas. Y a la inversa, que es la otra mitad de la observación: a pesar de estar comiteadas, hay servidores que no las tenían, así que se elija a quien se elija esas posiciones van a tener que ser reescritas con los valores correctos: donde falta un 4 habrá que colocar un 4, y donde faltan los 5, los 5. Eso es lo notable de la matemática que sustenta todo esto: lo que ya estaba comiteado va a permanecer comiteado independientemente de quién resulte elegido.

Para terminar, el resto de los candidatos. B va a perder en todos los casos: A, C y D lo rechazan, y E también, porque con el mismo término 4 en la última entrada E es más larga. El único que vota a favor es F, y dos votos contando el propio no alcanzan. E tampoco lo consigue: B y F votan a favor, pero A, C y D lo rechazan. Y F, evidentemente, tampoco, porque está muy desactualizada: ningún nodo la vota.

De modo que los posibles líderes son A, C y D, y los tres coinciden en tener por lo menos las entradas comiteadas que marcamos antes. Esa es una propiedad importante del algoritmo, y esa figura merece analizarse con detenimiento.

## Cuándo repara el líder los logs ajenos

Sobre ese mismo ejemplo quedaron algunas preguntas pendientes, y conviene atenderlas porque abordan un caso que la sección anterior no cubrió.

La primera: si A es elegido líder, ¿cuándo sincroniza su log? Repasemos qué elimina: a C el 6 que le sobra, a D sus dos 7, y a F todas las entradas divergentes. Las elimina con seguridad, porque ninguna estaba comiteada: para estarlo tiene que estar en cuatro máquinas. El 6 del índice 10 está en tres —contando a la caída, y conviene insistir en que se la cuenta, porque el sistema sigue funcionando con una máquina caída pero su log existió—, y tres no alcanzaba. Los 7 de D y las divergentes de F aparecen en un solo lugar, así que se pueden eliminar sin consecuencias.

Pero la pregunta puntual era otra: ¿eso lo elimina apenas es elegido líder, o cuando le van llegando entradas nuevas? Lo segundo. Apenas es elegido no elimina nada. Cuando le van llegando entradas nuevas e intenta hacer `AppendEntries`, los followers van a responderle que no pueden aceptarlas porque están desactualizados, y allí es donde empieza a retroceder en cada uno de esos logs, de a una entrada por vez, y eventualmente les envía todo junto.

Observemos el intercambio concreto. Apenas eligen a A, A intenta enviarles entradas a C y a D. Hay que prestar atención al término: si eligen a A, ya vamos a estar en el término ocho, porque para postularse tuvo que incrementarlo. Así que lo que envía es una entrada nueva del término 8, con `prevLogIndex` 9 y `prevLogTerm` 6, que son el índice y el término de su última entrada.

Y aquí aparece algo que no habíamos visto antes, y que es la parte más valiosa del recorrido. El razonamiento que uno hace en primera instancia es que C va a rechazarlo, porque el índice 9 no es el índice 11: el líder apunta a una posición que en C no es la última, C está más adelantado, y por lo tanto tendrían que retroceder. Da la impresión, por un momento, de que Raft no funciona en este caso. Pero no hay nada que retroceder: C advierte que en la posición 9 tiene efectivamente un 6 y que lo que tiene de más viene después de ese punto. Hasta el índice 9 la coincidencia es perfecta, así que puede aceptar la entrada directamente y restaurarse por sí solo. Lo único que necesita verificar es lo que está antes de la entrada nueva, y eso es correcto.

La regla, enunciada de una vez, es esta. Se rechaza al líder cuando el líder tiene que enviarle más entradas. Pero si el log tiene entradas de más, se trunca la cola de ese log y se acepta la entrada nueva directamente. En el índice 9 hay un 6, que es exactamente lo que el líder indicaba, así que la entrada del término 8 se coloca en el índice 10. ¿Y los dos 6 que sobraban al final? Se eliminan, y eso es correcto: si elegimos a A como líder, de una forma u otra esas entradas se iban a perder, porque la sincronización avanza en esa dirección.

Hay dos operaciones que resulta fácil confundir, porque uno tiende a imaginar que el follower va sobrescribiendo a medida que le llega cada paquete. Truncar la cola es directo: el follower advierte que coincide en el punto que el líder le señaló, descarta lo que tiene después y escribe lo nuevo, todo en un solo paso. Rebobinar hacia atrás es la otra operación, y esa sí avanza de a una entrada por vez.

Los otros dos followers son casos de rebobinado propiamente dicho. Empecemos por F, el más evidente porque es el más divergente. El líder le indica índice 9, término 6, y F lo rechaza; índice 8: rechazo; índice 7: rechazo; índice 6: rechazo; índice 5: rechazo; índice 4 tampoco, porque allí F tiene una entrada del término 2. Y recién con índice 3, término 1, lo acepta: esas tres primeras entradas son las únicas que ambos comparten. Entonces le envía todo junto y se sincronizan. Tiene que avanzar hacia atrás, de a una entrada por vez, pero cuando llega al punto de coincidencia el bloque completo viaja en el mismo mensaje: el 4, el 5, el 6 y todo lo que sigue de una sola vez. Y las entradas que F tenía más adelante las elimina directamente.

Con E ocurre algo similar, aunque el recorrido es más corto: lo va rechazando y va eliminando lo que le sobra, hasta que llega al índice 5 con término 4, donde los dos logs coinciden. Allí E elimina el resto y escribe la secuencia correcta, los 5 y los 6 que le faltaban.

Sobre este resultado hay una objeción que conviene tomar en serio, aunque no tenga respuesta cerrada. Resulta llamativo que se pierdan entradas de los servidores más adelantados: si se eligiera líder a uno de esos, prácticamente no se perderían datos y se reduciría la tasa de pérdida a largo plazo. La respuesta rigurosa es que eso no es verificable formulado de ese modo, que habría que demostrarlo. Pero sí se puede señalar qué ocurriría: se van a comitear entradas que nunca se le habían confirmado al cliente, porque esos 6 que estaban en tres máquinas nunca se le pudieron confirmar.

Y como todo se conecta con todo, este ejemplo se cierra sobre el primero de la clase. Supongamos que caen varias de las máquinas que tenían la información correcta y queda una sola con el log actualizado —y log actualizado significa, por definición, el que tiene lo que estaba comiteado—. La única opción es que esa sea elegida líder. Se asemeja al primer esquema del comienzo de la clase, el de la partición donde un solo nodo del lado mayor tenía la entrada comiteada: los demás nunca van a poder ser elegidos, porque él los va a rechazar a todos. Allí el algoritmo se ajusta por sí solo para que únicamente quien tiene las entradas comiteadas pueda ser líder.

Y si cae también esa máquina, la última que tenía el log completo, entonces ya no va a elegirse ningún líder, porque se supera el límite de la mayoría: quedan tres máquinas en funcionamiento y necesitamos por lo menos cuatro para poder seguir avanzando. En ese punto el sistema queda bloqueado, sin líder. Y eso es lo importante: no se trata de que se elija un líder que elimine entradas comiteadas, sino de que no se elige ninguno.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    la asimetría del truncado sobre el ejemplo extenso — arriba, C aceptando en el índice 10 la entrada del término 8 con `prevLogIndex` 9 y `prevLogTerm` 6 y truncando en un solo paso los dos 6 que le sobraban; abajo, F rechazando índice por índice hasta el punto de coincidencia y recibiendo después el bloque completo
    <span class="figura-ref">figura 7 del paper</span>
  </figcaption>
</figure>

Todo esto se asemeja a un rompecabezas donde Raft siempre tiene razón, porque está demostrado matemáticamente que el sistema va a funcionar. Uno de todos modos continúa analizando casos, para ver qué ocurre en una u otra situación, y el sistema se restaura por sí solo siempre, si está correctamente programado. Queda la asimetría del truncado: hacia adelante se trunca directamente, en un solo paso; hacia atrás hay que avanzar de a una entrada por vez, con las optimizaciones que ya discutimos.

---
