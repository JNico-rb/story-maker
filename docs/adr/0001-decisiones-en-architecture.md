# Las decisiones de diseño viven en architecture.md; ADR solo cuando ningún doc las posee

Las decisiones del producto se registran en `architecture.md`: abiertas en §10, cerradas en §11, y su porqué —con las alternativas descartadas— en la sección que las explica (§3.2, §3.14…). Migrarlas a ADRs se valoró y se descartó el 2026-09-23: el porqué ya está en el cuerpo, migrar lo duplicaría y obligaría a reconstruir alternativas que nunca se documentaron. Solo va a `docs/adr/` lo que cumple las cuatro condiciones del paso 3 de [`workflow/1-docs.md`](../../workflow/1-docs.md).
