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
if TYPE_CHECKING:
    from ..server import AppContext

# Importar funciones de utilidad desde el módulo local
from . import utils_consultas

def register_consulta_tools(mcp: FastMCP):
    '''
    Registra todas las herramientas relacionadas con consultas de cobertura en la instancia del servidor MCP.
    
    Herramientas incluidas:
    - consultar_cobertura_practica: verifica si una práctica está cubierta
    - consultar_tope_disponible: consulta el tope disponible de una práctica
    - consultar_historial_consumos: lista el historial de consumos del afiliado
    '''

    @mcp.tool(name="consultar_cobertura_practica")
    async def consultar_cobertura_practica(
        ctx: Context[ServerSession, "AppContext"],
        afiliado_id: int,
        practica_id: int
    ) -> str:
        '''
        Consulta si una práctica está cubierta para un afiliado autenticado.

        OBJETIVO DE CUMPLIMIENTO Y SEGURIDAD (Ley 25.326):
        - La consulta de cobertura puede implicar información sensible de salud.
        - El asistente debe garantizar que la respuesta se brinda únicamente al afiliado autenticado.
        - Se debe minimizar la información y evitar recolectar datos clínicos.

        Qué hace:
        - Verifica si la práctica está incluida en el plan del afiliado.
        - Informa si está cubierta.
        - (Opcional) Informa copago y/o porcentaje si aplica.
        - Indica si requiere autorización previa y/o derivación.

        Cuándo usarla:
        - SOLO cuando el usuario ya fue identificado con el flujo de autenticación.
        - Cuando el afiliado pregunta si una práctica está cubierta por su plan.
        - Después de haber identificado la práctica (practica_id) a partir de una búsqueda en el catálogo.

        Precondiciones obligatorias para el asistente:
        - ✅ El afiliado debe estar autenticado (no permitir consultas anónimas).
        - ✅ El asistente debe tener un practica_id válido (no adivinar ni inferir).
        - ❌ No solicitar ni registrar diagnóstico, motivo de consulta, síntomas o información médica.

        Cómo comunicarlo al usuario (mensajes recomendados):
        Si está cubierta:
        - "Sí, la práctica está cubierta por tu plan."
        - "Requiere autorización previa." (si aplica)
        - "Tiene copago de $X." (si aplica)
        - "Requiere derivación/orden." (si aplica)

        Si NO está cubierta:
        - "La práctica no está incluida en tu plan."
        - "Si corresponde, podés gestionarlo como reintegro o consultar alternativas por los canales oficiales."

        Manejo de errores (mensaje genérico, sin filtrar información):
        - Si falla la consulta por cualquier motivo:
        "No pude consultar la cobertura en este momento. Intentá nuevamente más tarde."

        Información prohibida:
        - No mostrar afiliado_id ni practica_id al usuario.
        - No revelar información del plan que no sea necesaria para responder la consulta.
        - No mencionar datos de terceros.

        Parámetros:
        - afiliado_id (int): Identificador interno del afiliado autenticado.
        - practica_id (int): Identificador interno de la práctica.

        Retorna:
        - str (JSON): { covered: bool, copago: number|null, requiere_autorizacion: bool, requiere_derivacion: bool }
        El asistente debe traducirlo a una respuesta breve y clara.
        '''
        try:
            import json
            from decimal import Decimal

            db = ctx.request_context.lifespan_context.db
            resultado = await utils_consultas.practica_cubierta(
                db.conn,
                afiliado_id,
                practica_id
            )

            # Convertir Decimal a float para JSON
            if resultado.get("copago") and isinstance(resultado["copago"], Decimal):
                resultado["copago"] = float(resultado["copago"])

            return json.dumps(resultado, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error al consultar cobertura de práctica: {e}")

    @mcp.tool(name="consultar_tope_disponible")
    async def consultar_tope_disponible(
        ctx: Context[ServerSession, "AppContext"],
        afiliado_id: int,
        practica_id: int,
        fecha_ref: date,
        periodo: str
    ) -> str:
        '''
        Consulta el tope disponible de una práctica para un afiliado autenticado.

        OBJETIVO DE CUMPLIMIENTO Y SEGURIDAD:
        - El cálculo de topes utiliza consumos previos del afiliado, lo que constituye
        información personal vinculada a prestaciones de salud.
        - La información debe brindarse únicamente al afiliado autenticado.
        - Se debe minimizar la información expuesta y evitar mostrar historiales detallados.

        Qué hace:
        - Calcula el límite aplicable a la práctica para el periodo indicado.
        - Determina cuántas unidades ya fueron consumidas.
        - Calcula cuántas unidades quedan disponibles para el afiliado.

        Cuándo usarla:
        - SOLO cuando el afiliado ya fue identificado mediante el flujo de autenticación.
        - Cuando el afiliado consulta cuántas sesiones o usos le quedan disponibles.
        - Luego de identificar correctamente la práctica a consultar (practica_id).

        Precondiciones obligatorias para el asistente:
        - ✅ El afiliado debe estar autenticado.
        - ✅ El practica_id debe provenir de una búsqueda en el catálogo de prácticas.
        - ❌ No solicitar ni inferir diagnóstico, motivo médico o información clínica.
        - ❌ No consultar topes de terceros ni usar datos de otros afiliados.

        Cómo comunicarlo al usuario (mensajes recomendados):
        Si la práctica tiene tope:
        - "Esta práctica tiene un límite de X unidades por período."
        - "Actualmente tenés Z unidades disponibles."

        Si la práctica no tiene tope:
        - "Esta práctica no tiene un límite de uso en tu plan."

        Manejo de errores (mensaje genérico):
        - Ante cualquier error:
        "No pude consultar el tope disponible en este momento. Intentá nuevamente más tarde."

        Información prohibida:
        - No mostrar fechas exactas de consumos.
        - No detallar cada prestación utilizada.
        - No mostrar prestadores ni lugares de atención.
        - No exponer periodo_desde ni periodo_hasta al usuario.
        - No mostrar afiliado_id ni practica_id.

        Parámetros:
        - afiliado_id (int): Identificador interno del afiliado autenticado.
        - practica_id (int): Identificador interno de la práctica.
        - fecha_ref (date): Fecha de referencia para el cálculo (uso interno).
        - periodo (str): Periodo de cálculo ('mensual' o 'anual').

        Retorna:
        - str (JSON interno):
        El asistente DEBE filtrar la respuesta y comunicar solo la disponibilidad.
        '''
        try:
            import json
            from decimal import Decimal
            from datetime import date as _date

            # Validar periodo
            if periodo not in ["mensual", "anual"]:
                raise ValueError("periodo debe ser 'mensual' o 'anual'")

            db = ctx.request_context.lifespan_context.db
            resultado = await utils_consultas.tope_practica_disponible(
                db.conn,
                afiliado_id,
                practica_id,
                fecha_ref,
                periodo
            )

            # Serializar fechas
            if resultado:
                if isinstance(resultado.get("periodo_desde"), _date):
                    resultado["periodo_desde"] = resultado["periodo_desde"].isoformat()
                if isinstance(resultado.get("periodo_hasta"), _date):
                    resultado["periodo_hasta"] = resultado["periodo_hasta"].isoformat()

            return json.dumps(resultado, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error al consultar tope disponible: {e}")

    @mcp.tool(name="consultar_historial_consumos")
    async def consultar_historial_consumos(
        ctx: Context[ServerSession, "AppContext"],
        afiliado_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> str:
        '''
            Devuelve un historial resumido de consumos del afiliado autenticado.

            OBJETIVO DE CUMPLIMIENTO:
            - El historial de consumos contiene información sensible de salud.
            - El asistente debe mostrar un resumen útil pero minimizado.

            CUÁNDO USARLA:
            - SOLO si el afiliado ya fue identificado.
            - Cuando el afiliado solicita ver su historial de consumos.

            SALIDA PERMITIDA (OBLIGATORIA):
            - Listado acotado (recomendado: últimos 10 consumos).
            - Para cada consumo mostrar SOLO:
            • nombre de la práctica
            • período en formato MES/AÑO (ej. "Dic 2025")

            INFORMACIÓN PROHIBIDA:
            - Día exacto de la fecha.
            - Prestador.
            - Costos, copagos o porcentajes.
            - Observaciones o datos clínicos.

            MENSAJE SUGERIDO:
            - "Este es un resumen de tus últimos consumos:"
            - "Total mostrado: X consumos."

            MANEJO DE ERRORES:
            - Respuesta genérica:
            "No pude consultar tu historial en este momento. Intentá nuevamente más tarde."

            PARÁMETROS:
            - afiliado_id (int): afiliado autenticado.
            - limit (int): el asistente debe preferir 10.
            - offset (int): paginación.

            RETORNO:
            - JSON interno. Las fechas deben venir ya truncadas a MES/AÑO
            o el asistente debe ignorar el día.
            '''
        try:
            import json
            from decimal import Decimal
            from datetime import date as _date, datetime as _datetime

            db = ctx.request_context.lifespan_context.db
            resultado = await utils_consultas.historial_consumos(
                db.conn,
                afiliado_id,
                limit,
                offset
            )

            # Serializar tipos no JSON
            def _serial(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                if isinstance(obj, (_date, _datetime)):
                    return obj.strftime("%Y-%m")
                if isinstance(obj, dict):
                    return {k: _serial(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_serial(i) for i in obj]
                return obj

            return json.dumps(_serial(resultado), ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error al consultar historial de consumos: {e}")