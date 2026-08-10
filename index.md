---
title: Inicio
layout: default
nav_order: 1
---

# Sistemas Distribuidos I
{: .no_toc }

Apuntes de clase de **TA050 — Sistemas Distribuidos I**, Facultad de Ingeniería
de la Universidad de Buenos Aires.

Cada clase está dividida en secciones, y cada sección es una página. Podés
recorrerlas en orden con los botones de navegación al pie, saltar directo desde
el índice lateral, o buscar cualquier término con el buscador de arriba.

## Clases

{% assign clases = site.clases | where: "has_children", true | sort: "nav_order" %}
{% for clase in clases -%}
{%- assign secciones = site.clases | where: "parent", clase.title | sort: "nav_order" -%}
- [**{{ clase.title }}**]({{ clase.url | relative_url }}) — {{ secciones | size }} secciones
{% endfor %}

## Cómo se estudia

El método de la materia son papers de sistemas reales de empresas reales. La
clase funciona como un club de lectura técnico: se lee la fuente primaria antes
y se discute en clase, y los temas van emergiendo de esos casos de uso en lugar
de bajar desde una teoría previa.

La lista completa está en [papers y bibliografía]({{ "/papers/" | relative_url }}).
