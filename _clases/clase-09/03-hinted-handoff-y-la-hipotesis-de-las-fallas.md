---
title: "3. Hinted handoff y la hipótesis de las fallas temporales"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 3
---

# 3. Hinted handoff y la hipótesis de las fallas temporales

Dynamo tiene varios métodos para recuperarse de esas situaciones. No son exactamente parches, sino mecanismos que se le fueron incorporando para que el sistema se vaya arreglando solo con el tiempo. El primero atiende justamente el caso que acabamos de ver: la escritura que no completó el quórum donde correspondía.

En el ejemplo, teníamos que escribir en S1, S2 y S3, y S3 está caído. Escribimos en S1 y S2, y el dato se lo mandamos a S4. Pero a S4 no le mandamos solamente la clave y el valor: en el mismo mensaje le mandamos también S3. El mensaje le indica algo preciso: ese dato no le corresponde a S4, que debe conservarlo disponible por si alguien lo solicita y entregarlo a S3 en cuanto sea posible. Ese dato adjunto, el nombre del destinatario que no pudo recibirlo, es el *hint*, y el mecanismo se llama **hinted handoff**.

<figure class="figura figura-con-imagen">
  <img src="{{ '/assets/clase-09/hinted-handoff.png' | relative_url }}" alt="El hinted handoff de S2 a S4, con el hint S3">
  <figcaption>
    <span class="figura-label">Figura</span>
    el hinted handoff — la preference list S1, S2, S3 encerrada en un óvalo; el coordinador S2 replica en S1, S3 está tachado, y un arco largo lleva a S4 el par (k, v) junto con el hint S3; una flecha de vuelta de S4 a S3 entrega el dato cuando S3 revive
    <span class="figura-ref">pizarra pág. 2 / notas pág. 1</span>
  </figcaption>
</figure>

S4 va a monitorear de vez en cuando a S3 para ver si se recupera, o solo para ver si es alcanzable desde S4: quizás S3 nunca estuvo caído, sino que los otros dos no llegaban hasta él, y S4 sí puede. Cuando S3 vuelve a estar disponible, S4 le manda la clave y el valor pendientes. El dato termina en S3, donde correspondía desde el principio; todo se restaura solo.

Nada de esto se parece a los algoritmos sofisticados que vimos antes, como Raft: es un mecanismo pragmático para que los datos, aunque no se hayan escrito donde correspondía, eventualmente se restauren.

La entrega tiene un detalle. Cuando S4 le escribe a S3 se aplican los criterios de siempre para ver si el valor que llega es más actualizado que el que S3 ya tiene. Quizás S3 se recuperó hace tiempo y alguien le escribió un valor todavía más reciente; en ese caso rechaza lo que le manda S4. Si no, lo acepta.

Todo el mecanismo se apoya en una idea sobre cómo fallan estos sistemas. Más que una teoría es una hipótesis, sin definición matemática detrás: la mayoría de las fallas son temporales. El caso típico es un router que empieza a rechazar paquetes pero eventualmente se restaura solo, y el servidor aparece de vuelta. Se cayó unos segundos, o unos minutos, y volvió.

Lo que la hipótesis dice, sobre todo, es lo que la falla no es: no es un servidor que se quemó. Cuando imaginamos fallas en sistemas distribuidos imaginamos casos que no son tan comunes como uno pensaría: que se dañó el disco o la computadora, o que un desastre natural destruyó el data center entero. Esos eventos catastróficos no son tan frecuentes. Mucho más frecuentes son los problemas temporales: que se sature la máquina y no pueda aceptar más requests, que su base de datos esté llena, y entonces los requests den timeout hasta que eso se restaure solo y la máquina vuelva a aceptar mensajes.

De ahí sale la decisión de diseño. Disparar el reemplazo completo de la máquina ante una pequeña latencia no tendría sentido. La apuesta es la contraria: si algo falló, primero asumimos que la máquina va a volver, le mandamos el dato a un compañero, y ese compañero eventualmente se lo devuelve.

---
