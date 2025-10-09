from datetime import date
from typing import Optional, Literal
import asyncpg

'''
 * Crea un registro de reintegro temporal en la base de datos.
 * Parámetros:
 *   connection (asyncpg.Connection) — Conexión a la base de datos.
 *   afiliado_id (int) — ID del afiliado que solicita el reintegro.
 *   total_presentado (float) — Monto total presentado inicialmente.
 * Retorna:
 *   int — El ID del reintegro creado.
 * Notas:
 *   El estado inicial del reintegro se establece como 'pendiente'.
'''
async def create_temp_reintegro(
        connection: asyncpg.Connection, 
        afiliado_id: int,
        total_presentado: float,
        ) -> int: 
    try:
        query = """
            INSERT INTO public.reintegro (afiliado_id, estado, total_presentado, total_aprobado)
            VALUES ($1, 'pendiente', $2, 0.0)
            RETURNING reintegro_id
        """
        result = await connection.fetchrow(query, afiliado_id, total_presentado)

        if result:
            return result['reintegro_id']
        else:
            raise Exception("No se pudo crear el reintegro y obtener el ID.")
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
     *   - Actualiza también el campo `updated_at` con NOW().
     *   - Si la tabla o columnas tienen nombres distintos, ajustar la consulta.
    '''
    try:
        query = """
            UPDATE public.reintegro
            SET estado = 'ESPERANDO_ADJUNTOS',
                adjuntos_confirmados = FALSE,
                updated_at = NOW()
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
