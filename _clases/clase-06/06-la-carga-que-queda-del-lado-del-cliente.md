---
title: "6. La carga que queda del lado del cliente"
parent: "Clase 6 — Raft II"
nav_order: 6
---

# 6. La carga que queda del lado del cliente

Queda una dificultad que conviene abordar de frente: la comparación que determina quién puede ser líder —el término de la última entrada y, si los términos coinciden, la longitud del log— no verifica en ningún momento si esas entradas estaban comiteadas. El caso que dispara la objeción es el de D en el ejemplo extenso, con sus dos entradas del término 7 al final: si D es elegido líder, esos dos 7 quedan comiteados en todo el cluster sin que ningún nodo haya verificado nada. Es una buena pregunta, y hay que conceder que la condición resulta contraintuitiva.

La respuesta breve es que funciona porque está demostrado que funciona. Pero para que deje de resultar chocante hay que cambiar de perspectiva y analizarlo desde el punto de vista del usuario.

Volvamos a las dos últimas entradas de D. Si D gana, ese 7 se va a propagar a todos los nodos y va a quedar comiteado. Pero cuando el usuario envió esas dos entradas nunca se le respondió que estuvieran comiteadas: no sabe qué ocurrió con ellas, y justamente por eso pudieron haber ocurrido las dos cosas. El mensaje de confirmación no nos llegó, o bien porque no se comiteó, o bien porque se comiteó y el mensaje se perdió en la red.

Desde el punto de vista del usuario la situación es difícil, porque debe adoptar alguna estrategia para evitar duplicados. Con una operación que no recibió respuesta, lo mejor que puede hacer es reintentarla; pero entonces tienen que ser operaciones que no produzcan efectos indeseados. Si se trata de una transacción bancaria y la operación consiste en acreditar dinero en una cuenta, no es tan simple como enviarla repetidamente hasta que quede registrada: que no responda puede significar que las operaciones están ingresando, o que ingresaron, el sistema falló, y cuando se restauró se terminaron de aplicar todas al final.

Para estos casos hay que generar las condiciones para tener una semántica de *exactly once*, algo que ya habíamos discutido antes en la materia. El cliente, cuando envía la operación a la capa de aplicación, debe agregarle algún ID de idempotencia, de manera que la aplicación pueda desduplicarlas y no aplicarlas varias veces a la base de datos. Y allí está el reparto de responsabilidades que conviene retener: eso ya no es competencia de Raft sino de la aplicación, y eliminar los duplicados es trabajo de la capa superior.

La objeción es legítima, y resulta chocante por ese mismo motivo: al no recibir respuesta, el cliente no sabe qué ocurrió. Raft está diseñado así porque funciona de las dos formas. Y esto va a ser importante para el trabajo práctico: implementar un simple retry contra una base de datos probablemente no funcione.

De allí surge un criterio de diseño de los sistemas reales. Dynamo sería uno de esos casos, y en general muchos key-value stores tienen todas sus operaciones idempotentes, justamente por este motivo. Por eso no suelen ofrecer una operación de `increment`, que no es idempotente: si se aplica varias veces, incrementa varias veces. En cambio una operación de `set` sí lo es: si se envía varias veces `set x = 5`, se aplica varias veces sin consecuencias. Hay que ser cuidadoso, entonces, al diseñar la aplicación para estos escenarios.
