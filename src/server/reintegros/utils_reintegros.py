from datetime import date
from typing import Optional, Literal, List
import asyncpg

'''
Crea un reintegro temporal según la nueva estructura de la tabla `reintegro`.
Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  afiliado_id (int) — ID del afiliado que solicita el reintegro.
  cbu (str) — CBU asociado al reintegro.
Retorna:
  int — El ID del reintegro creado.
'''
async def create_temp_reintegro(
        connection: asyncpg.Connection, 
        afiliado_id: int,
        cbu: str
        ) -> int:
    try:
        query = """
            INSERT INTO public.reintegro (
                afiliado_id, estado, total_presentado, total_aprobado, cbu
            )
            VALUES ($1, 'PENDIENTE', 0::numeric, 0::numeric, $2)
            RETURNING reintegro_id
        """
        row = await connection.fetchrow(query, afiliado_id, cbu)
        if not row:
            raise Exception("No se pudo crear el reintegro.")
        return row['reintegro_id']
    except Exception as e:
        raise Exception(f"Error en utils.create_temp_reintegro: {e}")
'''
 * Agrega un ítem (práctica o medicamento) a un reintegro existente.
 * Parámetros:
 *   connection (asyncpg.Connection) — Conexión a la base de datos.
 *   reintegro_id (int) — ID del reintegro al que se agrega el ítem.
 *   tipo (Literal["M", "P"]) — Tipo de ítem ('M' para medicamento, 'P' para práctica).
 *   practica_id (Optional[int]) — ID de la práctica (si aplica).
 *   medicamento_id (Optional[int]) — ID del medicamento (si aplica).
 *   fecha_prestacion (date) — Fecha en que se realizó la prestación.
 *   monto_presentado (float) — Monto presentado para este ítem.
 * Retorna:
 *   int — El ID del ítem de reintegro creado.
'''
async def add_item_to_reintegro(
        connection: asyncpg.Connection, 
        reintegro_id: int,
        tipo: Literal["M", "P"],
        practica_id: Optional[int],
        medicamento_id: Optional[int],
        fecha_prestacion: date,
        monto_presentado: float,
        ) -> int:
    try:
        # Obtener fecha_presentacion del reintegro y validar diferencia <= 60 días
        row_reintegro = await connection.fetchrow(
            "SELECT fecha_presentacion FROM public.reintegro WHERE reintegro_id = $1",
            reintegro_id
        )
        if not row_reintegro:
            raise ValueError("Reintegro no encontrado")

        fecha_reintegro_ts = row_reintegro.get('fecha_presentacion')
        if fecha_reintegro_ts is None:
            raise ValueError("Fecha de presentación del reintegro no disponible")

        # Normalizar a date si viene como datetime
        fecha_reintegro_date = fecha_reintegro_ts.date() if hasattr(fecha_reintegro_ts, "date") else fecha_reintegro_ts

        # Calcular diferencia en días
        delta_days = abs((fecha_prestacion - fecha_reintegro_date).days)
        if delta_days > 60:
            raise ValueError("La diferencia entre fecha_presentacion del reintegro y fecha_prestacion del ítem supera los 60 días")

        # Mapear 'M'/'P' a los valores de la base de datos y validar
        if tipo == "M":
            tipo_db = "medicamento"
            if not medicamento_id:
                raise ValueError("medicamento_id es requerido cuando el tipo es 'M'")
        elif tipo == "P":
            tipo_db = "practica"
            if not practica_id:
                raise ValueError("practica_id es requerido cuando el tipo es 'P'")
        else:
            raise ValueError("El valor de 'tipo' debe ser 'M' o 'P'")

        query = """
            INSERT INTO public.reintegro_item (
                reintegro_id, tipo, practica_id, medicamento_id, 
                fecha_prestacion, monto_presentado
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING item_id
        """
        result = await connection.fetchrow(
            query,
            reintegro_id, tipo_db, practica_id, medicamento_id,
            fecha_prestacion, monto_presentado
        )

        if result:
            return result['item_id']
        else:
            raise Exception("No se pudo agregar el ítem y obtener el ID.")
    except Exception as e:
        raise Exception(f"Error en utils.add_item_to_reintegro: {e}")

async def add_docs_reintegro(connection: asyncpg.Connection, reintegro_id: int) -> bool:
    '''
     * Marca un reintegro como esperando adjuntos y resetea la confirmación de adjuntos.
     *
     * Parámetros:
     *   connection (asyncpg.Connection) — Conexión a la base de datos.
     *   reintegro_id (int) — ID del reintegro al que se le asignan los documentos.
     *
     * Retorna:
     *   bool — True si la actualización afectó al menos una fila (éxito), False si no (reintegro no encontrado).
     *
     * Notas:
     *   - Si la tabla o columnas tienen nombres distintos, ajustar la consulta.
    '''
    try:
        query = """
            UPDATE public.reintegro
            SET estado = 'ESPERANDO_ADJUNTOS',
                adjuntos_confirmados = FALSE
            WHERE reintegro_id = $1
        """
        result = await connection.execute(query, reintegro_id)

        # `execute` devuelve algo tipo 'UPDATE <n_rows>'
        if result and result.startswith("UPDATE"):
            try:
                updated = int(result.split()[1])
                return updated > 0
            except (IndexError, ValueError):
                # Resultado inesperado; considerar que no se actualizó
                return False
        return False
    except Exception as e:
        raise Exception(f"Error en utils.add_docs_reintegro: {e}")
    
'''
 * Lista reintegros para un afiliado dentro de un rango de fechas (inclusive).
 *
 * Parámetros:
 *   connection (asyncpg.Connection) — Conexión a la base de datos.
 *   afiliado_id (int) — ID del afiliado.
 *   fecha_desde (date) — Fecha inicial (inclusive).
 *   fecha_hasta (date) — Fecha final (inclusive).
 *
 * Retorna:
 *   List[dict] — Lista de reintegros (cada item es un dict con columnas seleccionadas).
 *
 * Notas:
 *   - Se usa fecha_presentacion::date para comparar solo la parte fecha.
 *   - La tabla `reintegro` no tiene `updated_at`; se seleccionan columnas existentes.
'''
async def list_reintegros_por_afiliado_y_rango(
    connection: asyncpg.Connection,
    afiliado_id: int,
    fecha_desde: date,
    fecha_hasta: date,
) -> List[dict]:
    try:
        query = """
            SELECT reintegro_id, afiliado_id, estado, total_presentado, total_aprobado, fecha_presentacion, observaciones
            FROM public.reintegro
            WHERE afiliado_id = $1
              AND fecha_presentacion::date BETWEEN $2 AND $3
            ORDER BY fecha_presentacion DESC
        """
        rows = await connection.fetch(query, afiliado_id, fecha_desde, fecha_hasta)
        return [dict(r) for r in rows]
    except Exception as e:
        raise Exception(f"Error en utils.list_reintegros_por_afiliado_y_rango: {e}")
