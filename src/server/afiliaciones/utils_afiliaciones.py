from datetime import date
from typing import List
import asyncpg

'''
Crea una nueva solicitud de afiliación.
Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  nombre_apellido (str) — Nombre completo del solicitante.
  dni (int) — DNI del solicitante.
  fecha_nacimiento (date) — Fecha de nacimiento.
  domicilio_calle (str) — Calle del domicilio.
  domicilio_numero (str) — Número del domicilio.
  localidad (str) — Localidad.
  provincia (str) — Provincia.
  telefono (str) — Teléfono de contacto.
  email (str) — Email de contacto.
  tipo_afiliado (str) — Tipo de afiliado (EMPLEADO, MONOTRIBUTISTA, JUBILADO, PARTICULAR).
Retorna:
  int — El ID de la afiliación creada.
'''
async def create_afiliacion(
        connection: asyncpg.Connection,
        nombre_apellido: str,
        dni: int,
        fecha_nacimiento: date,
        domicilio_calle: str,
        domicilio_numero: str,
        localidad: str,
        provincia: str,
        telefono: str,
        email: str,
        tipo_afiliado: str
        ) -> int:
    try:
        query = """
            INSERT INTO public.afiliacion (
                nombre_apellido, dni, fecha_nacimiento, domicilio_calle,
                domicilio_numero, localidad, provincia, telefono, email,
                tipo_afiliado, estado, adjuntos_confirmados
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'PENDIENTE', FALSE)
            RETURNING id
        """
        row = await connection.fetchrow(
            query,
            nombre_apellido, dni, fecha_nacimiento, domicilio_calle,
            domicilio_numero, localidad, provincia, telefono, email,
            tipo_afiliado
        )
        if not row:
            raise Exception("No se pudo crear la afiliación.")
        return row['id']
    except Exception as e:
        raise Exception(f"Error en utils.create_afiliacion: {e}")

'''
Marca una afiliación como esperando adjuntos y resetea la confirmación de adjuntos.
Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  afiliacion_id (int) — ID de la afiliación.
Retorna:
  bool — True si la actualización fue exitosa, False si no se encontró la afiliación.
'''
async def add_docs_afiliacion(connection: asyncpg.Connection, afiliacion_id: int) -> bool:
    try:
        query = """
            UPDATE public.afiliacion
            SET estado = 'ESPERANDO_ADJUNTOS',
                adjuntos_confirmados = FALSE
            WHERE id = $1
        """
        result = await connection.execute(query, afiliacion_id)

        if result and result.startswith("UPDATE"):
            try:
                updated = int(result.split()[1])
                return updated > 0
            except (IndexError, ValueError):
                return False
        return False
    except Exception as e:
        raise Exception(f"Error en utils.add_docs_afiliacion: {e}")

'''
Lista afiliaciones dentro de un rango de fechas (basado en la columna implícita creado_en o fecha que uses).
Nota: La tabla afiliacion no tiene timestamp explícito en el DDL proporcionado.
Esta función asume que existe o se puede usar otra lógica de filtrado.
Si no hay fecha de creación, ajustar según necesidad.
Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  fecha_desde (date) — Fecha inicial (inclusive).
  fecha_hasta (date) — Fecha final (inclusive).
Retorna:
  List[dict] — Lista de afiliaciones.
'''
async def list_afiliaciones_por_rango(
    connection: asyncpg.Connection,
    fecha_desde: date,
    fecha_hasta: date,
) -> List[dict]:
    try:
        # Como la tabla no tiene timestamp explícito, esta query es un ejemplo
        # Ajustar según campo real de fecha si existe
        query = """
            SELECT id, nombre_apellido, dni, fecha_nacimiento, domicilio_calle,
                   domicilio_numero, localidad, provincia, telefono, email,
                   tipo_afiliado, estado, adjuntos_confirmados
            FROM public.afiliacion
            WHERE fecha_nacimiento BETWEEN $1 AND $2
            ORDER BY id DESC
        """
        rows = await connection.fetch(query, fecha_desde, fecha_hasta)
        return [dict(r) for r in rows]
    except Exception as e:
        raise Exception(f"Error en utils.list_afiliaciones_por_rango: {e}")