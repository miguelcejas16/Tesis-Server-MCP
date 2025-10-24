from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from datetime import date
import sys
from pathlib import Path
from typing import TYPE_CHECKING

root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))

from bd.baseModels import Reglamento  # Usar el mismo modelo base
if TYPE_CHECKING:
    from ..server import AppContext

from . import utils_afiliaciones

def register_afiliacion_tools(mcp: FastMCP):
    '''
     * Registra todas las herramientas relacionadas con afiliaciones en la instancia del servidor MCP.
     * Parámetros:
     *   mcp (FastMCP) — La instancia principal del servidor FastMCP.
     * Retorna:
     *   None
    '''
    
    @mcp.tool("iniciar_afiliacion")
    async def iniciar_afiliacion() -> Reglamento:
        '''
        Muestra el reglamento oficial de afiliaciones de la obra social MCP.

        Cuándo usarla:
        - Cuando el usuario menciona "afiliarme" o "afiliación" por primera vez.
        - Cuando pregunta "¿Qué necesito para afiliarme?"
        - Cuando tiene dudas sobre requisitos de afiliación.
        - Antes de iniciar cualquier solicitud de afiliación (ofrecerlo SIEMPRE).

        Cómo comunicarlo al usuario:
        PREGUNTÁ SIEMPRE antes de mostrar:
        • "¿Querés que te muestre el reglamento de afiliación primero?"
        • "¿Necesitás conocer los requisitos antes de empezar?"
        
        Después de mostrar el reglamento:
        • "Acá tenés el reglamento completo de afiliación."
        • "¿Tenés alguna duda sobre los requisitos?"
        • "¿Querés que te ayude a iniciar tu solicitud de afiliación ahora?"

        Qué devuelve:
        - El texto completo del reglamento en formato Markdown.
        - NO mostrar detalles técnicos al usuario.
        - Presentarlo de forma clara y legible.

        Reglas para el asistente:
        - 🔴 SIEMPRE ofrecer ver el reglamento antes de crear_afiliacion.
        - ✅ Preguntar primero, no asumir que el usuario lo quiere ver.
        - ✅ Después de mostrarlo, esperar confirmación para continuar.
        '''
        try:
            import os
            base_dir = os.path.dirname(__file__)
            ruta = os.path.normpath(os.path.join(base_dir, '../../static/reglamento_afiliacion.md'))
            
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()

            reglamento = Reglamento(
                titulo="Reglamento de Afiliación",
                contenido_md=contenido,
                formato='md',
                ruta_local=ruta
            )
            return reglamento
        except Exception as e:
            raise Exception(f"Error leyendo reglamento de afiliación: {e}")

    @mcp.tool(name="crear_afiliacion_inicial")
    async def crear_afiliacion(
        ctx: Context[ServerSession, "AppContext"],
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
        '''
        Inicia una nueva solicitud de afiliación.

        ⚠️ IMPORTANTE - Flujo OBLIGATORIO antes de ejecutar esta tool:
        
        1. PRIMERO: Ofrecer mostrar el reglamento
           • "Antes de empezar, ¿querés que te muestre el reglamento de afiliación?"
           • Si dice que sí → llamar a iniciar_afiliacion()
           • Si dice que no → continuar con paso 2
        
        2. SEGUNDO: Recopilar datos del solicitante
           • Pedir todos los datos requeridos
           • Validar que estén completos
        
        3. TERCERO: MOSTRAR RESUMEN Y PEDIR CONFIRMACIÓN FINAL
           • Mostrar TODOS los datos ingresados de forma clara
           • "Revisá tus datos antes de confirmar:"
           • Listar todos los datos completos
           • "⚠️ IMPORTANTE: Una vez confirmado, NO se pueden modificar los datos."
           • "¿Confirmás que todos los datos son correctos y querés crear la solicitud?"
           • ESPERAR confirmación explícita del usuario
        
        4. CUARTO: Crear la afiliación
           • SOLO después de la confirmación → llamar a esta herramienta
           • Guardar el afiliacion_id retornado y muestraselo al usuario, pidiendo que lo recuerde y lo anote en algun lugar.
        
        5. FINALMENTE: Activar formulario de adjuntos
           • Llamar a adjuntar_documentos_a_afiliacion
           • ⚠️ SOLO cuando todos los datos estén completos

        Cómo comunicarlo al usuario:
        Antes de crear:
        • "Perfecto, voy a crear tu solicitud de afiliación con los datos confirmados."
        
        Después de crear:
        • "✅ Solicitud creada exitosamente. Ahora necesitás adjuntar la documentación requerida."
        • NO mostrar el afiliacion_id técnico al usuario.

        Parámetros:
        - nombre_apellido (str): Nombre completo del solicitante.
        - dni (int): DNI del solicitante.
        - fecha_nacimiento (date): Fecha de nacimiento (YYYY-MM-DD).
        - domicilio_calle (str): Calle del domicilio.
        - domicilio_numero (str): Número del domicilio.
        - localidad (str): Localidad.
        - provincia (str): Provincia.
        - telefono (str): Teléfono de contacto.
        - email (str): Email de contacto.
        - tipo_afiliado (str): Tipo (EMPLEADO, MONOTRIBUTISTA, JUBILADO, PARTICULAR).

        Retorna:
        - int: ID de la afiliación creada (usarlo internamente, no mostrarlo).

        Estado inicial:
        - La afiliación queda en estado PENDIENTE.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            afiliacion_id = await utils_afiliaciones.create_afiliacion(
                db.conn,
                nombre_apellido,
                dni,
                fecha_nacimiento,
                domicilio_calle,
                domicilio_numero,
                localidad,
                provincia,
                telefono,
                email,
                tipo_afiliado
            )
            return afiliacion_id
        except Exception as e:
            raise Exception(f"Error al iniciar afiliación: {str(e)}")

    @mcp.tool(name="adjuntar_documentos_a_afiliacion")
    async def adjuntar_documentos_a_afiliacion(
        ctx: Context[ServerSession, "AppContext"],
        afiliacion_id: int
    ) -> str:
        '''
        Activa el formulario de carga de documentos para que el usuario finalice la afiliación.

        Cuándo usarla:
        - Solo cuando la solicitud ya tiene todos los datos cargados.
        - ⚠️ SIEMPRE preguntar al usuario antes de llamar a esta herramienta.

        Qué hace:
        - Pone la solicitud en estado "esperando documentos".
        - Activa el formulario donde el usuario puede subir los documentos requeridos (PDF).
        - El formulario se abrirá automáticamente en la interfaz del usuario.

        Cómo comunicarlo al usuario (texto claro y breve):
        Antes de llamar a esta tool, PREGUNTÁ:
        • "¿Querés que active el formulario para subir los documentos ahora?"
        • "¿Estás listo para adjuntar la documentación requerida?"
        
        Después de activar el formulario:
        • "Activé el formulario para que subas los documentos requeridos (PDF)."
        • "Al finalizar, presioná 'Enviar solicitud' para cerrar el trámite."
        • ⚠️ "Importante: una vez enviado, la solicitud queda cerrada y no se puede modificar."

        Reglas clave para el asistente:
        - 🔴 OBLIGATORIO: Preguntar SIEMPRE antes de ejecutar esta herramienta.
        - ❌ No existe una herramienta para finalizar desde acá: el envío final ocurre únicamente en el formulario.
        - ✅ Después de activar el formulario, no llames más tools en este flujo.
        - ✅ Tras el envío desde la UI, la afiliación pasa a ENVIADO y ya no admite cambios.

        Qué le tenés que pasar (internamente, sin decirlo al usuario):
        - La referencia interna de la afiliación (no la muestres).

        Qué te devuelve:
        - Confirmación de que el formulario fue activado (no mostrar los detalles técnicos al usuario).
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            
            success = await utils_afiliaciones.add_docs_afiliacion(db.conn, afiliacion_id)
            
            if not success:
                raise Exception(f"No se pudo actualizar la afiliación con ID {afiliacion_id}")
            
            import json
            return json.dumps({
                "accion": "activar_form_afiliacion",
                "afiliacion_id": afiliacion_id,
                "url": f"http://localhost:8000/afiliaciones/{afiliacion_id}"
            })
            
        except Exception as e:
            raise Exception(f"Error en tool.adjuntar_documentos_a_afiliacion: {e}")
        
    @mcp.tool(name="mostrar_afiliacion")
    async def mostrar_afiliacion(
        ctx: Context[ServerSession, "AppContext"],
        afiliacion_id: int,
        dni: int
    ) -> str:
        '''
        Muestra los detalles de una afiliación específica.

        Instrucciones para el LLM que use esta herramienta:
        - Pedir siempre al usuario el ID de la afiliación y el DNI en formato numérico.
        - Validar el formato de los parámetros antes de llamar a la tool.
        - Confirmar con el usuario el ID y DNI que se usarán:
          "Voy a buscar la afiliación con ID {afiliacion_id} y DNI {dni}. ¿Continuo?"
        - Solo llamar esta herramienta cuando el usuario confirme los parámetros.

        Parámetros:
        - afiliacion_id (int): ID de la afiliación.
        - dni (int): DNI del afiliado.

        Retorna:
        - str: JSON con la lista de afiliaciones y sus detalles.

        Notas:
        - El formato de fecha es YYYY-MM-DD.
        - Si no hay afiliaciones, retorna una lista vacía.
        '''
        try:
            import json
            from decimal import Decimal
            from datetime import date, datetime

            db = ctx.request_context.lifespan_context.db
            afiliaciones = await utils_afiliaciones.list_afiliaciones_por_id_y_dni(
                db.conn, afiliacion_id, dni
            )

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

            return json.dumps(_serial(afiliaciones))
        except Exception as e:
            raise Exception(f"Error al listar afiliaciones: {str(e)}")