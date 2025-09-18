# utils.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bd.connection import get_connection
from bd.baseModels import Afiliado
from typing import Optional

# buscar afiliado por dni
async def buscar_afiliado_por_dni(connection, tipo_doc: str, nro_doc: str) -> Optional[Afiliado]:
    """
    Busca un afiliado por tipo y número de documento
    Args:
        connection: Conexión a la base de datos asyncpg
        tipo_doc (str): Tipo de documento (DNI, PASAPORTE, etc.)
        nro_doc (str): Número de documento
    Returns:
        Optional[Afiliado]: Objeto Afiliado o None si no existe
    """
    try:
        query = """
            SELECT afiliado_id, tipo_doc, nro_doc, nombre, apellido, 
                   fecha_nac, email, tel, plan_id
            FROM public.afiliado 
            WHERE tipo_doc = $1 AND nro_doc = $2
        """
        result = await connection.fetchrow(query, tipo_doc, nro_doc)
        
        if result:
            return Afiliado(**dict(result))
        return None
    except Exception as e:
        print(f"Error al buscar afiliado: {e}")
        return None
