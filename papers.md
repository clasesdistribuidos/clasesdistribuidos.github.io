---
title: Papers y bibliografía
layout: default
nav_order: 90
---

# Papers y bibliografía
{: .no_toc }

La materia funciona como un club de lectura técnico: cada clase se apoya en una
fuente primaria que se espera leída de antemano. Esta es la lista completa de
lecturas del [calendario](https://fiubata050.github.io/calendario/), agrupada
por eje temático, y al final lo que las clases mencionan sin asignarlo. La
práctica 1 tiene su propia
[bibliografía]({{ "/practica-01/15-referencias/" | relative_url }}).

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
{% if grupo.intro %}
{{ grupo.intro }}
{% endif %}
{% for item in grupo.items -%}
- {% if item.url %}[**{{ item.titulo }}**]({{ item.url }}){% else %}**{{ item.titulo }}**{% endif %}{% if item.tipo %} · *{{ item.tipo }}*{% endif %}
  <br>{{ item.autor }}{% if item.clases %} · {% if grupo.mencion %}se menciona en{% else %}se discute en{% endif %} {% include lista_clases.html clases=item.clases %}{% endif %}
  {%- if item.nota %}<br>{{ item.nota }}{% endif %}
{% endfor %}
{% endfor %}
