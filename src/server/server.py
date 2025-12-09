from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import Tool
from contextlib import asynccontextmanager
import asyncpg
import os
import sys
import logging
from dotenv import load_dotenv
from typing import Optional, Any, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar src al path para importaciones absolutas
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import buscar_afiliado_por_dni, buscar_practica_por_nombre,get_practicas_cubiertas
from bd.baseModels import Afiliado, Practica
from reintegros.tools_reintegros import register_reintegro_tools
from afiliaciones.tools_afiliaciones import register_afiliacion_tools
from comunicaciones.tools_comunicaciones import register_comunicacion_tools
from consultas.tools_consultas import register_consulta_tools

# Cargar variables de entorno
load_dotenv()

class Database:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    @classmethod
    async def connect(cls) -> "Database":
        try:
            logger.info(f"Intentando conectar a: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")
            logger.info(f"Base de datos: {os.getenv('DB_NAME')}")
            logger.info(f"Usuario: {os.getenv('DB_USER')}")
            
            conn = await asyncpg.connect(
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
            )
            logger.info("Conexión exitosa!")
            return cls(conn)
        except Exception as e:
            logger.error(f"Error específico: {e}")
            raise Exception(f"Error conectando a la base de datos: {e}")
    
    async def disconnect(self) -> None:
        await self.conn.close()

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    db = None
    try:
        db = await Database.connect()
        yield AppContext(db=db)
    except Exception as e:
        raise Exception(f"Error en el lifespan: {e}")
    finally:
        if db:
            await db.disconnect()


mcp = FastMCP("Obra Social Server", lifespan=app_lifespan)

# Registrar herramientas de reintegros
register_reintegro_tools(mcp)
register_afiliacion_tools(mcp)
register_comunicacion_tools(mcp)
register_consulta_tools(mcp)

# @mcp.tool()
# async def afiliado_por_dni(ctx: Context[ServerSession, AppContext], numero_afiliado: str, nro_doc: str) -> Optional[Afiliado]:
#     """
#     Busca un afiliado por tipo y número de documento
#     Args:
#         numero_afiliado (str): Número de afiliado
#         nro_doc (str): Número de documento
#     Returns:
#         Datos del afiliado, incluyendo su plan_id
#     """
#     try:
#         db = ctx.request_context.lifespan_context.db
#         resultado = await buscar_afiliado_por_dni(db.conn, numero_afiliado, nro_doc)
#         return resultado
#     except Exception as e:
#         raise Exception(f"Error al buscar afiliado: {str(e)}")

@mcp.tool()
async def solicitar_codigo_afiliado(ctx: Context[ServerSession, AppContext], numero_afiliado: str, nro_doc: str) -> str:
    """
    PASO 1: Solicita un código OTP para validar la identidad del afiliado.
    
    Esta es la PRIMERA herramienta que debes usar cuando el usuario pida ver sus datos o tu necesites los datos del afiliado.
    
    Flujo para el LLM:
    1. Cuando el usuario pida "ver mis datos", "mi cobertura", "mis reintegros", etc.
    2. PRIMERO pide al usuario su número de afiliado y número de documento.
    3. Llama a esta herramienta con esos datos.
    4. Informa al usuario: "Te envié un código de 6 dígitos al email registrado. Por favor, escribí el código aquí."
    5. Espera a que el usuario proporcione el código.
    6. Luego usa la herramienta 'datos_afiliado_verificados' con el código.
    
    Args:
        numero_afiliado (str): Número de afiliado
        nro_doc (str): Número de documento
    
    Returns:
        str: Mensaje confirmando que se envió el código por email
    """
    try:
        from utils import generar_codigo_otp, guardar_otp, enviar_email
        
        db = ctx.request_context.lifespan_context.db
        
        # 1. Verificar que el afiliado existe
        afiliado = await buscar_afiliado_por_dni(db.conn, numero_afiliado, nro_doc)
        if not afiliado:
            return "No se encontró un afiliado con esos datos"
        
        # 2. Generar código OTP
        codigo = generar_codigo_otp()
        
        # 3. Guardar el código en la base de datos
        await guardar_otp(db.conn, numero_afiliado, nro_doc, codigo)
        
        # 4. Enviar código por email
        asunto = "Código de verificación - Obra Social"
        cuerpo = f"Hola {afiliado.nombre},\n\nTu código de verificación es: {codigo}\n\nEste código expira en 5 minutos."
        enviar_email(afiliado.email, asunto, cuerpo)
        
        # 5. Retornar mensaje genérico
        return f"Se ha enviado un código de verificación al email registrado para el afiliado {numero_afiliado}"
        
    except Exception as e:
        raise Exception(f"Error al solicitar código: {str(e)}")

