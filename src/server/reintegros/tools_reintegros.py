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

from bd.baseModels import Reglamento
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
    async def iniciar_reintegro() -> dict:
        '''
        Devuelve el reglamento oficial de reintegros de la obra social MCP.

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
        - SIEMPRE ofrecer ver el reglamento antes de crear_reintegro.
        - Preguntar primero, no asumir que el usuario lo quiere ver.
        - Después de mostrarlo, esperar confirmación para continuar.

        Retorna:
        - dict: Contenido del reglamento.
        '''

        return {
            "documento": {
                "tipo": "Reglamento",
                "nombre": "Reglamento de Reintegros Médicos MCP",
                "formato_requerido": "Toda la documentación debe presentarse en formato PDF"
            },

            "marco_legal_obligatorio": {
                "jerarquia": "Norma rectora prioritaria",
                "descripcion_general": (
                    "El presente procedimiento se encuentra alcanzado por la normativa "
                    "de protección de datos personales y datos sensibles de salud, "
                    "resultando de cumplimiento obligatorio en todas las etapas del reintegro."
                ),
                "normativa_aplicable": [
                    {
                        "norma": "Ley 25.326 de Protección de los Datos Personales",
                        "tipo": "Ley nacional",
                        "caracter": "Cumplimiento obligatorio",
                        "ambito": "Tratamiento de datos personales y datos sensibles de salud",
                        "impacto_directo_en_el_procedimiento": [
                            "Tratamiento confidencial de los datos de salud",
                            "Limitación del acceso a datos a personal autorizado",
                            "Uso exclusivo de los datos para la gestión del reintegro",
                            "Prohibición de usos secundarios no autorizados",
                            "Garantía de los derechos del titular de los datos"
                        ]
                    }
                ],
                "obligacion_para_el_asistente": (
                    "Toda explicación, solicitud de datos o descripción del procedimiento "
                    "debe contextualizarse en el marco de la Ley 25.326, especialmente "
                    "cuando se trate información de salud."
                )
            },

            "procedimiento_operativo_de_reintegros": {
                "practicas_ambulatorias": {
                    "descripcion": "Reintegros vinculados a prácticas médicas realizadas en forma ambulatoria",
                    "requisitos": [
                        "Orden médica con diagnóstico emitida por profesional matriculado",
                        "Autorización previa cuando la práctica lo requiera según convenio",
                        "Informe o resultado de la prestación cuando corresponda",
                        "Factura original a nombre del afiliado titular firmada por el mismo",
                        "Fotocopia del DNI del afiliado"
                    ]
                },

                "medicamentos": {
                    "descripcion": "Reintegros vinculados a la adquisición de medicamentos",
                    "requisitos": [
                        "Receta médica con los datos del profesional prescriptor",
                        "Factura o ticket fiscal original",
                        "Troqueles o rótulos de los medicamentos adquiridos",
                        "Fotocopia del DNI del afiliado"
                    ]
                }
            },

            "plazo_de_presentacion": {
                "plazo": "60 días corridos",
                "computo": "Desde la fecha de emisión de la factura o de la receta médica",
                "consecuencia_del_incumplimiento": "La solicitud puede ser rechazada por presentación fuera de término"
            },

            "forma_de_pago": {
                "modalidad": "Transferencia bancaria",
                "destinatario": "Titular afiliado",
                "requisito": "CBU informado y validado del titular"
            },

            "tratamiento_de_datos_personales": {
                "categorias_de_datos": {
                    "datos_identificatorios": [
                        "Nombre y apellido",
                        "Tipo y número de documento",
                        "Número de afiliado",
                        "Datos de contacto"
                    ],
                    "datos_administrativos_y_economicos": [
                        "Información del plan de salud",
                        "Datos bancarios (CBU) del titular"
                    ],
                    "datos_de_salud": [
                        "Diagnóstico consignado en la orden médica o receta",
                        "Tipo de prestación médica",
                        "Fecha y lugar de la atención",
                        "Informes o resultados vinculados a la práctica o medicación"
                    ]
                },
                "caracter_de_los_datos": {
                    "datos_de_salud": "Datos sensibles que requieren protección reforzada"
                }
            },

            "finalidad_del_tratamiento": {
                "objetivos": [
                    "Recepcionar la solicitud de reintegro",
                    "Analizar y gestionar el trámite administrativo",
                    "Verificar el cumplimiento del reglamento",
                    "Efectuar el pago del reintegro correspondiente",
                    "Cumplir con obligaciones legales y regulatorias del sistema de salud"
                ],
                "limitacion_de_uso": "Los datos no podrán ser utilizados para finalidades distintas a las aquí establecidas"
            },

            "derechos_del_titular_de_los_datos": {
                "derechos_reconocidos": [
                    "Acceso a los datos personales",
                    "Rectificación de datos incorrectos",
                    "Actualización de la información",
                    "Supresión de los datos cuando corresponda",
                    "Información sobre el tratamiento de los datos"
                ],
                "canales_de_ejercicio": {
                    "correo_electronico": "obrasocialMCP@mcp.com",
                    "telefono": "3834-112233",
                    "atencion_presencial": {
                        "direccion": "Nuñez del Prado 666",
                        "horario": "Lunes a viernes de 7:00 a 13:00"
                    }
                }
            },

            "confidencialidad_y_acceso": {
                "acceso_a_los_datos": "Limitado exclusivamente a personal autorizado",
                "terceros": "Proveedores involucrados bajo deber de confidencialidad",
                "medidas_generales": [
                    "Confidencialidad reforzada",
                    "Acceso restringido",
                    "Uso conforme a finalidad declarada"
                ]
            }
        }


    @mcp.tool(name="crear_reintegro_inicial")
    async def crear_reintegro(ctx: Context[ServerSession, "AppContext"], afiliado_id: int, cbu: str) -> int:
        '''
        Inicia un nuevo reintegro para el afiliado usando su CBU registrado.

        ⚠️ REGLAS OBLIGATORIAS SOBRE EL CBU:
        
        1. NUNCA pedir un CBU al afiliado
        2. NUNCA aceptar un CBU que te ofrezcan
        3. SIEMPRE usar el CBU que está registrado en el sistema
        4. ANTES de ejecutar esta tool, MOSTRAR al afiliado su CBU registrado
        5. PEDIR confirmación explícita antes de crear el reintegro
        
        Cómo confirmar con el afiliado (OBLIGATORIO):
        Antes de llamar a esta tool, DECIR EXACTAMENTE:
        • "El reintegro se realizará al siguiente CBU registrado: [CBU completo]"
        • "¿Es correcto este CBU para continuar?"
        
        Si el afiliado dice que NO es correcto:
        • "Necesitás acercarte a la obra social para actualizar tu CBU."
        • "No puedo modificar el CBU desde acá."
        • NO crear el reintegro.
        
        Si el afiliado dice que SÍ es correcto:
        • Llamar a esta tool con el CBU registrado.
        • "Perfecto, voy a iniciar tu reintegro."

        INFORMA AL AFILIADO ANTES DE EJECUTAR. "Vamos a armar tu solicitud paso a paso. Podés agregar prácticas/medicamentos y luego adjuntar la documentación."

        ⚠️ FLUJO COMPLETO OBLIGATORIO:
        
        1. PRIMERO: Ofrecer mostrar el reglamento
           • "Antes de empezar, ¿querés que te muestre el reglamento de reintegros?"
           • Si dice que sí → llamar a iniciar_reintegro()
           • Si dice que no → continuar con paso 2
        
        2. SEGUNDO: Confirmar CBU registrado
           • Obtener el CBU del afiliado desde el sistema
           • Mostrar el CBU completo al afiliado
           • "El reintegro se realizará al siguiente CBU registrado: [CBU]"
           • "¿Es correcto este CBU para continuar?"
           • Esperar confirmación explícita
        
        3. TERCERO: Crear el reintegro
           • Solo si el afiliado confirmó el CBU
           • Llamar a esta herramienta
           • Guardar el reintegro_id retornado
        
        4. DESPUÉS: Agregar ítems
           • Llamar a agregar_item_a_reintegro (una o varias veces)
           • Necesitás al menos 1 ítem antes de continuar
        
        5. FINALMENTE: Activar formulario de adjuntos
           • Llamar a adjuntar_documentos_a_reintegro
           • ⚠️ SOLO cuando ya haya ítems cargados

        Parámetros:
        - afiliado_id (int): ID del afiliado que solicita el reintegro.
        - cbu (str): CBU registrado del afiliado (obtenido del sistema, NO del usuario).

        Retorna:
        - int: ID del reintegro creado (usarlo internamente, no mostrarlo).

        Estado inicial:
        - El reintegro queda en estado PENDIENTE.
        '''
        try:
            # Validación simple del CBU (22 dígitos)
            if cbu is None:
                raise ValueError("CBU requerido")
            cbu_clean = str(cbu).strip()
            if not cbu_clean.isdigit() or len(cbu_clean) != 22:
                raise ValueError("CBU inválido: debe ser una cadena de 22 dígitos")

            db = ctx.request_context.lifespan_context.db
            reintegro_id = await utils_reintegros.create_temp_reintegro(db.conn, afiliado_id, cbu)
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

        OBLIGATORIO - Avisar al usuario que tenga cuidado con los items que carga porque no hay vuelta atras.
        LUEGO DE USAR RECUERDA QUE ESTE TRANQUILO QUE PUEDE CANCELAR EL REINTEGRO SI SE EQUIVOCA.

        Flujo para el LLM (estricto):
        1) Asegurate de tener `reintegro_id` (devuelto por `iniciar_reintegro`).
        2) Si `tipo == 'P'` (Práctica), **requerido** `practica_id`.
        3) Si `tipo == 'M'` (Medicamento), **requerido** `medicamento_id`.
        4) Repetir hasta cargar todos los ítems necesarios.
        5) Cuando haya al menos **1 ítem**, llamar a `adjuntar_documentos_a_reintegro` para que el afiliado adjunte PDFs y complete el envío desde la UI.

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
        
    @mcp.tool(name="obtener_reintegro_por_id")
    async def obtener_reintegro_por_id(
        ctx: Context[ServerSession, "AppContext"],
        reintegro_id: int,
        afiliado_id: int
    ) -> str:
        '''
        Obtiene los detalles completos de un reintegro por su ID y afiliado.

        Parámetros:
        - reintegro_id (int): ID del reintegro a consultar.
        - afiliado_id (int): ID del afiliado dueño del reintegro.

        Retorna:
        - str: JSON con todos los detalles del reintegro, incluyendo ítems y estado.

        Notas:
        - Valida que el reintegro pertenezca al afiliado especificado.
        - Si no se encuentra el reintegro o no pertenece al afiliado, retorna un error descriptivo.
        '''
        try:
            import json
            db = ctx.request_context.lifespan_context.db
            reintegro = await utils_reintegros.get_reintegro_por_id(db.conn, reintegro_id, afiliado_id)
            
            if reintegro is None:
                return(f"Reintegro no encontrado o no pertenece al afiliado {afiliado_id}")
            
            return json.dumps(reintegro)
        except Exception as e:
            raise Exception(f"Error al obtener reintegro por ID: {str(e)}")
    
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


