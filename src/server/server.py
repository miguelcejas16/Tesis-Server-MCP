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

@mcp.tool()
async def afiliado_por_dni(ctx: Context[ServerSession, AppContext], tipo_doc: str, nro_doc: str) -> Optional[Afiliado]:
    """
    Busca un afiliado por tipo y número de documento
    Args:
        tipo_doc (str): Tipo de documento (DNI, PASAPORTE, etc.)
        nro_doc (str): Número de documento
    Returns:
        Datos del afiliado, incluyendo su plan_id
    """
    try:
        db = ctx.request_context.lifespan_context.db
        resultado = await buscar_afiliado_por_dni(db.conn, tipo_doc, nro_doc)
        return resultado
    except Exception as e:
        raise Exception(f"Error al buscar afiliado: {str(e)}")

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