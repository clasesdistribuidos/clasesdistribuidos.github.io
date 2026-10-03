---
title: "8. El modelo de cobro"
parent: "Clase 9 — Dynamo II y DynamoDB"
nav_order: 8
---

# 8. El modelo de cobro

El modelo de cobro es casi un descanso en la teoría dura, y sin embargo es la parte con la que uno más va a tratar: en la práctica profesional uno interactúa con proveedores de cloud mucho más de lo que arma servicios como estos. Cuando algo falla o se comporta de manera anómala, la teoría sirve para intuir qué puede estar mal —problemas de consistencia, por ejemplo—, pero en el día a día lo que preocupa es cómo escalan los servicios y cuánto cobran.

La característica principal se entiende otra vez por contraste. Antes uno compraba una máquina física y la instalaba en algún lado: una inversión toda al principio, con la cuenta de en cuánto tiempo se recupera, la amortización a lo largo de los años, y la decisión de cuánta capacidad de más comprar para no quedarse corto. En un servicio cloud eso desaparece: se cobra como la luz o el gas, por uso. Es un principio fundamental que en el sentido amplio nunca falla: si uno usa menos, paga menos; si usa más, paga más. Las variaciones están en el detalle, y tres ejemplos muestran lo distintas que resultan.

El primero son las máquinas virtuales. En Google Cloud, por ejemplo, se cobra la hora de uso: si uno deja una máquina funcionando tres horas, la factura dice tres horas multiplicadas por el precio de la hora.

El segundo es un CDN, un *content delivery network*: una red de servidores caché distribuidos por el mundo, que sirven imágenes y páginas web desde un lugar cercano a quien las pide, lo que acelera mucho las descargas. Si todo tuviera que llegar al servidor central, que bien puede estar en Estados Unidos, sería muy lento. Los cachés se conectan solos con el servidor original, que les manda el contenido, y uno accede a esa copia cercana. El ejemplo familiar es Netflix: cuando lo vemos, el tráfico no va hasta Estados Unidos sino a algún servidor cercano, en la zona de Buenos Aires. Un CDN cobra por tráfico. Lo llamativo es que el modelo es completamente distinto del anterior: uno cobra por hora, el otro por tráfico. Y en ninguno hay un pago inicial para recién después poder usar el servicio.

El tercero es DynamoDB, una base de datos, que combina dos dimensiones: storage y requests por segundo. Cobra más cuanto más espacio se usa y cuantas más queries se hacen. La cuenta es más complicada, pero la idea es la misma: cuanto más se usa, más se cobra. Y si casi no se usa, quizás haya algunos costos fijos, pero la factura no aumenta.

Esto tiene una consecuencia arquitectónica, y es lo más interesante. El usuario se conecta en abstracto con el servicio cloud y lo usa. Pero internamente estas empresas tuvieron que inventar otros servicios para que el cobro por uso sea posible. El servicio cloud le manda datos a un servicio que suele llamarse *metering*, el equivalente del medidor de gas de una casa: le va mandando las métricas de uso de cada usuario. En Dynamo, donde se cobran requests por segundo, le reporta cada cierto tiempo cuántos requests hizo cada usuario. El metering agrega todos esos datos y se los pasa al servicio de *billing*, que los combina con los precios, hace todas las complicaciones contables, y el resultado vuelve al usuario: la factura, que después hay que pagar.

<figure class="figura">
  <figcaption>
    <span class="figura-label">Figura</span>
    el circuito del cobro — el usuario y el servicio cloud arriba, con una flecha de doble punta entre ellos; del servicio baja una flecha al metering, del metering una flecha horizontal al billing, y del billing sube al usuario la flecha de la factura, rotulada con el signo $
    <span class="figura-ref">notas pág. 6 / pizarra pág. 6</span>
  </figcaption>
</figure>

Los servicios cloud tuvieron que resolver una parte que uno no imaginaría: si esto se va a vender, hay que poder medirlo y cobrarlo.

---
