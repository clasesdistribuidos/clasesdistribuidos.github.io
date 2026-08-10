---
title: Papers y bibliografía
layout: default
nav_order: 90
---

# Papers y bibliografía
{: .no_toc }

La materia funciona como un club de lectura técnico: cada clase se apoya en una
fuente primaria que se espera leída de antemano. Esta es la lista completa,
agrupada por eje temático.

{: .nota }
> Si es tu primera vez leyendo papers de sistemas, empezá por *How to Read a
> Paper* de Keshav. El método de las tres pasadas que propone ahorra muchísimo
> tiempo.

<details open markdown="block">
  <summary>Ejes</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

{% for grupo in site.data.papers %}
## {{ grupo.eje }}

{% for item in grupo.items -%}
- [**{{ item.titulo }}**]({{ item.url }}){% if item.tipo == "libro" %} · *libro*{% endif %}
  <br>{{ item.autor }}{% if item.clase %} · se discute en la clase {{ item.clase }}{% endif %}
  {%- if item.nota %}<br>{{ item.nota }}{% endif %}
{% endfor %}
{% endfor %}
