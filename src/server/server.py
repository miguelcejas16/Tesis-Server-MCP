from collections.abc import AsyncIterator
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import Tool
from contextlib import asynccontextmanager
import asyncpg
import os
import sys
from dotenv import load_dotenv
from typing import Optional, Any

# Agregar src al path para importaciones absolutas
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import buscar_afiliado_por_dni
from bd.baseModels import Afiliado

# Cargar variables de entorno
load_dotenv()

# Cargar variables de entorno
load_dotenv()

class Database:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    @classmethod
    async def connect(cls) -> "Database":
        try:
            conn = await asyncpg.connect(
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
            )
            return cls(conn)
        except Exception as e:
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

@mcp.tool()
async def afiliado_por_dni(ctx: Context[ServerSession, AppContext], tipo_doc: str, nro_doc: str) -> Optional[Afiliado]:
    """
    Busca un afiliado por tipo y número de documento
    Args:
        ctx: Contexto del servidor con sesión y aplicación
        tipo_doc (str): Tipo de documento (DNI, PASAPORTE, etc.)
        nro_doc (str): Número de documento
    Returns:
        Optional[Afiliado]: Objeto Afiliado o None si no existe
    """
    try:
        db = ctx.request_context.lifespan_context.db
        resultado = await buscar_afiliado_por_dni(db.conn, tipo_doc, nro_doc)
        return resultado
    except Exception as e:
        raise Exception(f"Error al buscar afiliado: {str(e)}")

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')