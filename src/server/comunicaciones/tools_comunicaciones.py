from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from datetime import date
from typing import Optional
import sys
from pathlib import Path
from typing import TYPE_CHECKING

root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))

# Importar el tipo AppContext desde server.py para anotaciones
# Se usa 'if TYPE_CHECKING' para evitar importaciones circulares en runtime.

if TYPE_CHECKING:
    from ..server import AppContext

# Importar funciones de utilidad desde el módulo local
from . import utils_comunicaciones

def register_comunicacion_tools(mcp: FastMCP):
    '''
    Registra las tools relacionadas con comunicaciones:
      - buscar_comunicaciones: busca por numero_afiliado y rango de fechas (obligatorio).
      - crear_comunicacion: inserta una nueva comunicación y devuelve el nota_id.

    Nota: La conexión a la BD es asyncpg y se obtiene desde ctx.request_context.lifespan_context.db.conn
    '''
    @mcp.tool(name="buscar_comunicaciones")
    async def buscar_comunicaciones(
        ctx: Context[ServerSession, "AppContext"],
        afiliado_id: int,
        nota_id: int
    ) -> str:
        '''
        Busca una comunicación específica por su ID y número de afiliado.

        ── Qué hace
        Recupera una comunicación de la tabla 'comunicacion' filtrando por:
        - numero_afiliado (obligatorio): número de 8 caracteres del afiliado
        - nota_id (obligatorio): ID único de la comunicación

        ── Parámetros
        - numero_afiliado (str): Número de afiliado de 8 caracteres (ej: "00001234")
        - nota_id (int): ID de la comunicación a buscar

        ── Qué devuelve
        String JSON con los datos de la comunicación encontrada:
        - nota_id: ID único de la comunicación
        - tipo: AGRADECIMIENTO, SUGERENCIA o RECLAMO
        - asunto: Tema principal
        - afiliado_id: ID interno del afiliado

        Si no se encuentra, devuelve null.

        ── Instrucciones para el LLM
        1) Solicitar al usuario:
           - Número de afiliado (8 caracteres)
           - ID de la comunicación (nota_id)

        2) Validar ANTES de llamar:
           - numero_afiliado: no vacío, exactamente 8 caracteres numéricos
           - nota_id: número entero positivo

        ── Ejemplo de uso
        Usuario: "Quiero ver mi comunicación número 42"
        LLM solicita: número de afiliado
        Usuario: "00001234"
        Llamada: buscar_comunicaciones(ctx, "00001234", 42)
        '''
        try:
            import json
            from decimal import Decimal
            from datetime import date as _date, datetime as _datetime

            db = ctx.request_context.lifespan_context.db
            comunicacion = await utils_comunicaciones.fetch_comunicacion_by_id(
                db.conn, afiliado_id, nota_id
            )

            # Serializar tipos no JSON (Decimal, date, datetime)
            def _serial(v):
                if v is None:
                    return None
                if isinstance(v, Decimal):
                    return float(v)
                if isinstance(v, (_date, _datetime)):
                    return v.isoformat()
                if isinstance(v, dict):
                    return {k: _serial(val) for k, val in v.items()}
                if isinstance(v, list):
                    return [_serial(i) for i in v]
                return v

            return json.dumps(_serial(comunicacion), ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error en tool.buscar_comunicaciones: {e}")

    @mcp.tool(name="crear_comunicacion")
    async def crear_comunicacion(
        ctx: Context[ServerSession, "AppContext"],
        tipo: str,
        descripcion: str,
        afiliado_id: int,
        asunto: Optional[str] = None,
        lugar: Optional[str] = None,
        fecha_evento: Optional[date] = None,
        resultado_deseado: Optional[str] = None
    ) -> int:
        '''
            Registra una comunicación formal de un afiliado hacia la obra social
            (agradecimiento, sugerencia o reclamo).

            OBJETIVO Y ALCANCE:
            - Esta herramienta registra comunicaciones internas para su análisis
            por las áreas correspondientes de la obra social.
            - La información se utiliza exclusivamente para la gestión del caso.

            INSTRUCCIONES OBLIGATORIAS PARA EL ASISTENTE (LLM):

            1. AVISO PREVIO AL AFILIADO
            - Antes de recopilar datos, informar:
                "Esta comunicación será registrada para su análisis interno.
                Los datos deben ser verídicos y se utilizarán únicamente para evaluar la situación."

            2. RECOLECCIÓN DE DATOS (OBLIGATORIA)
            - Solicitar de forma clara y respetuosa:
                1. Tipo de comunicación (AGRADECIMIENTO / SUGERENCIA / RECLAMO)
                2. Asunto o tema principal
                3. Descripción objetiva de la situación (tono formal, sin lenguaje ofensivo)
                4. Lugar relacionado con el hecho
                5. Fecha del evento (YYYY-MM-DD)
                6. Resultado o acción que espera el afiliado

            3. REDACCIÓN FINAL
            - Redactar un texto formal, claro y objetivo.
            - Diferenciar hechos de la solicitud.
            - No agregar opiniones propias del asistente.
            - No prometer resultados ni sanciones.

            4. REGISTRO
            - Llamar a esta herramienta SOLO cuando todos los campos estén completos.
            - No modificar el sentido de lo expresado por el afiliado.

            5. CIERRE
            - Informar:
                "Tu comunicación fue registrada correctamente.
                La obra social analizará la situación y continuará el tratamiento por los canales correspondientes."

            PARÁMETROS:
            - tipo (str): "AGRADECIMIENTO", "SUGERENCIA" o "RECLAMO".
            - descripcion (str): Texto final redactado.
            - afiliado_id (int): Identificador del afiliado.
            - asunto (str): Resumen breve.
            - lugar (str): Lugar del hecho.
            - fecha_evento (date): Fecha del evento.
            - resultado_deseado (str): Acción solicitada.

            RETORNA:
            - int: ID interno de la comunicación registrada.
            '''
        try:
            db = ctx.request_context.lifespan_context.db
            nota_id = await utils_comunicaciones.insert_comunicacion(
                db.conn,
                tipo,
                descripcion,
                afiliado_id,
                asunto=asunto,
                lugar=lugar,
                fecha_evento=fecha_evento,
                resultado_deseado=resultado_deseado
            )
            return nota_id
        except Exception as e:
            raise Exception(f"Error en tool.crear_comunicacion: {e}")

