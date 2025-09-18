from collections.abc import AsyncIterator
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import Tool
from contextlib import asynccontextmanager
import asyncpg
import os
from dotenv import load_dotenv
from typing import Optional, Any

from .utils import buscar_afiliado_por_dni as buscar_afiliado_utils
from ..bd.baseModels import Afiliado

# Cargar variables de entorno
load_dotenv()

class Database:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    @classmethod
    async def connect(cls) -> "Database":
        conn = await asyncpg.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
        )
        return cls(conn)
    
    async def disconnect(self) -> None:
        await self.conn.close()

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()


mcp = FastMCP("Obra Social Server", lifespan=app_lifespan)

@mcp.tool()
async def buscar_afiliado_por_dni(ctx: Context[ServerSession, AppContext], tipo_doc: str, nro_doc: str) -> Optional[Afiliado]:
    """
    Busca un afiliado por tipo y número de documento
    Args:
        ctx: Contexto del servidor con sesión y aplicación
        tipo_doc (str): Tipo de documento (DNI, PASAPORTE, etc.)
        nro_doc (str): Número de documento
    Returns:
        Optional[Afiliado]: Objeto Afiliado o None si no existe
    """
    db = ctx.request_context.lifespan_context.db
    return await buscar_afiliado_utils(db.conn, tipo_doc, nro_doc)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')