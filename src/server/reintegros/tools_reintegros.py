from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from datetime import date
from typing import Optional

# Importar el tipo AppContext desde server.py para anotaciones
# Se usa 'if TYPE_CHECKING' para evitar importaciones circulares en runtime.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..server import AppContext

# Importar funciones de utilidad desde el módulo local
from . import utils_reintegros

def register_reintegro_tools(mcp: FastMCP):
    '''
     * Registra todas las herramientas relacionadas con reintegros en la instancia del servidor MCP.
     * Parámetros:
     *   mcp (FastMCP) — La instancia principal del servidor FastMCP.
     * Retorna:
     *   None
    '''
    
    @mcp.tool(name="mcp_obra_social_iniciar_reintegro")
    async def iniciar_reintegro(ctx: Context[ServerSession, "AppContext"], afiliado_id: int, total_presentado: float) -> int:
        '''
         * Inicia el proceso de un nuevo reintegro creando un "contenedor" temporal.
         *
         * Esta es la **primera herramienta** que se debe llamar para comenzar un reintegro. Crea un registro base en estado 'pendiente' al cual se le agregarán ítems (prácticas, medicamentos) posteriormente.
         *
         * Workflow para el LLM:
         * 1.  Usa esta herramienta para crear el reintegro temporal. Necesitas el `afiliado_id`. Si no lo tienes, búscalo primero con la herramienta `afiliado_por_dni`.
         * 2.  La herramienta devuelve un `reintegro_id`. **Guarda este ID**, es esencial para los siguientes pasos.
         * 3.  Usa el `reintegro_id` devuelto para llamar a la herramienta `agregar_item_a_reintegro` una o varias veces.
         * 4.  Una vez que todos los ítems han sido agregados, usa la herramienta `finalizar_reintegro` para enviarlo a revisión.
         *
         * Parámetros:
         *   afiliado_id (int) — El ID del afiliado que solicita el reintegro. Es un dato obligatorio.
         *   total_presentado (float) — Un monto inicial presentado. Puede ser 0.0 si los montos se agregarán con cada ítem.
         *
         * Retorna:
         *   int — El ID (`reintegro_id`) del reintegro temporal recién creado. Este ID es necesario para agregarle ítems.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            reintegro_id = await utils_reintegros.create_temp_reintegro(db.conn, afiliado_id, total_presentado)
            return reintegro_id
        except Exception as e:
            raise Exception(f"Error al iniciar reintegro: {str(e)}")

    @mcp.tool(name="mcp_obra_social_agregar_item_a_reintegro")
    async def agregar_item_a_reintegro(
        ctx: Context[ServerSession, "AppContext"],
        reintegro_id: int,
        tipo: str,
        fecha_prestacion: date,
        monto_presentado: float,
        practica_id: Optional[int] = None,
        medicamento_id: Optional[int] = None
    ) -> int:
        '''
         * Agrega un ítem (práctica o medicamento) a un reintegro temporal.
         *
         * Esta herramienta se usa para añadir detalles específicos al reintegro que se inició previamente con `iniciar_reintegro`. Cada llamada agrega un ítem individual.
         *
         * Workflow para el LLM:
         * 1. Asegúrate de tener el `reintegro_id` del reintegro temporal creado con `iniciar_reintegro`.
         * 2. Si agregas una práctica, primero usa la herramienta `get_id_practica_por_nombre` para obtener el `practica_id`.
         * 3. Si agregas un medicamento, asegúrate de tener su `medicamento_id`.
         * 4. Usa esta herramienta para agregar cada ítem al reintegro.
         * 5. La herramienta devuelve un `item_id` para cada ítem agregado.
         * 6. Repite este proceso para cada ítem que desees agregar.
         * 7. Una vez que todos los ítems han sido agregados, usa la herramienta `finalizar_reintegro`.
         *
         * Parámetros:
         *   reintegro_id (int) — El ID del reintegro temporal al que se le va a agregar el ítem.
         *   tipo (str) — Tipo de ítem, 'M' para medicamento o 'P' para práctica.
         *   fecha_prestacion (date) — Fecha en formato 'YYYY-MM-DD' cuando se realizó la prestación.
         *   monto_presentado (float) — Monto presentado para este ítem.
         *   practica_id (Optional[int]) — El ID de la práctica si el tipo es 'P'. Requerido si tipo es 'P'.
         *   medicamento_id (Optional[int]) — El ID del medicamento si el tipo es 'M'. Requerido si tipo es 'M'.
         *
         * Retorna:
         *   int — El ID (`item_id`) del ítem agregado al reintegro.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            item_id = await utils_reintegros.add_item_to_reintegro(
                db.conn,
                reintegro_id,
                tipo,
                practica_id,
                medicamento_id,
                fecha_prestacion,
                monto_presentado
            )
            return item_id
        except Exception as e:
            raise Exception(f"Error al agregar ítem al reintegro: {str(e)}")

    @mcp.tool(name="mcp_obra_social_finalizar_reintegro")
    async def finalizar_reintegro(ctx: Context[ServerSession, "AppContext"], reintegro_id: int) -> bool:
        '''
         * Finaliza un reintegro y lo envía a revisión.
         *
         * Esta es la **última herramienta** que se debe llamar en el flujo de un reintegro. Cambia el estado del reintegro de 'pendiente' a 'en_revision', indicando que ya no se pueden agregar más ítems.
         *
         * Workflow para el LLM:
         * 1.  Llama a esta herramienta únicamente después de haber agregado todos los ítems necesarios con `agregar_item_a_reintegro`.
         * 2.  Llama a esta herramienta solo cuando tenga archivos adjuntos listos para enviar (si es necesario).
         * 3.  Necesitas el `reintegro_id` que obtuviste al llamar a `iniciar_reintegro`.
         * 4.  Una vez ejecutada, el reintegro queda bloqueado y pasa al sistema de back-office para su procesamiento.
         *
         * Parámetros:
         *   reintegro_id (int) — El ID del reintegro que se va a finalizar.
         *
         * Retorna:
         *   bool — `True` si el reintegro se finalizó y envió a revisión correctamente, `False` en caso contrario.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            success = await utils_reintegros.commit_reintegro(db.conn, reintegro_id)
            return success
        except Exception as e:
            raise Exception(f"Error al finalizar el reintegro: {str(e)}")

    @mcp.tool(name="mcp_obra_social_adjuntar_documentos_a_reintegro")
    async def adjuntar_documentos_a_reintegro(ctx: Context[ServerSession, "AppContext"], reintegro_id: int) -> str:
        '''
         * Señal para adjuntar documentos a un reintegro.
         *
         * Esta herramienta marca un reintegro como "ESPERANDO_ADJUNTOS" y pone
         * `adjuntos_confirmados = FALSE` actualizando directamente la base de datos.
         * Luego devuelve un enlace para que el usuario pueda subir los documentos.
         *
         * Parámetros:
         *   reintegro_id (int) — ID del reintegro al que se le adjuntarán documentos.
         *
         * Retorna:
         *   str — Enlace para adjuntar documentos al reintegro.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            
            # Usar la función de utilidad para actualizar el estado del reintegro
            success = await utils_reintegros.add_docs_reintegro(db.conn, reintegro_id)
            
            if not success:
                raise Exception(f"No se pudo actualizar el reintegro con ID {reintegro_id}")
            
            # Devolver el enlace para adjuntar documentos
            return f"http://localhost:8501/?reintegro_id={reintegro_id}&open=adjuntos"
            
        except Exception as e:
            raise Exception(f"Error en tool.adjuntar_documentos_a_reintegro: {e}")