# definitions.md

Vocabulario del dominio de una solución de IA que genera novelas de ciencia ficción sobre el mundo posterior a la revolución de la IA.

Este documento define **qué entidades existen, qué atributos tienen y cómo se relacionan**. Las justificaciones de dominio están en `domain-knowledge.md`; las decisiones de diseño, en `architecture.md`.

Convención: los identificadores van sin acentos ni espacios, para que los diagramas rendericen en cualquier visor de Mermaid.

---

## 1. Storyworld (canon)

### Novum

Postulado especulativo raíz de la obra. El elemento novedoso que separa el mundo de la ficción del mundo real y del cual se deriva todo lo demás.

- **Atributos:** enunciado, ámbito (tecnológico / político / económico / cognitivo), fecha de aparición, origen (semilla o invención).
- **Relaciones:** `implica` → Consecuencia; `define` → Restriccion.

### Consecuencia

Derivación causal de un Novum o de otra Consecuencia.

- **Atributos:** enunciado, orden (1.º, 2.º, 3.er), confianza especulativa, visible en la narración (sí/no).
- **Relaciones:** `deriva_de` → Novum | Consecuencia; `sustenta` → RegimenGobernanza, RegimenEconomico, NormaSocial, Tecnologia.

### Restriccion

Regla inviolable del mundo: lo que no puede ocurrir.

- **Atributos:** enunciado, tipo (físico / legal / tecnológico / social), detectable automáticamente (sí/no).

### AIEntity

Entidad artificial con relevancia narrativa o estructural.

- **Atributos:** arquitectura, grado de agencia, alineamiento, estatus legal, sustrato, opacidad para los humanos.
- **Relaciones:** `instancia_de` → Tecnologia; `participa_en` → Evento; `miembro_de` → Faccion.

### Tecnologia

Artefacto o capacidad técnica existente en el mundo.

- **Atributos:** nombre, principio de funcionamiento, difusión, coste social.

### RegimenGobernanza / RegimenEconomico / NormaSocial

Estructuras derivadas de Consecuencias.

- **Atributos:** descripción, ámbito geográfico, vigencia temporal.
- **Relaciones:** `deriva_de` → Consecuencia.

### Faccion

Grupo con agencia colectiva: estado, corporación, culto, red informal.

- **Atributos:** objetivo, recursos, postura respecto a la IA.
- **Relaciones:** `agrupa` → Personaje, AIEntity.

### Personaje

- **Atributos:** nombre, rol narrativo, arco, motivación, voz, atributos físicos fijos.
- **Relaciones:** `miembro_de` → Faccion; `conoce` → EstadoEpistemico; `participa_en` → Evento.

### Localizacion

- **Atributos:** nombre, tipo, atmósfera, régimen aplicable.

### Evento

Hecho situado en el tiempo del mundo.

- **Atributos:** fecha ficcional, participantes, consecuencias, visible en la narración (sí/no).

### LineaTemporal

Ordenación de Eventos. Incluye eventos de trasfondo nunca narrados.

### Modelo de clases

```mermaid
classDiagram
    class Novum {
        enunciado
        ambito
        fecha_aparicion
        origen
    }
    class Consecuencia {
        enunciado
        orden
        confianza_especulativa
        visible_en_narracion
    }
    class Restriccion {
        enunciado
        tipo
        detectable_automaticamente
    }
    class AIEntity {
        arquitectura
        grado_agencia
        alineamiento
        estatus_legal
        sustrato
    }
    class Tecnologia {
        nombre
        principio
        difusion
        coste_social
    }
    class Faccion {
        objetivo
        recursos
        postura_ante_IA
    }
    class Personaje {
        nombre
        rol_narrativo
        arco
        motivacion
        voz
    }
    class Evento {
        fecha_ficcional
        participantes
        visible_en_narracion
    }
    class Localizacion {
        nombre
        tipo
        atmosfera
    }

    Novum "1" --> "*" Consecuencia : implica
    Consecuencia "1" --> "*" Consecuencia : encadena
    Consecuencia "1" --> "*" Tecnologia : sustenta
    Novum "1" --> "*" Restriccion : define
    Tecnologia "1" --> "*" AIEntity : instancia
    Faccion "1" --> "*" Personaje : agrupa
    Faccion "1" --> "*" AIEntity : controla
    Personaje "*" --> "*" Evento : participa
    Localizacion "1" --> "*" Evento : situa
```

---

## 2. Artefacto narrativo

Jerarquía: `Obra → Parte → Capitulo → Escena → Beat`

### Obra

- **Atributos:** título, longitud objetivo, estructura, premisa, resolución.

### Capitulo

- **Atributos:** número, función en el arco, tensión de entrada y de salida, longitud objetivo.

### Escena

Unidad mínima de generación y evaluación.

- **Atributos:** POV, tiempo narrativo, localización, personajes presentes, función dramática (setup / conflicto / giro / resolución), longitud objetivo.
- **Relaciones:** `produce` → DeltaDeEstado; `consume` y `produce` → EstadoEpistemico.

### DeltaDeEstado

Qué cambia en el mundo al terminar una escena.

- **Atributos:** entidades afectadas, cambios, reversible (sí/no).

