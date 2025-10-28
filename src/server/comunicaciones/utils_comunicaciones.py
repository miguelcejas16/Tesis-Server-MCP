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

'''
Función sencilla para convertir filas de cursor a diccionarios.
'''
def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    cols = [c[0] for c in cursor.description] if cursor.description else []
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

'''
Fetch comunicaciones desde la base de datos.

Parametros:
- conn: conexión psycopg2 (o similar) ya abierta.
- tipo: filtrar por tipo ('AGRADECIMIENTO','SUGERENCIA','RECLAMO') opcional.
- afiliado_id: filtrar por afiliado_id opcional.
- limit: número máximo de filas a devolver (por defecto 100).
- offset: desplazamiento para paginación (por defecto 0).

Retorna: lista de diccionarios con las filas obtenidas.
Ejemplo:
  filas = fetch_comunicaciones(conn, tipo='RECLAMO', limit=10)
'''
def fetch_comunicaciones(conn, tipo: Optional[str] = None, afiliado_id: Optional[int] = None,
                        limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    sql = """
    SELECT nota_id, tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado,
           afiliado_id, creado_en
    FROM public.comunicacion
    WHERE 1=1
    """
    params = []
    if tipo:
        sql += " AND tipo = %s"
        params.append(tipo)
    if afiliado_id:
        sql += " AND afiliado_id = %s"
        params.append(afiliado_id)
    sql += " ORDER BY creado_en DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cur = conn.cursor()
    try:
        cur.execute(sql, tuple(params))
        rows = _rows_to_dicts(cur)
        return rows
    finally:
        cur.close()

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
def insert_comunicacion(conn,
                        tipo: str,
                        descripcion: str,
                        afiliado_id: int,
                        asunto: Optional[str] = None,
                        lugar: Optional[str] = None,
                        fecha_evento: Optional[datetime.date] = None,
                        resultado_deseado: Optional[str] = None) -> int:
    sql = """
    INSERT INTO public.comunicacion
      (tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado, afiliado_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING nota_id
    """
    params = (tipo, asunto, descripcion, lugar, fecha_evento, resultado_deseado, afiliado_id)

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        nota_id = cur.fetchone()[0]
        conn.commit()
        return nota_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()