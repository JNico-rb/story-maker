# Matriz de relación: planes contra arquitectura

Registro del bucle de gap del [proceso 3](../workflow/3-plan.md). Para cada spec anota qué secciones de [architecture.md](architecture.md) implementa su plan y cada diferencia entre los dos. Una spec no pasa a código mientras su apartado tenga una diferencia abierta.

## 1. Cobertura

Una fila por par sección–spec. Toda sección de `architecture.md` que describe comportamiento del producto tiene al menos una spec; las que solo registran razones, como §16, no entran. La tabla se rellena al cerrar la fase de docs, y cada spec marca sus filas como revisadas al llegar a gap cero.

| Sección | Spec | Revisada |
|---|---|---|

## 2. Diferencias

Una fila por diferencia entre el plan, junto con su spec, y `architecture.md`. Va en el apartado de su spec y se numera `NNN-k`.

| Tipo | Cuándo |
|---|---|
| omisión | `architecture.md` lo pide y el plan no lo entrega |
| deriva | el plan entrega algo que `architecture.md` no respalda |
| contradicción | los dos dicen cosas distintas: un nombre, un valor, un orden o un límite |

Una diferencia se cierra de una de tres formas:

- **plan corregido**;
- **doc corregido**, por el [proceso 1](../workflow/1-docs.md) y con grill;
- **la cubre otra spec**, que tiene esa sección en §1.

**Gap cero** de una spec: todas sus filas de §1 revisadas, ninguna diferencia abierta en su apartado y una pasada del subagente `auditor` sobre la versión final que no encuentra ninguna nueva.

### 001-base

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 002-aut-autenticacion

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 003-pol-politica-y-guardarrailes

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 004-obs-observabilidad

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 005-ent-entrevista-y-brief

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 006-tla-especificacion-del-harness

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 007-run-ejecuciones

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 008-mem-memoria

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 009-lea-validador-formal-de-la-historia

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 010-pln-planificacion

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 011-cap-produccion-por-capitulo

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 012-lin-linters-de-prosa

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 013-lec-lectura-web-y-pdf

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 014-pub-publicacion-y-versiones

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 015-cam-cambios-y-edicion-manual

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 016-mcp-servidor-mcp

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 017-evl-evaluacion-del-sistema

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|

### 018-sec-auditoria-de-seguridad

| # | Sección | Tipo | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|
