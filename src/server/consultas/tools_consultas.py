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
        Consulta si una práctica está cubierta para un afiliado.

        Qué hace:
        - Verifica si la práctica está incluida en el plan del afiliado.
        - Informa el porcentaje de cobertura y copago.
        - Indica si requiere autorización previa.

        Cuándo usarla:
        - Cuando el afiliado pregunta "¿Está cubierta esta práctica?"
        - Antes de realizar un tope o consumo.
        - Para verificar requisitos previos.

        Cómo comunicarlo al usuario:
        Si está cubierta:
        • "Sí, esa práctica está cubierta por tu plan."
        • "Tenés un copago de $X" (si aplica).
        • "Requiere autorización previa" (si aplica).

        Si NO está cubierta:
        • "Esa práctica no está incluida en tu plan."
        • "Podés consultarla como reintegro."

        Parámetros:
        - afiliado_id (int): ID del afiliado.
        - practica_id (int): ID de la práctica a consultar.

        Retorna:
        - str: JSON con covered (bool), copago, requiere_autorizacion, requiere_derivacion.
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
        Consulta el tope disponible de una práctica para el afiliado.

        Qué hace:
        - Calcula cuántas unidades puede usar el afiliado en el periodo.
        - Muestra cuántas ya consumió y cuántas quedan disponibles.

        Cuándo usarla:
        - Cuando el afiliado pregunta "¿Cuántas sesiones me quedan?"
        - Para verificar disponibilidad antes de solicitar una práctica.

        Cómo comunicarlo al usuario:
        Si hay tope:
        • "Tenés un límite de X unidades por [mes/año]."
        • "Ya usaste Y, te quedan Z disponibles."

        Si NO hay tope:
        • "Esta práctica no tiene límite de uso en tu plan."

        Parámetros:
        - afiliado_id (int): ID del afiliado.
        - practica_id (int): ID de la práctica.
        - fecha_ref (date): Fecha de referencia (YYYY-MM-DD).
        - periodo (str): siempre 'mensual'.

        Retorna:
        - str: JSON con unidades_max, consumido, disponible, periodo_desde, periodo_hasta.
        - Si no hay tope definido: retorna "null".
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
        limit: int = 50,
        offset: int = 0
    ) -> str:
        '''
        Lista el historial de consumos del afiliado.

        Qué hace:
        - Muestra todas las prácticas que el afiliado usó.
        - Incluye fecha, prestador, costo, cobertura y copago.
        - Ordenado de más reciente a más antiguo.

        Cuándo usarla:
        - Cuando el afiliado pregunta "¿Qué prácticas usé?"
        - Para revisar consumos previos.
        - Para verificar detalles de facturas.

        Cómo comunicarlo al usuario:
        • "Acá está tu historial de consumos."
        • "La práctica más reciente fue [nombre] el [fecha]."
        • "En total tenés X consumos registrados."

        Parámetros:
        - afiliado_id (int): ID del afiliado.
        - limit (int): Cantidad de registros a mostrar (por defecto 50).
        - offset (int): Desplazamiento para paginación (por defecto 0).

        Retorna:
        - str: JSON con lista de consumos (fecha, practica_nombre, prestador, costo, cobertura, copago).
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
                    return obj.isoformat()
                if isinstance(obj, dict):
                    return {k: _serial(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_serial(i) for i in obj]
                return obj

            return json.dumps(_serial(resultado), ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error al consultar historial de consumos: {e}")