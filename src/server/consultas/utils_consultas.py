# utils_consultas.py
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncpg

'''
Funciones utilitarias simples para consultas relacionadas con planes, prácticas y consumos.
Cada función hace una sola tarea y está documentada con un comentario antes de su definición.
'''

'''
Retorna el plan_id asociado a un afiliado.
Parámetros:
- conn: asyncpg.Connection abierto.
- afiliado_id: id del afiliado.
Retorna:
- plan_id (int) o None si no existe.

Ejemplo:
  plan = await get_plan_id_by_afiliado(conn, 123)
'''
async def get_plan_id_by_afiliado(conn: asyncpg.Connection, afiliado_id: int) -> Optional[int]:
    """
    Retorna plan_id del afiliado o None si no tiene.
    """
    row = await conn.fetchrow(
        "SELECT plan_id FROM public.afiliado WHERE afiliado_id = $1",
        afiliado_id
    )
    return row["plan_id"] if row else None

'''
Calcula la ventana (desde, hasta) para un periodo dado a partir de una fecha de referencia.
Soporta 'mensual' y 'anual'.
Parámetros:
- fecha_ref: fecha base.
- periodo: 'mensual' o 'anual'.
Retorna:
- tupla (desde: date, hasta: date)

Ejemplo:
  desde, hasta = periodo_window(date(2025,5,15), "mensual")
'''
def periodo_window(fecha_ref: date, periodo: str) -> tuple[date, date]:
    """
    Devuelve (desde, hasta) para 'mensual' o 'anual' con base calendario.
    """
    if periodo == "mensual":
        desde = fecha_ref.replace(day=1)
        if fecha_ref.month == 12:
            hasta = fecha_ref.replace(month=12, day=31)
        else:
            # último día del mes: tomar primer día del mes siguiente - 1
            siguiente = fecha_ref.replace(month=fecha_ref.month + 1, day=1)
            hasta = (siguiente - timedelta(days=1))
        return (desde, hasta)
    elif periodo == "anual":
        desde = date(fecha_ref.year, 1, 1)
        hasta = date(fecha_ref.year, 12, 31)
        return (desde, hasta)
    else:
        raise ValueError("periodo debe ser 'mensual' o 'anual'")

'''
Consulta si una práctica está cubierta para el plan del afiliado y devuelve detalles básicos.
Parámetros:
- conn: asyncpg.Connection abierto.
- afiliado_id: id del afiliado.
- practica_id: id de la práctica.
Retorna:
- dict con keys: covered (bool), copago, requiere_autorizacion (bool), requiere_derivacion (bool)

Ejemplo:
  info = await practica_cubierta(conn, 12, 345)
'''
async def practica_cubierta(
    conn: asyncpg.Connection,
    afiliado_id: int,
    practica_id: int
) -> Dict[str, Any]:
    """
    Devuelve:
      covered: bool
      copago: decimal | None
      requiere_autorizacion: bool
      requiere_derivacion: bool (no está en tu esquema -> siempre False)
    """
    try:
        plan_id = await get_plan_id_by_afiliado(conn, afiliado_id)  # afiliado.plan_id
        if plan_id is None:
            return {
                "covered": False,
                "copago": None,
                "requiere_autorizacion": False,
                "requiere_derivacion": False
            }

        # cobertura por plan/practica
        cob = await conn.fetchrow(
            """
            SELECT porcentaje, copago
            FROM public.cobertura_practica
            WHERE plan_id = $1 AND practica_id = $2
            """,
            plan_id, practica_id
        )

        # flag general de la práctica
        pr = await conn.fetchrow(
            "SELECT COALESCE(requiere_autorizacion,0) AS req FROM public.practica WHERE practica_id = $1",
            practica_id
        )

        covered = (cob is not None) and (cob["porcentaje"] > 0)
        return {
            "covered": covered,
            "copago": cob["copago"] if cob else None,
            "requiere_autorizacion": bool(pr["req"]) if pr else False,
            "requiere_derivacion": False  # tu esquema no lo tiene por plan
        }
    except Exception as e:
        raise Exception(f"Error en practica_cubierta: {e}")

