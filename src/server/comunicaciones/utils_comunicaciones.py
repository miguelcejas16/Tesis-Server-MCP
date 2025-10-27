# ...existing code...
'''
Plan simple:
- Proveer dos utilidades sencillas para la tabla "comunicacion":
  1) fetch_comunicaciones: consultar notas con filtros básicos (tipo, afiliado_id, limit, offset).
  2) insert_comunicacion: insertar una fila y devolver el nota_id creado.
- Usar SQL parametrizado y operaciones de cursor simples.
- Hacer commit en el insert y rollback en caso de error.
'''

import datetime
from typing import List, Optional, Dict, Any
import asyncpg

'''
Función sencilla para convertir filas de asyncpg (Record) a diccionarios.
'''
def _records_to_dicts(rows: List[asyncpg.Record]) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]

'''
Fetch comunicaciones buscando por numero de afiliado y rango de fechas.
La búsqueda ENTRE fechas es obligatoria (fecha_desde y fecha_hasta).
Opcional: filtrar por nota_id.

Parámetros:
- connection: asyncpg.Connection ya abierta.
- numero_afiliado: cadena con el número de afiliado (bpchar(8) en la BD).
- fecha_desde: fecha inicio (inclusive) tipo datetime.date (obligatorio).
- fecha_hasta: fecha fin (inclusive) tipo datetime.date (obligatorio).
- nota_id: filtrar por nota_id opcional.

Retorna: lista de diccionarios con las filas obtenidas.
'''
async def fetch_comunicaciones_por_numero_y_rango(
        connection: asyncpg.Connection,
        numero_afiliado: str,
        fecha_desde: datetime.date,
        fecha_hasta: datetime.date,
        nota_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:

    if not numero_afiliado:
        raise ValueError("numero_afiliado es requerido")
    if fecha_desde is None or fecha_hasta is None:
        raise ValueError("fecha_desde y fecha_hasta son obligatorios")

    # Consulta simple y clara. No limit/offset según requerimiento.
    sql_base = """
    SELECT c.nota_id, c.tipo, c.asunto, c.descripcion, c.lugar, c.fecha_evento,
           c.resultado_deseado, c.afiliado_id, a.numero_afiliado, c.creado_en
    FROM public.comunicacion c
    JOIN public.afiliado a ON a.afiliado_id = c.afiliado_id
    WHERE a.numero_afiliado = $1
      AND c.creado_en::date BETWEEN $2 AND $3
    """
    params = [numero_afiliado, fecha_desde, fecha_hasta]

    if nota_id is not None:
        sql_base += " AND c.nota_id = $4"
        params.append(nota_id)

    sql_base += " ORDER BY c.creado_en DESC"

    try:
        rows = await connection.fetch(sql_base, *params)
        return _records_to_dicts(rows)
    except Exception as e:
        raise Exception(f"Error en fetch_comunicaciones_por_numero_y_rango: {e}")

'''
Insertar una nueva comunicación en la tabla (asyncpg).
Retorna el nota_id creado.
'''
async def insert_comunicacion(
        connection: asyncpg.Connection,
        tipo: str,
        descripcion: str,
        afiliado_id: int,
        asunto: Optional[str] = None,
        lugar: Optional[str] = None,
        fecha_evento: Optional[datetime.date] = None,
        resultado_deseado: Optional[str] = None
    ) -> int:

    sql = """
    INSERT INTO public.comunicacion
      (tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado, afiliado_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING nota_id
    """
    params = (tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado, afiliado_id)

    try:
        row = await connection.fetchrow(sql, *params)
        if not row:
            raise Exception("No se pudo insertar la comunicación")
        return row["nota_id"]
    except Exception as e:
        raise Exception(f"Error en insert_comunicacion: {e}")