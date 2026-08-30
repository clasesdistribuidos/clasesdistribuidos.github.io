---
name: recortar-figuras
description: >-
  Recorta las figuras de una clase de la pizarra y las notas del profesor, y
  reemplaza los placeholders punteados de `_clases/clase-NN/` por las imágenes.
  Usar después de partir el apunte con la skill `nueva-clase`, cuando las
  páginas ya están y lo que falta son los dibujos. No cubre la escritura ni el
  partido del apunte.
---

# Recortar las figuras de una clase

Las figuras no se dibujan de nuevo: se recortan de lo que el profesor usó en
clase. `scripts/recortar_figuras.py` es a la vez la herramienta y el registro:
tiene una tabla por clase con una caja por figura, y `--clase N` regenera
`assets/clase-NN/` entero. Es idempotente, así que corregir una caja es editar
un número y volver a correrlo.

**Avisar al empezar:** "Voy a usar la skill recortar-figuras."

## Las dos fuentes

Las dos viven en el repo de trabajo `clases-apuntes`, en `raw/claseN/`. Dónde
está clonado es cosa de cada máquina: el script lo busca al lado de este repo y
si no está se le pasa con `--apuntes`.

- **La pizarra virtual** (`pizarra.pdf`), que dibujó en vivo. Es la fuente
  preferida: son trazos vectoriales y se rinden nítidos a cualquier resolución.
  Intercala hojas dibujadas a mano con capturas del libro, fotos y recortes.
- **Los scans de las notas** (`notas/pagina-NN.jpg`), que preparó antes de la
  clase. Papel, más sucios y de menos resolución. Se usan solo cuando la pizarra
  no sirve: porque esa página quedó sin dibujo, o porque el dibujo quedó
  apretado contra otra cosa y es ilegible.

Cuando se elige notas sobre pizarra, **dejar un comentario en el script diciendo
por qué**. En la clase 1 pasó dos veces y las dos están anotadas; en la clase 3
no pasó ninguna.

## Antes de tocar nada

1. **Contar los placeholders.** Es el número exacto de figuras que la tabla
   tiene que tener, y el script no lo verifica por su cuenta:

   ```sh
   grep -c '<figure class="figura">' _clases/clase-NN/*.md
   ```

   Los `figura-codigo` son otra cosa y no se cuentan acá.

2. **Leer el mapeo, no adivinarlo.** El `<span class="figura-ref">` de cada
   placeholder ya dice de qué página sale esa figura; está escrito desde que se
   transcribió el apunte. Conviene volcarlo en orden de lectura, porque ese es
   el orden en que después hay que insertar las imágenes.

3. **Confirmar de qué clase del repo de apuntes sale.** Las dos numeraciones se
   separaron: la del repo cuenta grabaciones y la del sitio cuenta clases
   publicadas. La clase 3 del sitio se grabó como la 4. Si no coinciden, va en
   `FUENTE_POR_CLASE` del script —para que `--clase N` a secas siga dando lo
   mismo— y no en un `--fuente` suelto que después nadie recuerda.

   La señal de que se erró de directorio es que falte `notas/` o que la cantidad
   de páginas no llegue a la que piden las referencias.

## Sacar las cajas

4. **De un render con grilla**, no a ojo ni a fuerza de iterar:

   ```sh
   python3 scripts/recortar_figuras.py --clase N --grilla
   ```

   Vuelca en un directorio temporal cada página de la pizarra y de las notas con
   una grilla rotulada **en el mismo espacio en el que se escriben las cajas**.
   Se miran esas imágenes y se leen las cajas directamente de la grilla.

5. **Mirar la página entera antes de cortar.** Una página de pizarra suele tener
   varias figuras —la 3 de la clase 3 tiene cuatro— y además texto que no es
   parte de ninguna.

6. **Llenar la tabla.** Las cajas de la pizarra van en coordenadas de 150 dpi
   (1241x1754); el script rinde a 300 y las escala solo. Las de los scans van en
   las coordenadas nativas del jpg. La caja no necesita ser precisa: el script la
   ciñe al contenido real y le deja un margen parejo. Lo que sí importa es que no
   entre contenido ajeno.

7. **Sacarse de encima el texto vecino.** Hay dos formas y conviene la primera:

   - **Correr el borde de la caja**, cuando el título y la figura no se pisan.
     En la clase 3, "RSM" y su subrayado terminan en x=145 y la secuencia
     `O₁ O₂ O₃ O₄` recién arranca en 165: alcanzó con empezar la caja en 155.
   - **Taparlo con `borrar`**, cuando sí se pisan: rectángulos blancos, en las
     mismas coordenadas que las cajas. Son para títulos que el apunte ya dice
     con palabras, separadores entre secciones de la pizarra y restos de la
     figura de al lado.

   Si hay que decidir si una anotación del costado entra o no, mandar la
   descripción del placeholder: cuando dice "al costado, master/slaves y
   writer/read-replica", esas etiquetas son parte de la figura.

