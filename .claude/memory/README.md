# Memoria del proyecto — espejo commiteado

Esta carpeta es la copia commiteada de la memoria automática de Claude Code para story-maker. La memoria viva, la que Claude Code carga en cada sesión, está en el perfil del usuario (`~/.claude/projects/<proyecto>/memory/`), fuera del repositorio. El encargo pide `.claude/` commiteada con la memoria; esta copia es esa evidencia y sirve para rehidratar la memoria en otra máquina copiándola al perfil.

- `MEMORY.md` es el índice: una línea por memoria, con enlace a su fichero.
- Cada fichero es una memoria: hechos del entorno, preferencias de trabajo del usuario o decisiones del proyecto, con su porqué y cómo aplicarla.

## Sincronización

- Manual, al cerrar una sesión en la que cambió alguna memoria.
- La hace el integrador (`/orquestar`, checkout principal, V2): copia los ficheros del perfil a esta carpeta, los sanea y commitea. Los carriles no la tocan.
- Sanear = quitar nombres de personas y de la empresa, identificadores de sesión y rutas de usuario; el contenido no cambia.
- Si una memoria del perfil se borra, se borra aquí en la misma copia.

Registro del uso en `docs/verification.md` §9.5.
