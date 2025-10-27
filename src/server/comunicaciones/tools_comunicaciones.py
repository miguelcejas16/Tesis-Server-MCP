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
        numero_afiliado: str,
        fecha_desde: date,
        fecha_hasta: date,
        nota_id: Optional[int] = None
    ) -> str:
        '''
        Busca comunicaciones registradas por número de afiliado dentro de un rango de fechas obligatorio.

        ── Qué hace
        Consulta la tabla 'comunicacion' filtrando por:
        - numero_afiliado (obligatorio)
        - Rango de fechas [fecha_desde, fecha_hasta] (ambas obligatorias)
        - nota_id (opcional, para buscar una comunicación específica)

        ── Parámetros
        - numero_afiliado (str): Número de afiliado de 8 caracteres (ej: "00001234")
        - fecha_desde (date): Fecha de inicio del rango (formato YYYY-MM-DD)
        - fecha_hasta (date): Fecha de fin del rango (formato YYYY-MM-DD)
        - nota_id (int, opcional): ID específico de la comunicación a buscar

        ── Qué devuelve
        String JSON con lista de comunicaciones encontradas. Cada comunicación incluye:
        - nota_id: ID único de la comunicación
        - tipo: AGRADECIMIENTO, SUGERENCIA o RECLAMO
        - asunto: Tema principal
        - descripcion: Texto completo de la comunicación
        - lugar: Lugar del evento
        - fecha_evento: Fecha del hecho reportado
        - resultado_deseado: Solicitud del afiliado
        - afiliado_id: ID interno del afiliado
        - numero_afiliado: Número de afiliado
        - creado_en: Fecha/hora de registro en el sistema

        ── Instrucciones para el LLM
        1) SIEMPRE pedir una fecha aproximada al usuario:
           "¿Recordás más o menos cuándo hiciste la comunicación?"
           Ejemplos válidos: "alrededor del 10/05/2025", "a fines de mayo", "la semana pasada"

        2) Con la fecha aproximada, construir un rango de ±5 días:
           - fecha_desde = fecha_aproximada - 5 días
           - fecha_hasta = fecha_aproximada + 5 días

        3) Si el usuario da un rango explícito (ej: "entre el 1 y 20 de mayo"),
           usar ese rango sin modificar.

        4) Preguntar si conoce el ID de la nota:
           "¿Tenés el número de la comunicación?"
           - Si lo tiene: incluir nota_id
           - Si no lo tiene: omitir nota_id (buscar todas en el rango)

        5) Validar ANTES de llamar:
           - numero_afiliado: no vacío, 8 caracteres
           - fecha_desde <= fecha_hasta
           - Fechas en formato ISO (YYYY-MM-DD)

        6) Si el usuario no recuerda fecha, pedir referencia temporal:
           "semana pasada" → usar miércoles de esa semana
           "principios de marzo" → usar 05/03/2025
           Luego aplicar ±5 días

        ── Ejemplo de uso
        Usuario: "Quiero ver mi reclamo del 15 de mayo"
        LLM calcula: fecha_desde=2025-05-10, fecha_hasta=2025-05-20
        Llamada: buscar_comunicaciones(ctx, "00001234", date(2025,5,10), date(2025,5,20))
        '''
        try:
            import json
            from decimal import Decimal
            from datetime import date as _date, datetime as _datetime

            db = ctx.request_context.lifespan_context.db
            rows = await utils_comunicaciones.fetch_comunicaciones_por_numero_y_rango(
                db.conn, numero_afiliado, fecha_desde, fecha_hasta, nota_id
            )

            # Serializar tipos no JSON (Decimal, date, datetime)
            def _serial(v):
                if isinstance(v, Decimal):
                    return float(v)
                if isinstance(v, (_date, _datetime)):
                    return v.isoformat()
                if isinstance(v, dict):
                    return {k: _serial(val) for k, val in v.items()}
                if isinstance(v, list):
                    return [_serial(i) for i in v]
                return v

            return json.dumps(_serial(rows), ensure_ascii=False)
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
        Registra una nueva comunicación formal de un afiliado hacia la institución
        (agradecimiento, sugerencia o reclamo).

        👉 Instrucciones para el modelo (LLM):
        - Antes de usar esta herramienta, debes recopilar toda la información necesaria
        a través del diálogo con el afiliado. No invoques la tool hasta que tengas
        TODOS los campos completos.
        - Pregunta al afiliado de manera natural y respetuosa los siguientes datos:
            1. tipo de comunicación (AGRADECIMIENTO / SUGERENCIA / RECLAMO)
            2. asunto o tema principal
            3. descripción detallada de la situación (redacta en tono formal)
            4. lugar donde ocurrió o se relaciona el hecho
            5. fecha del evento o situación (usa formato YYYY-MM-DD)
            6. resultado deseado o solicitud del afiliado
        - Luego, redacta la descripción final combinando la información recopilada
        en un texto coherente, formal y claro, apto para registrar como comunicación oficial.
        - Finalmente, llama a esta tool pasando todos los parámetros completos.

        Parámetros:
        - tipo (str): "AGRADECIMIENTO", "SUGERENCIA" o "RECLAMO".
        - descripcion (str): Texto redactado final de la comunicación.
        - afiliado_id (int): ID del afiliado que realiza la comunicación.
        - asunto (str): Tema principal o resumen breve.
        - lugar (str): Lugar relacionado con el hecho.
        - fecha_evento (date): Fecha del hecho o situación.
        - resultado_deseado (str): Qué espera el afiliado que se haga al respecto.

        Retorna:
        - El ID (int) de la comunicación creada en la base de datos.

        Ejemplo de uso esperado:
        1️⃣ El afiliado explica su situación.
        2️⃣ El modelo formula preguntas para obtener todos los campos.
        3️⃣ El modelo redacta un texto formal.
        4️⃣ El modelo llama a crear_comunicacion() con todos los valores completos.
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

