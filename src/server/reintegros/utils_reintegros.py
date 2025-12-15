from datetime import date, datetime
from decimal import Decimal
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

        # Verificar si el ítem ya existe en el reintegro
        query_check = """
            SELECT item_id FROM public.reintegro_item
            WHERE reintegro_id = $1
              AND tipo = $2
              AND COALESCE(practica_id, 0) = $3
              AND COALESCE(medicamento_id, 0) = $4
        """
        existing_item = await connection.fetchrow(
            query_check,
            reintegro_id,
            tipo_db,
            practica_id or 0,
            medicamento_id or 0,
        )
        
        if existing_item:
            raise ValueError("El ítem ya existe en este reintegro")

        # Insertar el ítem y actualizar el total del reintegro dentro de una transacción simple
        query = """
            INSERT INTO public.reintegro_item (
                reintegro_id, tipo, practica_id, medicamento_id, 
                fecha_prestacion, monto_presentado
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING item_id
        """

        async with connection.transaction():
            result = await connection.fetchrow(
                query,
                reintegro_id, tipo_db, practica_id, medicamento_id,
                fecha_prestacion, monto_presentado
            )

            if not result:
                raise Exception("No se pudo agregar el ítem y obtener el ID.")

            item_id = result['item_id']

            # Usar Decimal para sumar con precisión
            monto_dec = Decimal(str(monto_presentado))
            await connection.execute(
                "UPDATE public.reintegro SET total_presentado = COALESCE(total_presentado, 0::numeric) + $1 WHERE reintegro_id = $2",
                monto_dec, reintegro_id
            )

        return item_id
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
Obtiene un reintegro por su ID y afiliado_id junto con sus ítems asociados.
Incluye información de práctica (nombre) o medicamento (principio_activo, marca)
según corresponda al tipo del ítem.
Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  reintegro_id (int) — ID del reintegro a buscar.
  afiliado_id (int) — ID del afiliado dueño del reintegro.
Retorna:
  Optional[dict] — Diccionario con los datos del reintegro y una clave 'items' con la lista de ítems;
                   None si no se encuentra el reintegro, no pertenece al afiliado o está CANCELADO.
'''
async def get_reintegro_por_id(
    connection: asyncpg.Connection,
    reintegro_id: int,
    afiliado_id: int
) -> Optional[dict]:
    try:
        # Obtener el reintegro principal validando reintegro_id Y afiliado_id
        query_reintegro = """
            SELECT reintegro_id, afiliado_id, estado, total_presentado, total_aprobado,
                   fecha_presentacion, observaciones, cbu, adjuntos_confirmados
            FROM public.reintegro
            WHERE reintegro_id = $1 AND afiliado_id = $2
        """
        row = await connection.fetchrow(query_reintegro, reintegro_id, afiliado_id)
        if not row:
            return None # Reintegro no encontrado o no pertenece al afiliado

        # Validar que el reintegro no esté CANCELADO
        if row['estado'] == 'CANCELADO':
            return None

        # Convertir fila a dict y hacer valores JSON-safe (Decimal -> float, datetime/date -> ISO)
        def _json_safe_value(v):
            if isinstance(v, Decimal):
                return float(v)
            if isinstance(v, datetime) or isinstance(v, date):
                return v.isoformat()
            return v

        reintegro = {k: _json_safe_value(v) for k, v in dict(row).items()}

        # Obtener los items asociados al reintegro, incluyendo datos de practica/medicamento
        query_items = """
            SELECT ri.item_id,
                   ri.reintegro_id,
                   ri.tipo,
                   ri.practica_id,
                   p.nombre AS practica_nombre,
                   ri.medicamento_id,
                   m.principio_activo AS medicamento_principio_activo,
                   m.marca AS medicamento_marca,
                   ri.fecha_prestacion,
                   ri.monto_presentado,
                   ri.monto_aprobado,
                   ri.cobertura_aplicada,
                   ri.copago,
                   ri.prestador_txt,
                   ri.comprobante_txt
            FROM public.reintegro_item ri
            LEFT JOIN public.practica p ON ri.practica_id = p.practica_id
            LEFT JOIN public.medicamento m ON ri.medicamento_id = m.medicamento_id
            WHERE ri.reintegro_id = $1
            ORDER BY ri.fecha_prestacion, ri.item_id
        """
        items_rows = await connection.fetch(query_items, reintegro_id)

        items = []
        for r in items_rows:
            item = {k: _json_safe_value(v) for k, v in dict(r).items()}
            items.append(item)

        # Agregar la lista de items al dict del reintegro
        reintegro['items'] = items

        return reintegro
    except Exception as e:
        raise Exception(f"Error en utils.get_reintegro_por_id: {e}")

'''
Lista reintegros para un afiliado dentro de un rango de fechas (inclusive).
Excluye reintegros con estado CANCELADO.

Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  afiliado_id (int) — ID del afiliado.
  fecha_desde (date) — Fecha inicial (inclusive).
  fecha_hasta (date) — Fecha final (inclusive).

Retorna:
  List[dict] — Lista de reintegros (cada item es un dict con columnas seleccionadas).
              No incluye reintegros CANCELADOS.

Notas:
  - Se usa fecha_presentacion::date para comparar solo la parte fecha.
  - La tabla `reintegro` no tiene `updated_at`; se seleccionan columnas existentes.
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
              AND estado != 'CANCELADO'
            ORDER BY fecha_presentacion DESC
        """
        rows = await connection.fetch(query, afiliado_id, fecha_desde, fecha_hasta)
        return [dict(r) for r in rows]
    except Exception as e:
        raise Exception(f"Error en utils.list_reintegros_por_afiliado_y_rango: {e}")

'''
Cancela un reintegro poniendo su estado en 'CANCELADO'.
Valida que el reintegro pertenezca al afiliado dado.

Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  reintegro_id (int) — ID del reintegro a cancelar.
  afiliado_id (int) — ID del afiliado dueño del reintegro.

Retorna:
  bool — True si se actualizó al menos una fila; False si no existe o no pertenece al afiliado.
'''
async def cancelar_reintegro(
    connection: asyncpg.Connection,
    reintegro_id: int,
    afiliado_id: int
) -> bool:
    try:
        query = """
            UPDATE public.reintegro
            SET estado = 'CANCELADO'
            WHERE reintegro_id = $1 AND afiliado_id = $2
        """
        result = await connection.execute(query, reintegro_id, afiliado_id)
        if result and result.startswith("UPDATE"):
            try:
                updated = int(result.split()[1])
                return updated > 0
            except (IndexError, ValueError):
                return False
        return False
    except Exception as e:
        raise Exception(f"Error en utils.cancelar_reintegro: {e}")