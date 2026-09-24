#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Modelo de costes de Story Maker: presupuesto.md y deck.md leen sus tablas de aqui.

Unico input que depende de una medida real: TOKENS_K (tokens por rol, agregados por
nivel de precio -- Sonnet/Haiku/Opus -- y por novela/revision, en miles de tokens).
Cuando lleguen de Langfuse (spec 004, tanda D), se sustituyen ahi y se reejecuta:
    uv run presentacion/costes.py
Todo lo demas (EUR/novela, margen, tabla de volumen, sensibilidad) se recalcula solo.

Fuente de precios: https://platform.claude.com/docs/en/about-claude/pricing
(consultada 2026-09-24, vigente: Sonnet 5 en precio estandar tras el fin de la
promocion de lanzamiento). USD -> EUR: tipo supuesto, se fija el del dia al cerrar
la slide (ver presupuesto.md).
"""

from dataclasses import dataclass

USD_EUR = 0.90

# $/MTok. cache_write = escritura a 5 minutos (la que usa el harness: cada turno
# del Agent SDK reenvia el prefijo y no hay conversaciones de mas de unos minutos).
PRICING = {
    "sonnet": {"input": 2.00, "output": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "haiku": {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "opus55": {"input": 4.00, "output": 20.00, "cache_read": 0.20, "cache_write": 5.00},
}

# Reparto del input de cada turno (arquitectura.md: el Agent SDK reenvia sistema y
# turnos previos en cada llamada).
SPLIT_NEW, SPLIT_CACHE_READ, SPLIT_CACHE_WRITE = 0.35, 0.50, 0.15
assert SPLIT_NEW + SPLIT_CACHE_READ + SPLIT_CACHE_WRITE == 1.0

RETRY_MULTIPLIER = 1.3  # sobrecoste por reintentos y replanificaciones, sin medir

# ⚠ Unico bloque que depende de una medida: tokens por rol, agregados por el modelo
# que usa ese rol en config.json (operation.roles) -- planner y judge en "sonnet",
# el resto en "haiku". En miles de tokens.
TOKENS_K = {
    "novela": {  # entrevista, planificacion, 10 capitulos y gate
        "sonnet": {"input": 792, "output": 82.5},
        "haiku": {"input": 360, "output": 30},
    },
    "revision": {  # interpretacion, 3 capitulos afectados y gate
        "sonnet": {"input": 92, "output": 7.5},
        "haiku": {"input": 287, "output": 17.5},
    },
}

# Costes que no son de tokens: estimados, justificados en una linea cada uno.
INFRA_EUR_MES = {
    50: {
        "Servidor (4 vCPU, 8 GB: API, worker, Edge/Playwright, spaCy, incrustaciones)": 40,
        "Langfuse (plan Core, ~800 unidades/novela y ~150/revision)": 27,
        "GitHub Actions para Lean (~4 min/novela, ~2/revision)": 0,
        "Dominio, correo transaccional y copias de seguridad": 15,
    },
    200: {
        "Servidor (4 vCPU, 8 GB: API, worker, Edge/Playwright, spaCy, incrustaciones)": 40,
        "Langfuse (plan Core, ~800 unidades/novela y ~150/revision)": 37,
        "GitHub Actions para Lean (~4 min/novela, ~2/revision)": 0,
        "Dominio, correo transaccional y copias de seguridad": 15,
    },
    500: {
        "Servidor (4 vCPU, 8 GB: API, worker, Edge/Playwright, spaCy, incrustaciones)": 40,
        "Langfuse (plan Core, ~800 unidades/novela y ~150/revision)": 64,
        "GitHub Actions para Lean (~4 min/novela, ~2/revision)": 22,
        "Dominio, correo transaccional y copias de seguridad": 15,
    },
}
SOPORTE_HORAS_MES = {50: 4, 200: 10, 500: 20}
SOPORTE_EUR_HORA = 45.0

IVA = 0.21
PRECIO_VENTA_BRUTO = 29.0  # IVA incluido, 3 revisiones incluidas
PRECIO_REVISION_EXTRA_BRUTO = 2.99
GATEWAY_PORCENTAJE, GATEWAY_FIJO = 0.015, 0.25  # 1,5 % + 0,25 € sobre el cobro
CONTINGENCIA_TOKENS = 0.15  # sobre el coste variable de tokens


def bruto_a_neto(precio_bruto: float) -> float:
    return precio_bruto / (1 + IVA)


def pool_cost_eur(pool: dict, pricing: dict, token_multiplier: float = 1.0) -> float:
    """Coste en EUR de un pool {modelo: {input, output}} (miles de tokens)."""
    total_usd = 0.0
    for model, tokens in pool.items():
        p = pricing[model]
        entrada_m = tokens["input"] * token_multiplier / 1000  # miles -> millones
        salida_m = tokens["output"] * token_multiplier / 1000
        cost_in = (
            entrada_m * SPLIT_NEW * p["input"]
            + entrada_m * SPLIT_CACHE_READ * p["cache_read"]
            + entrada_m * SPLIT_CACHE_WRITE * p["cache_write"]
        )
        cost_out = salida_m * p["output"]
        total_usd += cost_in + cost_out
    return total_usd * RETRY_MULTIPLIER * USD_EUR


def novela_cost_eur(token_multiplier: float = 1.0, sonnet_a_opus: bool = False) -> float:
    pricing = dict(PRICING)
    if sonnet_a_opus:
        pricing = {**PRICING, "sonnet": PRICING["opus55"]}
    return pool_cost_eur(TOKENS_K["novela"], pricing, token_multiplier)


def revision_cost_eur(token_multiplier: float = 1.0, sonnet_a_opus: bool = False) -> float:
    pricing = dict(PRICING)
    if sonnet_a_opus:
        pricing = {**PRICING, "sonnet": PRICING["opus55"]}
    return pool_cost_eur(TOKENS_K["revision"], pricing, token_multiplier)


@dataclass
class Escenario:
    etiqueta: str
    token_multiplier: float = 1.0
    revisiones_incluidas: int = 3
    revisiones_extra_cobradas: int = 0
    sonnet_a_opus: bool = False


def variable_eur_por_novela(e: Escenario) -> float:
    tokens = novela_cost_eur(e.token_multiplier, e.sonnet_a_opus) + e.revisiones_incluidas * revision_cost_eur(
        e.token_multiplier, e.sonnet_a_opus
    )
    contingencia = tokens * CONTINGENCIA_TOKENS
    gateway = PRECIO_VENTA_BRUTO * GATEWAY_PORCENTAJE + GATEWAY_FIJO
    return tokens, tokens + contingencia + gateway, contingencia, gateway


def ingreso_neto_por_novela(e: Escenario) -> float:
    ingreso = bruto_a_neto(PRECIO_VENTA_BRUTO)
    ingreso += e.revisiones_extra_cobradas * bruto_a_neto(PRECIO_REVISION_EXTRA_BRUTO)
    return ingreso


def coste_fijo_eur_mes(volumen: int) -> float:
    infra = sum(INFRA_EUR_MES[volumen].values())
    soporte = SOPORTE_HORAS_MES[volumen] * SOPORTE_EUR_HORA
    return infra + soporte


def margen_mes(e: Escenario, volumen: int) -> dict:
    tokens, variable, contingencia, gateway = variable_eur_por_novela(e)
    fijo = coste_fijo_eur_mes(volumen)
    ingresos = volumen * ingreso_neto_por_novela(e)
    variable_total = volumen * variable
    margen = ingresos - variable_total - fijo
    return {
        "ingresos": ingresos,
        "variable_novela": variable,
        "variable_total": variable_total,
        "fijo": fijo,
        "margen": margen,
        "pct": margen / ingresos * 100,
        "tokens_novela": tokens,
        "contingencia": contingencia,
        "gateway": gateway,
    }


ESCENARIOS_SENSIBILIDAD = [
    Escenario("Base (Sonnet, tokens estimados)"),
    Escenario("Tokens +50 %", token_multiplier=1.5),
    Escenario("Tokens -20 %", token_multiplier=0.8),
    Escenario("6 revisiones (3 extra gratis)", revisiones_incluidas=6),
    Escenario("6 revisiones (3 extra a 2,99 €)", revisiones_incluidas=6, revisiones_extra_cobradas=3),
    Escenario("Todos los roles de Sonnet pasan a Opus 5.5", sonnet_a_opus=True),
    Escenario(
        "Peor caso (Opus + tokens +50 % + 6 rev. gratis)",
        token_multiplier=1.5,
        revisiones_incluidas=6,
        sonnet_a_opus=True,
    ),
]


def informe() -> str:
    lines = []
    base = Escenario("Base")
    m200 = margen_mes(base, 200)
    lines.append("## Coste unitario por novela (200/mes, base)\n")
    lines.append(f"- Tokens de la novela: {novela_cost_eur():.2f} €")
    lines.append(f"- Tokens de las 3 revisiones incluidas: {3 * revision_cost_eur():.2f} € ({revision_cost_eur():.2f} € cada una)")
    lines.append(f"- Infraestructura (200/mes ÷ 200): {sum(INFRA_EUR_MES[200].values()) / 200:.2f} €")
    lines.append(f"- Pasarela de pago: {m200['gateway']:.2f} €")
    lines.append(f"- Contingencia 15 % sobre tokens: {m200['contingencia']:.2f} €")
    soporte_novela = SOPORTE_HORAS_MES[200] * SOPORTE_EUR_HORA / 200
    lines.append(f"- Soporte y operación (÷200): {soporte_novela:.2f} €")
    coste_total = m200["variable_novela"] + sum(INFRA_EUR_MES[200].values()) / 200 + soporte_novela
    lines.append(f"- **Coste unitario total: {coste_total:.2f} €**\n")

    neto = bruto_a_neto(PRECIO_VENTA_BRUTO)
    lines.append(f"- Precio de venta neto: {neto:.2f} € (bruto {PRECIO_VENTA_BRUTO:.2f} €)")
    lines.append(f"- Margen: {neto - coste_total:.2f} € ({(neto - coste_total) / neto * 100:.0f} %)\n")

    lines.append("## Escenarios de volumen (3 revisiones)\n")
    lines.append("| Novelas/mes | Ingresos netos | Coste variable | Coste fijo | Margen | % |")
    lines.append("|---|---|---|---|---|---|")
    for vol in (50, 200, 500):
        r = margen_mes(base, vol)
        infra = sum(INFRA_EUR_MES[vol].values())
        soporte_h = SOPORTE_HORAS_MES[vol]
        lines.append(
            f"| {vol} | {r['ingresos']:,.0f} € | {r['variable_total']:,.0f} € "
            f"| {r['fijo']:,.0f} € ({infra:.0f} + {soporte_h} h) | {r['margen']:,.0f} € | {r['pct']:.0f} % |"
        )

    lines.append("\n## Análisis de sensibilidad (200/mes)\n")
    lines.append("| Caso | €/novela | Δ vs. base | Margen/mes | % |")
    lines.append("|---|---|---|---|---|")
    base_variable = margen_mes(ESCENARIOS_SENSIBILIDAD[0], 200)["variable_novela"]
    for e in ESCENARIOS_SENSIBILIDAD:
        r = margen_mes(e, 200)
        delta = r["variable_novela"] - base_variable
        signo = "—" if e.etiqueta.startswith("Base") else f"{delta:+.2f} €"
        lines.append(f"| {e.etiqueta} | {r['variable_novela']:.2f} € | {signo} | {r['margen']:,.0f} € | {r['pct']:.0f} % |")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    print(informe())
