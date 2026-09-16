Abre una sesión nueva de Claude Code en el repo. El orquestador arranca con el contexto vacío salvo la skill; no arrastra esta conversación.
1. El comando

```
/novela nueva "<tu idea en una o dos frases>" perfil.palabras_por_capitulo=350 formato.palabras_min_capitulo=200 formato.palabras_max_capitulo=600
```
Si prefieres verificar primero las tuberías sin entrevista (usa la idea de la técnica de ascensores de respuestas-prueba.md, aprueba la escaleta solo):

```
/novela nueva "prueba" modo-prueba: pruebas/respuestas-prueba.md perfil.palabras_por_capitulo=350 formato.palabras_min_capitulo=200 formato.palabras_max_capitulo=600
```
Mi recomendación: la primera con modo prueba (comprueba el harness, no la historia); la segunda con tu idea y la entrevista real.