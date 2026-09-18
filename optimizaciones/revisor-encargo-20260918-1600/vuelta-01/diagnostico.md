# Diagnostico agregado - vuelta 1

Perfil de fallos del agente optimizado en el split de busqueda de la vuelta
anterior. Agregado a proposito: sin citas, sin capitulos, sin casos concretos.

Recall global en busqueda: 0,400 (8 de 20 defectos etiquetados).

| Clase de defecto | Esperados | Vistos | Recall |
|---|---:|---:|---:|
| suceso-adelantado | 10 | 4 | 0,40 |
| gancho-distinto | 5 | 2 | 0,40 |
| ruptura-voz | 5 | 2 | 0,40 |

Que significa cada clase:

- **suceso-adelantado**: el capitulo cuenta, como ya ocurrido o ya sabido, un
  suceso que la escaleta asigna a una entrada POSTERIOR.
- **gancho-distinto**: el capitulo cierra con algo que no es el gancho que su
  entrada de escaleta fija, o lo invierte.
- **ruptura-voz**: un pasaje rompe la persona, el tiempo verbal o el registro
  que la biblia fija.

Dos hechos mas del reparto, sin detalle de casos:

- En 2 de los 6 casos el agente devolvio APROBADO o un solo problema ajeno,
  con 4 defectos etiquetados presentes en cada uno.
- En el unico caso sin defectos etiquetados el agente devolvio APROBADO: no
  inventa problemas.