## Revisar

8. **Hoja de contactos, y mirarla de una.** Recorte por recorte los errores se
   pasan por alto:

   ```sh
   python3 scripts/hoja_de_contactos.py --clase N
   ```

   Lo que salta ahí: el recorte que se llevó algo de al lado, el que cortó una
   etiqueta por el borde, y el que se comió un elemento entero de la figura. En
   la clase 3 aparecieron tres —a uno le faltaba un consumidor completo, a otro
   le cortaba "WEB SERVERS" por la izquierda, a un tercero le sobraba un resto
   del título—. Los subíndices son los que más se cortan: un `S₀` al que le
   falta el `₀` no se nota en miniatura, así que **abrir a tamaño completo los
   recortes que tengan texto contra el borde**.

9. **Verificar que las clases viejas no se movieron.** Cualquier cambio al
   script tiene que dejar los mismos bytes:

   ```sh
   python3 scripts/recortar_figuras.py --clase 1 && python3 scripts/recortar_figuras.py --clase 2
   git status --porcelain assets/     # tiene que salir vacío
   ```

## Meter las imágenes en las páginas

10. **Reemplazar cada placeholder**, en orden de lectura. El `<img>` va adentro
    del `<figure>`, antes del pie, y el `<figure>` suma la clase
    `figura-con-imagen`:

    ```html
    <figure class="figura figura-con-imagen">
      <img src="{{ '/assets/clase-03/el-log.png' | relative_url }}" alt="El log como fila de celdas que crece hacia la derecha">
      <figcaption>
        <span class="figura-label">Figura</span>
        el log como fila de celdas que crece hacia la derecha, con las tres propiedades: operaciones más orden, append-only y totalmente ordenado
        <span class="figura-ref">pizarra pág. 4 / notas pág. 3</span>
      </figcaption>
    </figure>
    ```

    **La descripción y la referencia se quedan como están.** La primera es el
    pie; la segunda dice de dónde salió el dibujo, y sigue nombrando las dos
    fuentes aunque el recorte haya salido de una sola. El `alt` va corto: el pie
    ya describe la figura en detalle y está ahí al lado.

11. **Verificar antes de mostrarlo:**

    ```sh
    grep -rn '<figure class="figura">' _clases/clase-NN/   # no tiene que quedar ninguno
    grep -rc 'figura-codigo' _clases/clase-NN/*.md         # los de código, intactos
    bundle exec jekyll build
    ```

    Y que cada `<img>` apunte a un archivo que existe y que no haya recortes
    huérfanos: la lista de rutas referenciadas tiene que coincidir exactamente
    con la de `assets/clase-NN/`.

## Los formatos los decide el script

El criterio: los trazos de la pizarra se ensucian en jpeg, así que van en png;
las fotos y los scans pesan mucho menos en jpeg y la diferencia no se ve. Ancho
máximo 1400 px, bastante más que la columna del theme, para que se vean bien en
pantallas densas.

Hay dos escapes para cuando el criterio automático se equivoca, y los dos son
conjuntos de `(clase, nombre)`:

- `FOTOS`, para lo que es foto aunque salga de la pizarra y el peso no alcance
  para distinguirlo.
- `TRAZOS`, para lo que es puro trazo y se pasa del umbral de peso, que si no
  terminaría en jpeg.

## Lo que no hay que hacer

- **No dibujar figuras.** Ni SVG, ni ASCII, ni mermaid. Si el dibujo no está en
  ninguna de las dos fuentes, el placeholder se queda como está.
- **No tocar la prosa.** El trabajo acá es de imágenes. Si algo del texto parece
  un error, señalarlo, no corregirlo.
- **No editar los recortes a mano.** Todo lo que hace falta se expresa como caja
  y `borrar` en la tabla, y por eso volver a correr una clase da lo mismo. Un
  retoque a mano se pierde en el siguiente `--clase N`.
- **No inventar las cajas a ojo** ni buscarlas iterando: para eso está
  `--grilla`.

## Dónde va

En la branch de la clase, `clase-NN`, la misma en la que se partió el apunte —no
en una aparte. Cada clase es una feature independiente y su branch la contiene
completa; el recorte es su segunda fase y va en un segundo commit.

Recién ahí se abre la PR, con la clase terminada. Si la branch todavía no
existe porque el texto ya está en `main`, entonces sí va una branch propia.