'''
Calcula los topes disponibles para un afiliado en un periodo (mensual/anual).
Para cada tope devuelve practica_id, unidades_max, consumido, disponible y el periodo.
Parámetros:
- conn: asyncpg.Connection abierto.
- afiliado_id: id del afiliado.
- fecha_ref: fecha de referencia para el periodo.
- periodo: 'mensual' o 'anual'.

Ejemplo:
  topes = await topes_disponibles(conn, 12, date.today(), "mensual")
'''
async def topes_disponibles(
    conn: asyncpg.Connection,
    afiliado_id: int,
    fecha_ref: date,
    periodo: str  # 'mensual' | 'anual'
) -> List[Dict[str, Any]]:
    """
    Para cada tope (del plan del afiliado y periodo), devuelve:
      practica_id, unidades_max, consumido, disponible, periodo_desde, periodo_hasta
    """
    try:
        plan_id = await get_plan_id_by_afiliado(conn, afiliado_id)
        if plan_id is None:
            return []

        desde, hasta = periodo_window(fecha_ref, periodo)

        # Topes definidos para el plan y periodo
        topes = await conn.fetch(
            """
            SELECT practica_id, unidades_max
            FROM public.tope_practica
            WHERE plan_id = $1 AND periodo = $2
            """,
            plan_id, periodo
        )

        if not topes:
            return []

        # Consumo del afiliado en la ventana
        rows = await conn.fetch(
            """
            SELECT practica_id, COALESCE(SUM(unidades),0) AS unidades_consumidas
            FROM public.consumo
            WHERE afiliado_id = $1 AND fecha BETWEEN $2 AND $3
            GROUP BY practica_id
            """,
            afiliado_id, desde, hasta
        )
        consumos = {r["practica_id"]: r["unidades_consumidas"] for r in rows}

        out = []
        for t in topes:
            cons = consumos.get(t["practica_id"], 0)
            disp = max(t["unidades_max"] - cons, 0)
            out.append({
                "practica_id": t["practica_id"],
                "unidades_max": t["unidades_max"],
                "consumido": cons,
                "disponible": disp,
                "periodo_desde": desde,
                "periodo_hasta": hasta
            })
        return out
    except Exception as e:
        raise Exception(f"Error en topes_disponibles: {e}")

'''
Lista el historial de consumos de un afiliado con paginación simple.
Parámetros:
- conn: asyncpg.Connection abierto.
- afiliado_id: id del afiliado.
- limit, offset: paginación.

Retorna:
- Lista de dicts con fecha, practica_codigo, practica_nombre, prestador, costo, cobertura, copago

Ejemplo:
  hist = await historial_consumos(conn, 12, limit=20)
'''
async def historial_consumos(
    conn: asyncpg.Connection,
    afiliado_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Lista consumos con detalle: fecha, práctica, prestador, costo, cobertura(%), copago.
    """
    try:
        rows = await conn.fetch(
            """
            SELECT
              c.fecha,
              p.codigo   AS practica_codigo,
              p.nombre   AS practica_nombre,
              c.prestador,
              c.costo,
              c.cobertura,
              c.copago
            FROM public.consumo c
            JOIN public.practica p ON p.practica_id = c.practica_id
            WHERE c.afiliado_id = $1
            ORDER BY c.fecha DESC, c.consumo_id DESC
            LIMIT $2 OFFSET $3
            """,
            afiliado_id, limit, offset
        )
        return [dict(r) for r in rows]
    except Exception as e:
        raise Exception(f"Error en historial_consumos: {e}")

'''
Calcula el tope disponible para un afiliado en una práctica específica y periodo (mensual/anual).
Devuelve practica_id, unidades_max, consumido, disponible y el periodo.
Parámetros:
- conn: asyncpg.Connection abierto.
- afiliado_id: id del afiliado.
- practica_id: id de la práctica específica a consultar.
- fecha_ref: fecha de referencia para el periodo.
- periodo: 'mensual' o 'anual'.

Retorna:
- dict con practica_id, unidades_max, consumido, disponible, periodo_desde, periodo_hasta
- None si no hay tope definido para esa práctica

Ejemplo:
  tope = await tope_practica_disponible(conn, 12, 5, date.today(), "mensual")
'''
async def tope_practica_disponible(
    conn: asyncpg.Connection,
    afiliado_id: int,
    practica_id: int,
    fecha_ref: date,
    periodo: str  # 'mensual' | 'anual'
) -> Optional[Dict[str, Any]]:
    """
    Devuelve el tope disponible para una práctica específica.
    """
    try:
        plan_id = await get_plan_id_by_afiliado(conn, afiliado_id)
        if plan_id is None:
            return None

        desde, hasta = periodo_window(fecha_ref, periodo)

        # Buscar tope definido para esta práctica
        tope = await conn.fetchrow(
            """
            SELECT practica_id, unidades_max
            FROM public.tope_practica
            WHERE plan_id = $1 AND periodo = $2 AND practica_id = $3
            """,
            plan_id, periodo, practica_id
        )

        if not tope:
            return None

        # Consumo del afiliado para esta práctica en la ventana
        consumo_row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(unidades),0) AS unidades_consumidas
            FROM public.consumo
            WHERE afiliado_id = $1 
              AND practica_id = $2
              AND fecha BETWEEN $3 AND $4
            """,
            afiliado_id, practica_id, desde, hasta
        )

        consumido = consumo_row["unidades_consumidas"] if consumo_row else 0
        disponible = max(tope["unidades_max"] - consumido, 0)

        return {
            "practica_id": tope["practica_id"],
            "unidades_max": tope["unidades_max"],
            "consumido": consumido,
            "disponible": disponible,
            "periodo_desde": desde,
            "periodo_hasta": hasta
        }
    except Exception as e:
        raise Exception(f"Error en tope_practica_disponible: {e}")