### EstadoEpistemico

Qué sabe cada personaje al entrar y al salir de una escena.

- **Atributos:** personaje, hechos conocidos, hechos creídos falsamente, momento de adquisición.

### Outline

Plan jerárquico de la obra; contrato entre planificación y generación.

- **Atributos:** versión, jerarquía de capítulos y escenas, cobertura de arcos, congelado (sí/no).

### Modelo de clases

```mermaid
classDiagram
    class Obra {
        titulo
        longitud_objetivo
        estructura
        premisa
    }
    class Capitulo {
        numero
        funcion_en_arco
        tension_entrada
        tension_salida
    }
    class Escena {
        pov
        tiempo_narrativo
        personajes_presentes
        funcion_dramatica
        longitud_objetivo
    }
    class DeltaDeEstado {
        entidades_afectadas
        cambios
        reversible
    }
    class EstadoEpistemico {
        personaje
        hechos_conocidos
        hechos_creidos_falsos
        momento_adquisicion
    }
    class Outline {
        version
        cobertura_arcos
        congelado
    }

    Obra "1" --> "*" Capitulo
    Capitulo "1" --> "*" Escena
    Escena "1" --> "1" DeltaDeEstado : produce
    Escena "*" --> "*" EstadoEpistemico : consume y produce
    Outline "1" --> "1" Obra : planifica
```

---

## 3. Entrada e intención del usuario

### Semilla

Entrada libre del usuario. Longitud y especificidad variables.

### ContratoDeBrief

Objeto derivado de la Semilla que declara qué es obligación y qué es espacio de invención.

- **Atributos:** lista de Compromisos, lista de Huecos, grado de libertad (0–1).

### Compromiso

Afirmación explícita o fuertemente implícita del usuario.

- **Atributos:** enunciado, tipo (premisa / tono / personaje / final / …), dureza (inviolable | preferencia), verificable (sí/no).

### Hueco

Decisión no especificada que el sistema debe resolver.

- **Atributos:** ámbito, resuelto por, canon resultante.

---

## 4. Contexto de generación

### CanonCard

Proyección compacta de una entidad de storyworld, recuperada por escena.

### ResumenRodante

Comprimido acumulativo de lo ya narrado, más las últimas N escenas en literal.

### StyleSheet

Voz, registro, léxico prohibido, densidad de exposición, disciplina de POV.

### EstadoDelMundo

Snapshot mutable, versionado por escena, construido aplicando Deltas.

### Trazabilidad

Vínculo entre un fragmento generado y los elementos de canon, compromiso y config que lo justifican.

---

## 5. Calidad

### Evaluable

Unidad sujeta a evaluación: Escena, Capitulo, Arco u Obra.

### Criterio

Predicado evaluable.

- **Atributos:** dimensión, nivel de aplicación, método (determinista / modelo / humano), umbral, bloqueante (sí/no), origen (config / brief / política).

### Evaluador

Implementación de uno o varios Criterios: validador programático, juez LLM con rúbrica, o revisor humano.

- **Atributos:** criterios cubiertos, método, fiabilidad conocida.

### Defecto

Instancia de violación de un Criterio.

- **Atributos:** criterio, severidad, localización, causa raíz (contexto ausente / canon contradictorio / deriva de estilo / fallo de outline / config infactible).

### Veredicto

Resultado agregado por Evaluable.

- **Atributos:** evaluable, defectos, acción (aceptar | corregir | regenerar | escalar).

### Tropo

Patrón saturado del género, registrado para su detección.

- **Atributos:** nombre, descripción, origen del registro (curado | aprendido), frecuencia observada.

### Modelo de clases

```mermaid
classDiagram
    class Criterio {
        dimension
        nivel_aplicacion
        metodo
        umbral
        bloqueante
        origen
    }
    class Evaluador {
        criterios_cubiertos
        metodo
        fiabilidad_conocida
    }
    class Evaluable {
        tipo
        referencia
    }
    class Defecto {
        severidad
        localizacion
        causa_raiz
    }
    class Veredicto {
        accion
    }
    class Tropo {
        nombre
        origen_registro
        frecuencia_observada
    }

    Criterio "*" --> "1" Evaluador : implementado por
    Evaluador "*" --> "*" Evaluable : evalua
    Evaluable "1" --> "*" Defecto : produce
    Defecto "*" --> "1" Veredicto : agrega
    Tropo "*" --> "*" Criterio : alimenta
```

---

## 6. Configuración

### config

Fichero de parámetros de forma y operación, ajeno a la verdad ficcional.

```
config
├── identidad     { id, version, congelado_desde }
├── estructura    { objetivo_palabras, capitulos, forma_distribucion, pov_max }
├── poetica       { tono, ritmo, densidad_especulativa, registro }
├── calidad       { umbrales_por_puerta, criterios_activos }
└── operacion     { modelo, reintentos_max, presupuesto }
```

- **estructura** — parámetros verificables de forma determinista.
- **poetica** — parámetros solo evaluables por juicio.
- **calidad** — umbrales y criterios activos; no editable por el usuario final.
- **operacion** — parámetros de ejecución, invisibles para el usuario final.
