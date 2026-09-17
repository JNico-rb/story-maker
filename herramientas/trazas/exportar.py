#!/usr/bin/env python3
"""Exporta una novela de story-maker a Langfuse como traza de dominio.

Proyecta `novelas/<slug>/registro.md` con la forma del problema:

    novela <slug>                     (traza)
    +- interrogatorio                 (span)
    |  +- interrogador / propuesta    (generation)
    |  +- revisor-continuidad / canon (generation)
    +- capitulo 01                    (span)
    |  +- intento 1                   (span)
    |  |  +- escritor / capitulo      (generation)
    |  |  +- resumidor / capitulo     (generation)
    |  |  +- revisor-encargo          (generation)
    |  |  +- revisor-continuidad      (generation)
    |  |  +- eventos: longitud, veredicto, decision_harness
    |  +- intento 2 ...
    +- final
       +- revisor-continuidad / global
       +- eventos: manuscrito, erratas, fin_ejecucion

Reglas (specs/functional.md 9.3), en orden de importancia:

1. NO es fuente de verdad. `registro.md` manda; esto es una proyeccion suya.
2. NO es puerta del flujo. Esto se ejecuta DESPUES, nunca desde dentro de /novela.
3. Fail-open: cualquier error se traga y se sale con codigo 0.
4. Solo lee. No escribe un byte en novelas/.
5. Las credenciales salen del entorno; este fichero no las contiene ni las imprime.

Uso:
    python herramientas/trazas/exportar.py novelas/<slug>
    python herramientas/trazas/exportar.py --todas
    python herramientas/trazas/exportar.py novelas/<slug> --dry-run

Variables de entorno: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.
Con --dry-run no hace falta ninguna: imprime el arbol y no envia nada.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COLUMNAS = [
    "fecha_hora", "evento", "etapa", "arco", "cap", "intento", "modelo",
    "pal_entrada", "pal_salida", "tok_entrada", "tok_salida", "coste_usd", "detalle",
]

VACIOS = {"", "-", "–", "—", "null", "None"}


# --------------------------------------------------------------- lectura

def celda(valor: str) -> str | None:
    valor = valor.strip()
    return None if valor in VACIOS else valor


def entero(valor: str | None) -> int | None:
    if valor is None:
        return None
    try:
        return int(valor.replace(".", "").replace(",", ""))
    except ValueError:
        return None


def decimal(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor.replace(",", "."))
    except ValueError:
        return None


def leer_registro(ruta: Path) -> list[dict[str, Any]]:
    """Parsea la tabla markdown de registro.md. Ignora cabecera y separador."""
    filas: list[dict[str, Any]] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea.startswith("|"):
            continue
        partes = [p for p in linea.strip("|").split("|")]
        if len(partes) < len(COLUMNAS):
            continue
        if partes[0].strip().startswith(("---", ":--")) or partes[1].strip() == "evento":
            continue
        fila = {k: celda(v) for k, v in zip(COLUMNAS, partes)}
        if not fila["evento"]:
            continue
        for k in ("pal_entrada", "pal_salida", "tok_entrada", "tok_salida"):
            fila[k] = entero(fila[k])
        fila["coste_usd"] = decimal(fila["coste_usd"])
        filas.append(fila)
    return filas


def momento(fila: dict[str, Any]) -> datetime | None:
    txt = fila.get("fecha_hora")
    if not txt:
        return None
    for formato in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(txt, formato).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def agente_y_modo(detalle: str | None) -> tuple[str | None, str | None]:
    """'escritor · modo capitulo (reescritura) · intento tecnico 1 · resultado ok · ...'"""
    if not detalle:
        return None, None
    trozos = [t.strip() for t in detalle.split("·")]
    agente = trozos[0] if trozos else None
    modo = None
    for t in trozos:
        if t.startswith("modo "):
            modo = t[len("modo "):].strip()
            break
    return agente, modo


def resultado_invocacion(detalle: str | None) -> str:
    if not detalle:
        return "desconocido"
    for estado in ("resultado ok", "resultado fallo", "resultado incumple", "en curso"):
        if estado in detalle:
            return estado.replace("resultado ", "")
    return "desconocido"


# --------------------------------------------------------------- estructura

def agrupar(filas: list[dict[str, Any]]) -> dict[str, Any]:
    """Reparte las filas en interrogatorio / capitulos / final, conservando el orden."""
    arbol: dict[str, Any] = {"interrogatorio": [], "capitulos": {}, "final": [], "otros": []}
    for fila in filas:
        cap = fila.get("cap")
        if cap:
            intento = fila.get("intento") or "-"
            arbol["capitulos"].setdefault(cap, {}).setdefault(intento, []).append(fila)
        elif fila.get("etapa") in ("final", "completa"):
            arbol["final"].append(fila)
        elif fila.get("etapa") == "interrogatorio":
            arbol["interrogatorio"].append(fila)
        else:
            arbol["otros"].append(fila)
    return arbol


def metadatos_novela(carpeta: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {"slug": carpeta.name}
    estado = carpeta / "estado.json"
    if estado.exists():
        try:
            e = json.loads(estado.read_text(encoding="utf-8"))
            meta.update({
                "etapa": e.get("etapa"),
                "total_capitulos": e.get("total_capitulos"),
                "capitulos_cerrados": len(e.get("capitulos") or {}),
                "por_agotamiento": sum(
                    1 for c in (e.get("capitulos") or {}).values() if c.get("por_agotamiento")),
                "invocaciones": e.get("invocaciones"),
                "avisos": e.get("avisos"),
                "version_estado": e.get("version"),
            })
        except (json.JSONDecodeError, OSError):
            meta["estado_json"] = "ilegible"
    cfg = carpeta / "config.json"
    if cfg.exists():
        try:
            c = json.loads(cfg.read_text(encoding="utf-8"))
            meta["perfil"] = (c.get("perfil") or {}).get("nombre")
            meta["modelos"] = {k: v for k, v in (c.get("modelos") or {}).items()
                               if isinstance(v, str)}
            meta["limites"] = c.get("limites")
        except (json.JSONDecodeError, OSError):
            meta["config_json"] = "ilegible"
    return meta


def metricas_cierre(carpeta: Path) -> dict[str, Any] | None:
    """Las metricas oficiales, tal como el harness las escribio. No se recalculan."""
    informe = carpeta / "informe-cierre.md"
    if not informe.exists():
        return None
    texto = informe.read_text(encoding="utf-8")
    metricas: dict[str, Any] = {}
    patron = re.compile(r"^\|\s*(\w[\w_]*)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(CUMPLE|NO CUMPLE|–|-)\s*\|",
                        re.MULTILINE)
    for nombre, valor, umbral, resultado in patron.findall(texto):
        metricas[nombre] = {"valor": valor, "umbral": umbral, "resultado": resultado}
    m = re.search(r"`cumple_todas`:\s*\*\*(\w+)\*\*", texto)
    if m:
        metricas["cumple_todas"] = m.group(1)
    return metricas or None


# --------------------------------------------------------------- emision

class Emisor:
    """Envuelve a Langfuse. En modo simulacro solo imprime el arbol."""

    def __init__(self, simulacro: bool):
        self.simulacro = simulacro
        self.cliente = None
        self.nivel = 0
        if simulacro:
            return
        from langfuse import Langfuse  # import tardio: --dry-run no necesita el SDK
        self.cliente = Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com",
        )

    def atributos_traza(self, **kw):
        """Los atributos de traza (nombre, session_id, tags) se propagan por contexto:
        el span raiz tiene que crearse DENTRO de este gestor."""
        if self.simulacro:
            return contextlib.nullcontext()
        from langfuse import propagate_attributes
        return propagate_attributes(**kw)

    def abrir_raiz(self, *, name, **kw):
        """Gestor de contexto: deja el span raiz activo, que es lo que hace que
        get_trace_url() y los atributos propagados apunten a esta traza."""
        if self.simulacro:
            print("  " * self.nivel + f"agent: {name}")
            self.nivel += 1
            return contextlib.nullcontext("simulado")
        return self.cliente.start_as_current_observation(name=name, as_type="agent", **kw)

    def abrir(self, padre, *, name, as_type="span", **kw):
        if self.simulacro:
            print("  " * self.nivel + f"{as_type}: {name}")
            self.nivel += 1
            return "simulado"
        return padre.start_observation(name=name, as_type=as_type, **kw)

    def cerrar(self, obs):
        if self.simulacro:
            self.nivel = max(0, self.nivel - 1)
            return
        obs.end()

    def evento(self, padre, *, name, metadata):
        if self.simulacro:
            print("  " * self.nivel + f"evento: {name}")
            return
        padre.create_event(name=name, metadata=metadata)

    def cerrar_todo(self):
        if not self.simulacro:
            self.cliente.flush()
            self.cliente.shutdown()


def emitir_invocacion(emisor: Emisor, padre, fila: dict[str, Any]) -> None:
    agente, modo = agente_y_modo(fila.get("detalle"))
    uso = {k: v for k, v in (("input", fila["tok_entrada"]), ("output", fila["tok_salida"])) if v}
    coste = {"total": fila["coste_usd"]} if fila["coste_usd"] else None
    obs = emisor.abrir(
        padre,
        name=f"{agente or 'agente'} / {modo or 'modo'}",
        as_type="generation",
        model=fila.get("modelo"),
        metadata={
            "agente": agente,
            "modo": modo,
            "resultado": resultado_invocacion(fila.get("detalle")),
            "pal_entrada": fila["pal_entrada"],
            "pal_salida": fila["pal_salida"],
            "fecha_hora": fila.get("fecha_hora"),
            "detalle": fila.get("detalle"),
            "_fuente": "registro.md",
        },
        usage_details=uso or None,
        cost_details=coste,
    )
    emisor.cerrar(obs)


def emitir_filas(emisor: Emisor, padre, filas: list[dict[str, Any]]) -> None:
    for fila in filas:
        if fila["evento"] == "invocacion":
            emitir_invocacion(emisor, padre, fila)
        else:
            emisor.evento(padre, name=fila["evento"],
                          metadata={k: v for k, v in fila.items() if v is not None})


def exportar(carpeta: Path, emisor: Emisor) -> str | None:
    registro = carpeta / "registro.md"
    if not registro.exists():
        print(f"  sin registro.md: {carpeta}", file=sys.stderr)
        return None

    filas = leer_registro(registro)
    if not filas:
        print(f"  registro.md sin filas: {carpeta}", file=sys.stderr)
        return None

    meta = metadatos_novela(carpeta)
    metricas = metricas_cierre(carpeta)
    idea = (carpeta / "idea.md").read_text(encoding="utf-8").strip() if (carpeta / "idea.md").exists() else None
    arbol = agrupar(filas)

    # propagate_attributes descarta valores de mas de 200 caracteres: ahi solo lo corto.
    # Todo lo demas (avisos, limites, invocaciones) va como metadato del span raiz.
    resumen = {k: meta.get(k) for k in ("perfil", "etapa", "total_capitulos",
                                        "capitulos_cerrados", "por_agotamiento")}
    contexto = emisor.atributos_traza(
        trace_name=f"novela {carpeta.name}",
        session_id=carpeta.name,
        tags=["story-maker", f"perfil:{meta.get('perfil')}", f"etapa:{meta.get('etapa')}"],
        metadata={k: v for k, v in resumen.items() if v is not None},
    )

    with contexto:
        with emisor.abrir_raiz(
                name=f"novela {carpeta.name}",
                input=idea,
                output=metricas,
                metadata={**meta, "filas_registro": len(filas), "_fuente": "registro.md"}) as raiz:
            emitir_arbol(emisor, raiz, arbol)
            # dentro del bloque: fuera, el span raiz ya no es el activo y no hay traza que consultar
            url = None if emisor.simulacro else emisor.cliente.get_trace_url()

    if emisor.simulacro:
        emisor.nivel = max(0, emisor.nivel - 1)
    return url


def emitir_arbol(emisor: Emisor, raiz, arbol: dict[str, Any]) -> None:
    if arbol["interrogatorio"]:
        etapa = emisor.abrir(raiz, name="interrogatorio")
        emitir_filas(emisor, etapa, arbol["interrogatorio"])
        emisor.cerrar(etapa)

    for cap in sorted(arbol["capitulos"]):
        span_cap = emisor.abrir(raiz, name=f"capitulo {cap}")
        for intento in sorted(arbol["capitulos"][cap]):
            filas_int = arbol["capitulos"][cap][intento]
            span_int = emisor.abrir(span_cap, name=f"intento {intento}",
                                    metadata=resumen_intento(filas_int))
            emitir_filas(emisor, span_int, filas_int)
            emisor.cerrar(span_int)
        emisor.cerrar(span_cap)

    if arbol["final"]:
        etapa = emisor.abrir(raiz, name="final")
        emitir_filas(emisor, etapa, arbol["final"])
        emisor.cerrar(etapa)

    if arbol["otros"]:
        etapa = emisor.abrir(raiz, name="otros")
        emitir_filas(emisor, etapa, arbol["otros"])
        emisor.cerrar(etapa)


def resumen_intento(filas: list[dict[str, Any]]) -> dict[str, Any]:
    veredicto = next((f["detalle"] for f in filas if f["evento"] == "veredicto"), None)
    decisiones = [f["detalle"] for f in filas if f["evento"] == "decision_harness"]
    longitud = next((f["detalle"] for f in filas if f["evento"] == "longitud"), None)
    return {
        "veredicto": veredicto,
        "longitud": longitud,
        "decisiones": decisiones,
        "invocaciones": sum(1 for f in filas if f["evento"] == "invocacion"),
        "pal_entrada_total": sum(f["pal_entrada"] or 0 for f in filas),
        "pal_salida_total": sum(f["pal_salida"] or 0 for f in filas),
    }


# --------------------------------------------------------------- entrada

def main() -> int:
    p = argparse.ArgumentParser(description="Exporta una novela de story-maker a Langfuse.")
    p.add_argument("carpeta", nargs="?", help="novelas/<slug>")
    p.add_argument("--todas", action="store_true", help="todas las carpetas de novelas/")
    p.add_argument("--dry-run", action="store_true", help="imprime el arbol y no envia nada")
    args = p.parse_args()

    raiz = Path(__file__).resolve().parents[2]
    if args.todas:
        carpetas = sorted(d for d in (raiz / "novelas").iterdir()
                          if d.is_dir() and (d / "registro.md").exists())
    elif args.carpeta:
        carpetas = [Path(args.carpeta) if Path(args.carpeta).is_absolute() else raiz / args.carpeta]
    else:
        p.error("indica una carpeta o --todas")

    if not args.dry_run and not (os.environ.get("LANGFUSE_PUBLIC_KEY")
                                 and os.environ.get("LANGFUSE_SECRET_KEY")):
        print("Faltan LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY en el entorno. "
              "Prueba con --dry-run para ver el arbol sin enviarlo.", file=sys.stderr)
        return 0  # regla 3: fail-open

    emisor = Emisor(simulacro=args.dry_run)
    try:
        for carpeta in carpetas:
            if not carpeta.exists():
                print(f"  no existe: {carpeta}", file=sys.stderr)
                continue
            print(f"{carpeta.name}:")
            url = exportar(carpeta, emisor)
            if url:
                print(f"  -> {url}")
        emisor.cerrar_todo()
    except Exception as err:  # regla 3: la observabilidad nunca rompe nada
        print(f"  error exportando (se ignora): {err}", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
