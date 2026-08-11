---
name: nueva-clase
description: Convierte el .md ya procesado de una clase en las páginas de _clases/clase-NN/, en una feature branch. Usar cuando el usuario pasa el apunte de una clase nueva (un único archivo de corrido, con marcadores [FIGURA:] y *[Nota:]*) y hay que dividirlo en secciones. No cubre el recorte de las figuras, que va después y por separado.
---

# Agregar una clase al sitio

El apunte llega como un único `.md` escrito de corrido, procesado fuera de este
repo. No hay que reescribirlo: hay que partirlo en páginas y dejar los
placeholders donde después van las figuras.

**Avisar al empezar:** "Voy a usar la skill nueva-clase para partir este apunte."

## Lo que trae el borrador

Ya viene con la taquigrafía que `scripts/split_clase.py` sabe traducir. No hay
que inventarla ni reemplazarla a mano:

| En el borrador | En la página |
| --- | --- |
| `## N. Título` | una página, con su front matter |
| `### N.M Subtítulo` | un `##` adentro de esa página, sin el número |
| `[FIGURA: descripción — notas pág. N / pizarra pág. M]` | recuadro punteado con la descripción y la referencia |
| `` [CÓDIGO PENDIENTE: descripción] `` | recuadro punteado, etiquetado como código |
| `*[Nota: texto]*` | callout azul |

Si un `[FIGURA:]` no está solo en su línea, el script no lo traduce y queda
como texto suelto. Contarlos antes y después.

## Pasos

1. **Branch propia**, desde `main` actualizado: `git switch -c clase-NN`.

2. **Copiar el borrador a un nombre con número**, fuera del repo — el
   scratchpad de la sesión sirve. El script saca el número de clase del nombre
   del archivo, así que tiene que llamarse `clase-NN.md`. El borrador no se
   versiona: una vez partido, las páginas son la única fuente.

3. **Contar lo que entra**, para poder comparar contra lo que sale:

   ```sh
   grep -cE '^## [0-9]+\.' borrador.md      # secciones -> páginas
   grep -cE '^\[FIGURA:.*\]$' borrador.md   # figuras que el script va a traducir
   grep -c '\[FIGURA:' borrador.md          # figuras totales; si difiere, hay una mal formada
   grep -cE '^\*\[Nota:' borrador.md
   ```

4. **Dry-run** y leer la salida entera:

   ```sh
   python3 scripts/split_clase.py <borrador> --titulo "Clase N — Tema" --dry-run
   ```

   El título sigue la forma `Clase N — Tema`, como los que ya están. Va a ser
   el `parent` de todas las secciones, así que cambiarlo después obliga a tocar
   todas las páginas.

   El script avisa cuántas líneas descartó de antes de la primera sección.
   Normalmente son el título genérico del borrador y su tabla de contenidos, y
   está bien tirarlas. **Leer ese aviso**: si ahí había contenido real, hay que
   rescatarlo a mano.

5. **Correr sin `--dry-run`.**

6. **Revisar el resultado** antes de mostrarlo:
   - la portada quedó solo con el título;
   - no quedó ningún `###` ni ningún subtítulo numerado;
   - la cuenta de `<figure class="figura">` coincide con la de `[FIGURA:]` del
     borrador, y cada uno conserva su `figura-ref`;
   - las páginas con dos o más `##` tienen índice interno y las de una sola no;
   - `bundle exec jekyll build` no rompe, y el sidebar muestra la clase con sus
     secciones en orden.

7. **Proponer los `Código pendiente` que falten.** El borrador marca solo
   algunos. Donde la prosa hable de código que no está —un ejemplo que se
   describe pero no se muestra, un archivo de configuración que se menciona—,
   agregar el recuadro con `class="figura figura-codigo"` y la etiqueta
   `Código pendiente`. Es criterio propio: listarlos en el mensaje final para
   que el usuario los apruebe o los saque.

8. **Commit y push de la branch**, y PR contra `main`. El merge lo decide el
   usuario.

## Lo que no hay que hacer

- **No reescribir la prosa.** El apunte ya está escrito y revisado; el trabajo
  acá es estructural. Si algo parece un error de contenido, señalarlo, no
  corregirlo.
- **No dibujar figuras.** Ni SVG, ni ASCII, ni mermaid. El placeholder se queda
  hasta que se recorte el dibujo real.
- **No versionar el borrador** ni dejarlo dentro del repo.
- **No usar `--force`** sobre una clase que ya existe: pisa las ediciones
  hechas a mano.

## Después: las figuras

Van en su propia branch, después de mergear esta. El proceso está en CLAUDE.md,
sección "Figuras: de la pizarra al sitio". Requiere que `scripts/recortar_figuras.py`
—hoy cableado a la clase 1— se parametrice por clase.
