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
Función sencilla para convertir asyncpg.Record a diccionarios.
'''
def _records_to_dicts(records) -> List[Dict[str, Any]]:
    return [dict(r) for r in records]

'''
Fetch comunicaciones desde la base de datos usando asyncpg.

Parametros:
- conn: conexión asyncpg.Connection ya abierta.
- tipo: filtrar por tipo ('AGRADECIMIENTO','SUGERENCIA','RECLAMO') opcional.
- afiliado_id: filtrar por afiliado_id opcional.
- limit: número máximo de filas a devolver (por defecto 100).
- offset: desplazamiento para paginación (por defecto 0).

Retorna: lista de diccionarios con las filas obtenidas.
Ejemplo:
  filas = await fetch_comunicaciones(conn, tipo='RECLAMO', limit=10)
'''
async def fetch_comunicaciones(
    conn: asyncpg.Connection,
    tipo: Optional[str] = None,
    afiliado_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    sql = """
    SELECT nota_id, tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado,
           afiliado_id, creado_en
    FROM public.comunicacion
    WHERE 1=1
    """
    params: List[Any] = []
    # construir condiciones con placeholders $1, $2, ...
    next_idx = 1
    if tipo:
        sql += f" AND tipo = ${next_idx}"
        params.append(tipo)
        next_idx += 1
    if afiliado_id is not None:
        sql += f" AND afiliado_id = ${next_idx}"
        params.append(afiliado_id)
        next_idx += 1

    sql += f" ORDER BY creado_en DESC LIMIT ${next_idx} OFFSET ${next_idx + 1}"
    params.extend([limit, offset])

    rows = await conn.fetch(sql, *params)
    return _records_to_dicts(rows)

'''
Insertar una nueva comunicación en la tabla.

Parametros:
- conn: conexión psycopg2 (o similar) ya abierta.
- tipo: obligatorio ('AGRADECIMIENTO','SUGERENCIA','RECLAMO').
- descripcion: obligatorio.
- afiliado_id: obligatorio.
- asunto, lugar, fecha_evento, resultado_deseado: opcionales.

Retorna: nota_id (int) del registro insertado.
Ejemplo:
  nid = insert_comunicacion(conn, 'SUGERENCIA', 'Texto...', 12, asunto='Tema')
'''
import datetime
from typing import Optional
import asyncpg

# Si recibes una CONEXIÓN asyncpg ya abierta
async def insert_comunicacion(
    conn: asyncpg.Connection,
    tipo: str,
    descripcion: str,
    afiliado_id: int,
    asunto: Optional[str] = None,
    lugar: Optional[str] = None,
    fecha_evento: Optional[datetime.date] = None,
    resultado_deseado: Optional[str] = None,
) -> int:
    sql = """
        INSERT INTO public.comunicacion
            (tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado, afiliado_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING nota_id
    """
    async with conn.transaction():
        row = await conn.fetchrow(
            sql,
            tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado, afiliado_id
        )
        # row es un asyncpg.Record; puedes indexar por nombre o por posición
        return row["nota_id"]
