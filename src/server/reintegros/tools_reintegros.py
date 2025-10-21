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

from bd.baseModels import ReglamentoReintegro
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
    
    @mcp.tool("iniciar_reintegro")
    async def iniciar_reintegro() -> ReglamentoReintegro:
        '''
        Muestra el reglamento oficial de reintegros de OSEP.

        Cuándo usarla:
        - Cuando el afiliado menciona "reintegro" por primera vez.
        - Cuando pregunta "¿Qué necesito para un reintegro?"
        - Cuando tiene dudas sobre qué puede solicitar.
        - Antes de iniciar cualquier reintegro (ofrecerlo SIEMPRE).

        Cómo comunicarlo al usuario:
        PREGUNTÁ SIEMPRE antes de mostrar:
        • "¿Querés que te muestre el reglamento de reintegros primero?"
        • "¿Necesitás conocer los requisitos antes de empezar?"
        
        Después de mostrar el reglamento:
        • "Acá tenés el reglamento completo de reintegros."
        • "¿Tenés alguna duda sobre los requisitos?"
        • "¿Querés que te ayude a iniciar tu reintegro ahora?"

        Qué devuelve:
        - El texto completo del reglamento en formato Markdown.
        - NO mostrar detalles técnicos al usuario.
        - Presentarlo de forma clara y legible.

        Reglas para el asistente:
        - 🔴 SIEMPRE ofrecer ver el reglamento antes de crear_reintegro.
        - ✅ Preguntar primero, no asumir que el usuario lo quiere ver.
        - ✅ Después de mostrarlo, esperar confirmación para continuar.
        '''
        try:
            import os
            # Obtener la ruta de este archivo (tools_reintegros.py)
            # que está en: src/server/reintegros/tools_reintegros.py
            base_dir = os.path.dirname(__file__)
            
            # Subir dos niveles para llegar a src/ y luego ir a static/
            # Desde: src/server/reintegros/ -> src/server/ -> src/ -> src/static/
            ruta = os.path.normpath(os.path.join(base_dir, '../../static/reglamento_reintegro.md'))
            
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                
            reglamento = ReglamentoReintegro(
                titulo="Reglamento de Reintegro",
                contenido_md=contenido,
                formato='md',
                ruta_local=ruta
            )
            return reglamento
        except Exception as e:
            raise Exception(f"Error leyendo reglamento: {e}")

    @mcp.tool(name="crear_reintegro_inicial")
    async def crear_reintegro(ctx: Context[ServerSession, "AppContext"], afiliado_id: int, cbu: int) -> int:
        '''
        Inicia un nuevo reintegro para el afiliado.

        ⚠️ IMPORTANTE - Flujo OBLIGATORIO antes de ejecutar esta tool:
        
        1. PRIMERO: Ofrecer mostrar el reglamento
           • "Antes de empezar, ¿querés que te muestre el reglamento de reintegros?"
           • Si dice que sí → llamar a iniciar_reintegro()
           • Si dice que no → continuar con paso 2
        
        2. SEGUNDO: Confirmar datos del afiliado
           • Verificar que tenés el afiliado_id correcto
           • Si no lo tenés, obtenerlo primero
        
        3. TERCERO: Crear el reintegro
           • Llamar a esta herramienta
           • Guardar el reintegro_id retornado
        
        4. DESPUÉS: Agregar ítems
           • Llamar a agregar_item_a_reintegro (una o varias veces)
           • Necesitás al menos 1 ítem antes de continuar
        
        5. FINALMENTE: Activar formulario de adjuntos
           • Llamar a adjuntar_documentos_a_reintegro
           • ⚠️ SOLO cuando ya haya ítems cargados

        Cómo comunicarlo al usuario:
        Antes de crear:
        • "Perfecto, voy a iniciar tu reintegro."
        
        Después de crear:
        • "Reintegro iniciado. Ahora necesito que me digas qué querés incluir."
        • NO mostrar el reintegro_id técnico al usuario.

        Parámetros:
        - afiliado_id (int): ID del afiliado que solicita el reintegro.
        - cbu (int): CBU donde se realizará el reintegro.

        Retorna:
        - int: ID del reintegro creado (usarlo internamente, no mostrarlo).

        Estado inicial:
        - El reintegro queda en estado PENDIENTE.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            reintegro_id = await utils_reintegros.create_temp_reintegro(db.conn, afiliado_id)
            return reintegro_id
        except Exception as e:
            raise Exception(f"Error al iniciar reintegro: {str(e)}")

    @mcp.tool(name="agregar_item_a_reintegro")
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
        Agrega un ítem (Práctica o Medicamento) a un reintegro existente.

        Descripción:
        - Inserta un ítem en el reintegro creado con `iniciar_reintegro`.
        - Podés llamar esta herramienta varias veces para cargar múltiples ítems.

        Flujo para el LLM (estricto):
        1) Asegurate de tener `reintegro_id` (devuelto por `iniciar_reintegro`).
        2) Si `tipo == 'P'` (Práctica), **requerido** `practica_id`.
        3) Si `tipo == 'M'` (Medicamento), **requerido** `medicamento_id`.
        4) Repetir hasta cargar todos los ítems necesarios.
        5) Cuando haya al menos **1 ítem**, llamar a `mcp_obra_social_adjuntar_documentos_a_reintegro` para que el afiliado adjunte PDFs y complete el envío desde la UI.

        Parámetros:
        - reintegro_id (int): ID del reintegro al que se agrega el ítem.
        - tipo (str): 'P' = práctica, 'M' = medicamento.
        - fecha_prestacion (date): Fecha de la prestación (YYYY-MM-DD).
        - monto_presentado (float): Monto presentado del ítem.
        - practica_id (Optional[int]): Requerido si `tipo == 'P'`.
        - medicamento_id (Optional[int]): Requerido si `tipo == 'M'`.

        Retorna:
        - int: `item_id` del ítem agregado.

        Validaciones esperadas:
        - Debe existir el `reintegro_id`.
        - `tipo` solo puede ser 'P' o 'M'.
        - Para la demo, no se validan duplicados; si el usuario lo pide, se pueden agregar varios ítems similares.
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

    @mcp.tool(name="adjuntar_documentos_a_reintegro")
    async def adjuntar_documentos_a_reintegro(ctx: Context[ServerSession, "AppContext"], reintegro_id: int) -> str:
        '''
        Activa el formulario de carga de comprobantes para que el usuario finalice el reintegro.

        Cuándo usarla
        - Solo cuando el reintegro ya tiene al menos un ítem cargado.
        - ⚠️ SIEMPRE preguntar al usuario antes de llamar a esta herramienta.

        Qué hace
        - Pone el trámite en estado "esperando comprobantes".
        - Activa el formulario donde el usuario puede subir 1–2 archivos PDF.
        - El formulario se abrirá automáticamente en la interfaz del usuario.

        Cómo comunicarlo al usuario (texto claro y breve)
        Antes de llamar a esta tool, PREGUNTÁ:
        • "¿Querés que active el formulario para subir los comprobantes ahora?"
        • "¿Estás listo para adjuntar los documentos?"
        
        Después de activar el formulario:
        • "Activé el formulario para que subas hasta 2 comprobantes (PDF)."
        • "Al finalizar, presioná 'Enviar reintegro' para cerrar el trámite."
        • ⚠️ "Importante: una vez enviado, el reintegro queda cerrado y no se puede modificar."

        Reglas clave para el asistente
        - 🔴 OBLIGATORIO: Preguntar SIEMPRE antes de ejecutar esta herramienta.
        - ❌ No existe una herramienta para finalizar desde acá: el envío final ocurre únicamente en el formulario.
        - ✅ Después de activar el formulario, no llames más tools en este flujo.
        - ✅ Tras el envío desde la UI, el reintegro pasa a ENVIADO y ya no admite cambios (ni ítems, ni montos, ni adjuntos).

        Qué le tenés que pasar (internamente, sin decirlo al usuario)
        - La referencia interna del reintegro (no la muestres).

        Qué te devuelve
        - Confirmación de que el formulario fue activado (no mostrar los detalles técnicos al usuario).
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            
            # Usar la función de utilidad para actualizar el estado del reintegro
            success = await utils_reintegros.add_docs_reintegro(db.conn, reintegro_id)
            
            if not success:
                raise Exception(f"No se pudo actualizar el reintegro con ID {reintegro_id}")
            
            # Retornar:
            import json
            return json.dumps({
                "accion": "activar_form_reintegro",
                "reintegro_id": reintegro_id,
                "url": f"http://localhost:8000/reintegros/{reintegro_id}"
            })
            
        except Exception as e:
            raise Exception(f"Error en tool.adjuntar_documentos_a_reintegro: {e}")
        
    @mcp.tool(name="listar_reintegros_afiliado")
    async def listar_reintegros_afiliado(
        ctx: Context[ServerSession, "AppContext"],
        afiliado_id: int,
        fecha_desde: date,
        fecha_hasta: date
    ) -> str:
        '''
        Lista reintegros para un afiliado dentro de un rango de fechas (inclusive).

        Instrucciones para el LLM que use esta herramienta:
        - Pedir siempre al usuario el RANGO de fechas en formato YYYY-MM-DD:
          "Por favor indicá fecha desde (YYYY-MM-DD) y fecha hasta (YYYY-MM-DD)."
        - Si el usuario NO puede dar un rango pero aporta UNA fecha estimada,
          pedir: "Si solo tenés una fecha estimada, indicámela (YYYY-MM-DD) y yo usaré ese día ±5 días."
          En ese caso construir el rango automáticamente restando 5 días a la fecha estimada para `fecha_desde`
          y sumando 5 días para `fecha_hasta`.
        - Validar el formato de la(s) fecha(s) antes de llamar a la tool.
        - Confirmar con el usuario el rango final que se usará:
          "Voy a buscar reintegros desde {fecha_desde} hasta {fecha_hasta}. ¿Continuo?"
        - Solo llamar esta herramienta cuando el usuario confirme el rango.

        Parámetros:
        - afiliado_id (int): ID del afiliado.
        - fecha_desde (date): Fecha inicial (inclusive).
        - fecha_hasta (date): Fecha final (inclusive).

        Retorna:
        - str: JSON con la lista de reintegros y sus detalles.

        Notas:
        - El formato de fecha es YYYY-MM-DD.
        - Si no hay reintegros, retorna una lista vacía.
        '''
        try:
            import json
            from decimal import Decimal
            from datetime import date, datetime

            # Llamada directa a la utilidad; asumimos que las fechas vienen ya en el formato esperado.
            db = ctx.request_context.lifespan_context.db
            reintegros = await utils_reintegros.list_reintegros_por_afiliado_y_rango(
                db.conn, afiliado_id, fecha_desde, fecha_hasta
            )

            # Conversión simple y recursiva para que json.dumps pueda serializar Decimals y fechas.
            def _serial(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                if isinstance(obj, (date, datetime)):
                    return obj.isoformat()
                if isinstance(obj, dict):
                    return {k: _serial(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_serial(i) for i in obj]
                return obj

            return json.dumps(_serial(reintegros))
        except Exception as e:
            raise Exception(f"Error al listar reintegros del afiliado: {str(e)}")
        
    @mcp.tool(name="generar_nota_reintegro")
    async def generar_nota_reintegro(
        ctx: Context[ServerSession, "AppContext"],
        motivo: str,
        numero_afiliado: str
    ) -> str:
        '''
        Genera una nota formal dirigida al Director/a de OSEP para solicitudes de reintegro.

        Instrucciones para el LLM (IMPORTANTE):
        Antes de llamar a esta herramienta, SIEMPRE preguntar al afiliado:
        1. ¿En qué lugar se realizó la prestación? (ciudad, clínica, hospital, etc.)
        2. ¿En qué fecha fue la prestación? (formato DD/MM/YYYY)
        3. ¿Quién fue el prestador? (nombre del médico, profesional o institución)
        4. ¿Cuál es el motivo de la solicitud? (qué necesita autorizar o reintegrar)

        Luego, construir el texto del motivo con esta estructura OBLIGATORIA:
        
        "Me dirijo a usted con el fin de [solicitud específica del afiliado]. La prestación fue realizada en [lugar] el día [fecha] por [prestador]. Adjunto los comprobantes y documentación requerida."

        Ejemplo completo:
        "Me dirijo a usted con el fin de solicitar el reintegro de una consulta médica especializada. La prestación fue realizada en Clínica San Martín, Mendoza, el día 15/10/2024 por el Dr. Juan Pérez. Adjunto los comprobantes y documentación requerida."

        Parámetros:
        - motivo (str): Texto completo de la nota siguiendo la estructura indicada arriba.
        - numero_afiliado (str): Número de carné del afiliado titular.

        Salida:
        - Devuelve la URL completa para descargar la nota generada en PDF.
        '''
        try:
            import json
            import httpx
            
            # Preparar el body del POST
            payload = {
                "motivo": motivo,
                "afiliado_numero": numero_afiliado
            }
            
            # Hacer la llamada POST a la API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/reintegros/generar-nota",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            # Devolver siempre JSON serializado (string) para el flujo de herramientas
            return json.dumps(result)
        except Exception as e:
            raise Exception(f"Error en tool.generar_nota_reintegro: {e}")

