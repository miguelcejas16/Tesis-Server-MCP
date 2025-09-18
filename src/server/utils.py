# utils.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bd.baseModels import Afiliado, Practica
from typing import Optional

# buscar afiliado por dni
async def buscar_afiliado_por_dni(connection, tipo_doc: str, nro_doc: str) -> Optional[Afiliado]:
    try:
        query = """
            SELECT afiliado_id, tipo_doc, nro_doc, nombre, apellido, 
                   fecha_nac, email, tel, plan_id
            FROM public.afiliado 
            WHERE tipo_doc = $1 AND nro_doc = $2
        """
        result = await connection.fetchrow(query, tipo_doc, nro_doc)
        
        if result:
            afiliado = Afiliado(**dict(result))
            return afiliado
        else:
            return None
    except Exception as e:
        raise Exception(f"Error en utils.buscar_afiliado_por_dni: {e}")

async def buscar_practica_por_nombre(connection, nombre: str) -> Optional[Practica]:
    try:
        query = """
            SELECT practica_id, codigo, nombre, requiere_autorizacion
            FROM public.practica 
            WHERE nombre ILIKE $1
        """
        result = await connection.fetch(query, f"%{nombre}%")
        
        if result:
            return [Practica(**dict(row)) for row in result]
        else:
            return None
    except Exception as e:
        raise Exception(f"Error en utils.buscar_practica_por_nombre: {e}")
    
async def get_practicas_cubiertas(connection, plan_id: int) -> Optional[list[Practica]]:
    try:
        query = """
            SELECT p.practica_id, p.codigo, p.nombre, p.requiere_autorizacion
            FROM public.practica p
            JOIN public.cobertura_practica pp ON p.practica_id = pp.practica_id
            WHERE pp.plan_id = $1
        """
        results = await connection.fetch(query, plan_id)
        
        if results:
            return [Practica(**dict(row)) for row in results]
        else:
            return None
    except Exception as e:
        raise Exception(f"Error en utils.get_practicas_cubiertas: {e}")