@mcp.tool()
async def datos_afiliado_verificados(ctx: Context[ServerSession, AppContext], numero_afiliado: str, nro_doc: str, codigo: str) -> Afiliado:
    """
    PASO 2: Verifica el código OTP y retorna los datos del afiliado.
    
    Esta herramienta se usa DESPUÉS de 'solicitar_codigo_afiliado' cuando el usuario ya proporcionó el código de 6 dígitos.
    
    Flujo para el LLM:
    1. Solo usar esta herramienta DESPUÉS de que el usuario proporcione el código OTP.
    2. Usa los MISMOS datos (numero_afiliado y nro_doc) que usaste en 'solicitar_codigo_afiliado'.
    3. Si la verificación es exitosa, muestra los datos del afiliado al usuario.
    4. Si falla, informa: "El código es inválido, expiró o ya fue utilizado. Por favor, solicitá un nuevo código."
    
    Args:
        numero_afiliado (str): Número de afiliado (el mismo usado en solicitar_codigo_afiliado)
        nro_doc (str): Número de documento (el mismo usado en solicitar_codigo_afiliado)
        codigo (str): Código OTP de 6 dígitos proporcionado por el usuario
    
    Returns:
        Afiliado: Datos completos del afiliado verificado (nombre, apellido, email, plan, cbu, etc.)
    """
    try:
        from utils import obtener_otp_valido
        
        db = ctx.request_context.lifespan_context.db
        
        # 1. Verificar código OTP
        otp_valido = await obtener_otp_valido(db.conn, numero_afiliado, nro_doc, codigo)
        if not otp_valido:
            raise Exception("Código de verificación inválido, expirado o ya utilizado")
        
        # 2. Buscar y retornar datos del afiliado
        afiliado = await buscar_afiliado_por_dni(db.conn, numero_afiliado, nro_doc)
        if not afiliado:
            raise Exception("Error al obtener datos del afiliado")
        
        return afiliado
        
    except Exception as e:
        raise Exception(f"Error en verificación: {str(e)}")

@mcp.tool()
async def get_id_practica_por_nombre(ctx: Context[ServerSession, AppContext], nombre: str) -> List[Practica]:
    """
    Busca y recupera el ID de una práctica médica a partir de su nombre.

    Esta es una herramienta de búsqueda fundamental que se debe usar ANTES de agregar un ítem de tipo 'práctica' a un reintegro.
    El objetivo principal es obtener el `practica_id` correcto para luego usarlo en la herramienta `add_item_to_reintegro`.

    Workflow para el LLM:
    1. Cuando el usuario mencione una práctica médica (ej: "una consulta", "una radiografía"), usa esta herramienta para encontrar su ID.
    2. La búsqueda es flexible (LIKE %nombre%), por lo que puedes usar términos parciales como "consulta", "radio", "laboratorio".
    3. La herramienta devuelve una LISTA de prácticas que coinciden.
       - Si la lista tiene un solo resultado, usa ese `practica_id`.
       - Si la lista tiene MÚLTIPLES resultados, DEBES preguntar al usuario para que elija la correcta antes de proceder.
       - Si la lista está vacía, informa al usuario que no se encontró la práctica.
    4. Una vez obtenido el `practica_id` definitivo, ya puedes llamar a la herramienta para agregar el ítem al reintegro.

    Args:
        nombre (str): Nombre o parte del nombre de la práctica a buscar.

    Returns:
        Una lista de objetos `Practica` que coinciden con el nombre. Cada objeto contiene `practica_id`, `codigo` y `nombre`.
    """
    try:
        db = ctx.request_context.lifespan_context.db
        resultado = await buscar_practica_por_nombre(db.conn, nombre)
        return resultado
    except Exception as e:
        raise Exception(f"Error al buscar práctica: {str(e)}")

@mcp.tool()
async def practicas_cubiertas(ctx: Context[ServerSession, AppContext], plan_id: int) -> List[Practica]:
    """
    Obtiene las prácticas médicas cubiertas por un plan
    Args:
        ctx: Contexto del servidor con sesión y aplicación
        plan_id (int): ID del plan
    Returns:
        Optional[List[Practica]]: Lista de objetos Practica o None si no hay coberturas
    """
    try:
        db = ctx.request_context.lifespan_context.db
        resultado = await get_practicas_cubiertas(db.conn, plan_id)
        return resultado
    except Exception as e:
        raise Exception(f"Error al obtener prácticas cubiertas: {str(e)}")


if __name__ == "__main__":
    # Inicializar y ejecutar el servidor
    mcp.run(transport='stdio')