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
    async def iniciar_afiliacion() -> dict:
        '''
            Muestra el reglamento oficial de afiliaciones de la obra social MCP.

            Cuándo usarla:
            - Cuando el usuario menciona "afiliación", "afiliar", "afiliarme", "alta", "inscripción".
            - Cuando pregunta por requisitos, condiciones o documentación para afiliarse.
            - SIEMPRE antes de iniciar una solicitud de afiliación.
            - No depende de si el usuario está identificado o no en la conversación.

            Comportamiento obligatorio del asistente (NO OPCIONAL):
            - 🔴 Al ejecutar esta herramienta, el asistente DEBE MOSTRAR AL USUARIO el contenido informativo devuelto.
            - 🔴 El reglamento es de visualización OBLIGATORIA y NO PUEDE SER OMITIDO, RESUMIDO NI REEMPLAZADO.
            - 🔴 Está PROHIBIDO iniciar, continuar o simular una afiliación sin haber mostrado previamente este contenido.
            - 🔴 NO preguntar si desea ver el reglamento.
            - El trámite de afiliación siempre se considera para un TITULAR (tercero).
            - No reutilizar datos de trámites o identificaciones previas del chat.

            Regla crítica de presentación (FORZANTE):
            - 🔴 El asistente DEBE RENDERIZAR ÍNTEGRAMENTE el contenido devuelto por la herramienta.
            - 🔴 NO interpretar, NO sintetizar, NO resumir, NO reescribir, NO seleccionar partes.
            - 🔴 El contenido cumple una función legal e informativa obligatoria.
            - 🔴 Si el contenido excede el límite de un mensaje, el asistente DEBE continuar en mensajes consecutivos hasta completarlo.

            Cómo comunicarlo al usuario (ORDEN OBLIGATORIO):
            1) Mostrar el reglamento completo y el aviso de privacidad.
            2) Luego mostrar exactamente, sin modificaciones, los siguientes mensajes:
            - "Este trámite es para un titular. Completá los datos solo si contás con su autorización."
            - "¿Querés iniciar la solicitud de afiliación ahora?"

            Qué devuelve la herramienta:
            - Un objeto estructurado (dict/JSON) que contiene:
            - Reglamento de afiliación vigente.
            - Aviso de tratamiento de datos personales (Ley N.º 25.326).
            - Reglas básicas de seguridad del trámite.
            - 🔴 El asistente NO debe mostrar claves técnicas ni explicar la estructura interna del objeto.
            - 🔴 El contenido devuelto es material de presentación directa al usuario.

            Reglas de seguridad:
            - No confirmar la existencia de afiliaciones previas.
            - No validar ni cruzar datos con información del contexto conversacional.
            - No inferir estado de afiliación a partir de mensajes previos.
            - El reglamento y el aviso de privacidad cumplen una función informativa obligatoria y no negociable.
            '''

        try:
            reglamento = {
                            "doc_type": "afiliacion_reglamento_v2",
                            "version": "2025-12-13",
                            "scope": {
                                "solo_titular": True,
                                "sin_grupo_familiar": True
                            },
                            "privacy_notice": {
                                "responsable": "Obra Social MCP",
                                "finalidad": "Tramitar una solicitud de afiliación como titular y su revisión por la obra social.",
                                "datos_recolectados": [
                                "Nombre y apellido",
                                "DNI/CUIL",
                                "Fecha de nacimiento",
                                "Domicilio",
                                "Localidad/Provincia",
                                "Teléfono",
                                "Email",
                                "Tipo de afiliado",
                                "Documentación respaldatoria (PDF/imagen)"
                                ],
                                "uso": "Los datos se utilizarán únicamente para gestionar esta solicitud de afiliación y su evaluación por la obra social. No se utilizarán para finalidades distintas a esta gestión.",
                                "obligatoriedad_y_consecuencia": "Los datos y documentos solicitados son obligatorios para evaluar la afiliación. La falta de información o documentación puede impedir la tramitación o demorar la revisión.",
                                "derechos": "El titular de los datos puede ejercer los derechos de acceso, rectificación, actualización o supresión por los canales oficiales de la obra social, conforme a la Ley N.º 25.326."
                            },
                            "agent_policy": {
                                "identidad": {
                                "no_reutilizar_contexto_afiliado": True,
                                "siempre_tercero_titular": True,
                                "mensaje_obligatorio_autorizacion": "Vas a cargar datos personales de un tercero. Completá la solicitud solo si contás con su autorización."
                                },
                                "minimizacion": {
                                "no_pedir_datos_de_salud": True,
                                "no_pedir_datos_extra": True
                                },
                                "seguridad": {
                                "no_confirmar_existencia_por_dni": True,
                                "no_confirmar_existencia_por_numero_solicitud": True,
                                "no_mostrar_adjuntos_en_seguimiento": True
                                },
                                "seguimiento_por_numero": {
                                "sin_verificacion": "respuesta_neutra",
                                "respuesta_neutra_texto": "Si el número es válido, la solicitud podría estar en revisión. Para ver el estado exacto necesito validar al titular.",
                                "con_verificacion": "permitir_estado_basico"
                                },
                                "cancelacion": {
                                "permitir_cancelar_borrador": True,
                                "permitir_desistir_enviada": True,
                                "texto_desistimiento": "Puedo registrar tu desistimiento, pero la solicitud ya enviada no se edita. La obra social la cerrará administrativamente."
                                }
                            },
                            "reglamento": {
                                "objeto": "Requisitos y condiciones para solicitar afiliación como titular.",
                                "condiciones_generales": [
                                "La solicitud es una declaración jurada digital y puede requerir verificación adicional.",
                                "Los datos y documentos deben ser verídicos, legibles y actuales.",
                                "La aprobación no es automática; la obra social puede solicitar información adicional o rechazar la solicitud.",
                                "Proceso 100% digital."
                                ],
                                "requisitos_titular": [
                                "Mayor de 18 años",
                                "DNI vigente",
                                "Completar datos personales obligatorios",
                                "Seleccionar tipo de afiliado"
                                ],
                                "documentacion_por_tipo": {
                                "EMPLEADO": ["DNI", "Último recibo de sueldo"],
                                "MONOTRIBUTISTA": ["DNI", "Constancia AFIP", "Último comprobante de pago"],
                                "JUBILADO": ["DNI", "Último recibo de haberes previsionales"],
                                "PARTICULAR": ["DNI", "Declaración jurada digital de ingresos"]
                                },
                                "validacion_aprobacion": [
                                "Estados: Pendiente de revisión / Aprobada / Rechazada.",
                                "La obra social podrá verificar datos con organismos oficiales.",
                                "La afiliación es efectiva una vez aprobada y asignado el número de afiliado."
                                ]
                            },
                            "ui_messages": {
                                "inicio": "Antes de iniciar, te muestro el reglamento de afiliación.",
                                "post_reglamento": "¿Querés iniciar la solicitud ahora?",
                                "pre_confirmacion": "Revisá el resumen. Si hay errores, volvé atrás antes de enviar. Una vez enviado no se edita.",
                                "post_creacion": "Solicitud creada. Ahora adjuntá la documentación requerida."
                            }
                            }

            return reglamento
            
        except Exception as e:
            raise Exception(f"Error leyendo reglamento de afiliación: {e}")

    @mcp.tool(name="crear_afiliacion_inicial")
    async def crear_afiliacion(
        ctx: Context[ServerSession, "AppContext"],
        nombre_apellido: str,
        dni: int,
        fecha_nacimiento: date | str,
        domicilio_calle: str,
        domicilio_numero: str,
        localidad: str,
        provincia: str,
        telefono: str,
        email: str,
        tipo_afiliado: str
    ) -> int:
        '''
        Inicia una nueva solicitud de afiliación como TITULAR.

        ⚠️ REGLAS OBLIGATORIAS DEL FLUJO:

        1. REGLAMENTO (OBLIGATORIO Y PREVIO)
        - El asistente DEBE haber llamado a iniciar_afiliacion()
        - El reglamento debe haber sido mostrado completo al usuario
        - NO se permite iniciar la afiliación sin este paso

        2. IDENTIDAD DEL TRÁMITE
        - La afiliación SIEMPRE se considera para un TITULAR (tercero)
        - NO reutilizar datos de identificación previa del chat
        - NO asumir que el usuario del chat es el solicitante
        - El usuario carga los datos del titular a afiliar
        - La fecha de nacimiento siempre debes cargarla en formato date, NUNCA como string

        3. CARGA DE DATOS
        - Solicitar todos los datos requeridos del titular
        - Validar formato y completitud
        - No solicitar datos de salud ni información adicional no requerida

        4. RESUMEN Y CONFIRMACIÓN (OBLIGATORIO)
        - Mostrar TODOS los datos ingresados en forma clara
        - "Revisá los datos del titular antes de confirmar"
        - Advertir:
            "Una vez enviada, la solicitud no se puede modificar"
        - Esperar confirmación explícita del usuario

        5. CREACIÓN DE LA SOLICITUD
        - SOLO después de la confirmación
        - Ejecutar esta herramienta
        - El ID retornado es interno y NO debe mostrarse como dato técnico

        6. PASO SIGUIENTE
        - Luego de crear la solicitud:
            "Solicitud creada. Ahora necesitás adjuntar la documentación requerida."

        Cómo comunicarlo al usuario:
        - Antes:
        • "Voy a crear la solicitud de afiliación con los datos confirmados."
        - Después:
        • "Solicitud creada exitosamente. Continuemos con la carga de documentación."
        • No exponer identificadores técnicos ni estados internos.

        Parámetros:
        - Corresponden exclusivamente al TITULAR de la afiliación.

        Retorna:
        - int: ID interno de la solicitud de afiliación (uso interno del sistema).

        Estado inicial:
        - La solicitud queda en estado PENDIENTE.
        '''
        if isinstance(fecha_nacimiento, str):
            fecha_nacimiento = date.fromisoformat(fecha_nacimiento.strip().strip('"').strip("'"))

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
        • "SIEMPRE informa el numero de solicitud al usuario para le pueda hacer seguimiento."
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
        Consulta el estado de una solicitud de afiliación mediante validación por
        número de solicitud y DNI del titular.

        ⚠️ OBJETIVO DE SEGURIDAD:
        - Esta herramienta NO debe exponer información personal a terceros.
        - El número de solicitud por sí solo NO habilita acceso a información.
        - La validación SIEMPRE es por combinación (afiliacion_id + dni).

        COMPORTAMIENTO OBLIGATORIO DEL ASISTENTE (LLM):

        1. SOLICITUD DE DATOS
        - Pedir SIEMPRE:
            • Número de solicitud
            • DNI del titular
        - Mensaje obligatorio:
            "Para consultar el estado de una solicitud necesito el número de solicitud y el DNI del titular."

        2. VALIDACIÓN DE FORMATO
        - Verificar que ambos valores sean numéricos.
        - Si el formato es inválido, responder:
            "Verificá que el número de solicitud y el DNI estén ingresados correctamente."

        3. NO CONFIRMAR EXISTENCIA
        - NO indicar si el número de solicitud existe.
        - NO indicar si el DNI coincide parcialmente.
        - NO diferenciar tipos de error.

        4. LLAMADA A LA TOOL
        - Llamar a esta herramienta SOLO cuando:
            • Ambos valores estén presentes
            • Ambos valores tengan formato válido
        - NO pedir confirmaciones adicionales.
        - NO repetir los valores al usuario antes de llamar a la tool.

        5. RESPUESTA EN CASO DE ERROR (ÚNICA Y GENÉRICA)
        - Ante cualquier falla, responder SIEMPRE:
            "No fue posible validar la solicitud con los datos ingresados. Verificá el número de solicitud y el DNI del titular, y volvé a intentar."

        6. RESPUESTA EN CASO DE ÉXITO
        - Mostrar ÚNICAMENTE:
            • Estado de la solicitud
        - Mensaje base obligatorio:
            "La solicitud fue validada correctamente."

        - Ejemplo:
            "La solicitud fue validada correctamente.
            Estado: Pendiente de revisión"

        7. INFORMACIÓN PROHIBIDA
        - NO mostrar:
            • fechas
            • datos personales adicionales
            • observaciones internas
            • documentación adjunta
            • motivos de rechazo
            • historial del trámite

        8. CIERRE OBLIGATORIO
        - Finalizar siempre con:
            "Si deseás saber más información, comunicate con la obra social por los canales oficiales."

        PARÁMETROS:
        - afiliacion_id (int): Número de solicitud de afiliación.
        - dni (int): DNI del titular de la solicitud.

        RETORNO:
        - str: JSON interno con el resultado de la validación.
        El asistente DEBE filtrar la respuesta y exponer solo el estado.
        '''
        try:
            import json
            from decimal import Decimal
            from datetime import date, datetime

            db = ctx.request_context.lifespan_context.db
            afiliaciones = await utils_afiliaciones.list_afiliaciones_por_id_y_dni(
                db.conn, afiliacion_id, dni
            )

            if afiliaciones is None:
                return f"No se pudo encontrar esa afiliacion, intente nuevamente."

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
    
    @mcp.tool(name="cancelar_reintegro")
    async def cancelar_reintegro(
        ctx: Context[ServerSession, "AppContext"],
        reintegro_id: int,
        afiliado_id: int
    ) -> str:
        '''
        Cancela un reintegro existente poniendo su estado en CANCELADO.

        Cuándo usarla:
        - Cuando el afiliado solicita cancelar un reintegro que aún no fue procesado.
        - Solo se pueden cancelar reintegros que pertenezcan al afiliado.
        - ⚠️ SIEMPRE confirmar con el usuario antes de cancelar.

        Cómo comunicarlo al usuario:
        Antes de llamar a esta tool, PREGUNTÁ:
        • "¿Estás seguro que querés cancelar el reintegro?"
        • "Una vez cancelado, no se puede revertir. ¿Confirmo la cancelación?"

        Después de cancelar:
        • "El reintegro fue cancelado exitosamente."
        • "Si necesitás hacer un nuevo reintegro, podés iniciarlo cuando quieras."

        Reglas para el asistente:
        - 🔴 OBLIGATORIO: Confirmar SIEMPRE antes de cancelar.
        - ✅ Validar que el reintegro pertenezca al afiliado.
        - ✅ Informar claramente que la acción es irreversible.

        Parámetros:
        - reintegro_id (int): ID del reintegro a cancelar.
        - afiliado_id (int): ID del afiliado dueño del reintegro.

        Retorna:
        - str: Mensaje de éxito o error.

        Notas:
        - Si el reintegro no existe o no pertenece al afiliado, retorna error.
        - La cancelación es definitiva y no puede revertirse.
        '''
        try:
            db = ctx.request_context.lifespan_context.db
            success = await utils_reintegros.cancelar_reintegro(db.conn, reintegro_id, afiliado_id)
            
            if not success:
                return f"No se pudo cancelar el reintegro. Verificá que el ID {reintegro_id} sea correcto y que te pertenezca."
            
            return f"Reintegro {reintegro_id} cancelado exitosamente."
        except Exception as e:
            raise Exception(f"Error al cancelar reintegro: {str(e)}")