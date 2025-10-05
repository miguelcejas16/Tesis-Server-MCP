# utils.py
from datetime import date
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bd.baseModels import Afiliado, Practica
from typing import Optional, List, Literal

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
    
async def buscar_practica_por_nombre(connection, nombre: str) -> Optional[List[Practica]]:
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
    
async def create_temp_reintegro(
        connection, 
        afiliado_id: int,
        total_presentado: float,
        ) -> int: 
    try:
        query = """
            INSERT INTO public.reintegro (afiliado_id, estado, total_presentado, total_aprobado)
            VALUES ($1, 'pendiente', $2, 0.0)
            RETURNING reintegro_id
        """
        result = await connection.fetchrow(query, afiliado_id, total_presentado)

        if result:
            return result['reintegro_id']
        else:
            return None
    except Exception as e:
        raise Exception(f"Error en utils.create_temp_reintegro: {e}")

async def add_item_to_reintegro(
        connection, 
        reintegro_id: int,
        tipo: Literal["M", "P"],
        practica_id: Optional[int],
        medicamento_id: Optional[int],
        fecha_prestacion: date,
        monto_presentado: float,
        ) -> int:
    try:
        # Mapear 'M'/'P' a los valores de la base de datos y validar
        if tipo == "M":
            tipo_db = "medicamento"
            if not medicamento_id:
                raise ValueError("medicamento_id es requerido cuando el tipo es 'M'")
        elif tipo == "P":
            tipo_db = "practica"
            if not practica_id:
                raise ValueError("practica_id es requerido cuando el tipo es 'P'")
        else:
            # Esta validación es por seguridad, aunque Literal ya lo previene estáticamente
            raise ValueError("El valor de 'tipo' debe ser 'M' o 'P'")

        query = """
            INSERT INTO public.reintegro_item (
                reintegro_id, tipo, practica_id, medicamento_id, 
                fecha_prestacion, monto_presentado
            )
            VALUES ($1, $2, $3, NULLIF($4, 0), $5, $6)
            RETURNING item_id
        """
        result = await connection.fetchrow(
            query,
            reintegro_id, tipo_db, practica_id, medicamento_id,
            fecha_prestacion, monto_presentado
        )

        if result:
            return result['item_id']
        else:
            return None
    except Exception as e:
        raise Exception(f"Error en utils.add_item_to_reintegro: {e}")
    
async def commit_reintegro(connection, reintegro_id: int) -> bool:
    try:
        query = """
            UPDATE public.reintegro
            SET estado = 'en_revision', updated_at = NOW()
            WHERE reintegro_id = $1
        """
        result = await connection.execute(query, reintegro_id)
        
        if result and result.startswith("UPDATE"):
            return True
        else:
            return False
    except Exception as e:
        raise Exception(f"Error en utils.commit_reintegro: {e}")