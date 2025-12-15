# utils.py
from datetime import date, datetime, timedelta
import sys
import os
import random
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bd.baseModels import Afiliado, Practica
from typing import Optional, List, Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''
Genera un código OTP de 6 dígitos
Retorna un string con 6 números aleatorios
'''
def generar_codigo_otp() -> str:
    return str(random.randint(100000, 999999))

'''
Guarda un código OTP en la base de datos
El código expira en 5 minutos
'''
async def guardar_otp(connection, numero_afiliado: str, nro_doc: str, codigo: str):
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    query = """
        INSERT INTO otp_afiliado (numero_afiliado, nro_doc, codigo, expires_at, usado, intentos)
        VALUES ($1, $2, $3, $4, FALSE, 0)
    """
    await connection.execute(query, numero_afiliado, nro_doc, codigo, expires_at)

# buscar afiliado por dni
async def buscar_afiliado_por_dni(connection, numero_afiliado: str, nro_doc: str) -> Optional[Afiliado]:
    try:
        query = """
            SELECT afiliado_id, tipo_doc, nro_doc, nombre, apellido, 
                   fecha_nac, email, tel, plan_id, cbu
            FROM public.afiliado 
            WHERE afiliado_numero = $1 AND nro_doc = $2
        """
        result = await connection.fetchrow(query, numero_afiliado, nro_doc)
        
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
        
        return [Practica(**dict(row)) for row in result] if result else []
    
    except Exception as e:
        raise Exception(f"Error en utils.buscar_practica_por_nombre: {e}")
    
'''
Obtiene las prácticas cubiertas para un afiliado.
Primero busca al afiliado por su ID, obtiene su plan_id y luego retorna sus prácticas cubiertas.
Parámetros:
  connection (asyncpg.Connection) — Conexión a la base de datos.
  afiliado_id (int) — ID del afiliado.
Retorna:
  Optional[list[Practica]] — Lista de prácticas cubiertas por el plan del afiliado,
                             None si el afiliado no existe o no tiene prácticas cubiertas.
'''
async def get_practicas_cubiertas(connection, afiliado_id: int) -> Optional[list[Practica]]:
    try:
        # Primero buscar al afiliado para obtener su plan_id
        query_afiliado = """
            SELECT plan_id
            FROM public.afiliado
            WHERE afiliado_id = $1
        """
        afiliado = await connection.fetchrow(query_afiliado, afiliado_id)
        
        if not afiliado:
            return None
        
        plan_id = afiliado['plan_id']
        
        # Luego buscar las prácticas cubiertas del plan
        query_practicas = """
            SELECT p.practica_id, p.codigo, p.nombre, p.requiere_autorizacion
            FROM public.practica p
            JOIN public.cobertura_practica pp ON p.practica_id = pp.practica_id
            WHERE pp.plan_id = $1
        """
        results = await connection.fetch(query_practicas, plan_id)
        
        if results:
            return [Practica(**dict(row)) for row in results]
        else:
            return None
    except Exception as e:
        raise Exception(f"Error en utils.get_practicas_cubiertas: {e}")

'''
Valida y obtiene un código OTP
Verifica que el código sea correcto, no esté usado, no esté vencido y no supere 3 intentos
Retorna el registro OTP si es válido, None si no lo es
'''
async def obtener_otp_valido(connection, numero_afiliado: str, nro_doc: str, codigo: str):
    # Buscar el OTP más reciente
    query = """
        SELECT id, codigo, expires_at, usado, intentos
        FROM otp_afiliado
        WHERE numero_afiliado = $1 AND nro_doc = $2
        ORDER BY id DESC
        LIMIT 1
    """
    row = await connection.fetchrow(query, numero_afiliado, nro_doc)
    
    if not row:
        return None
    
    now = datetime.utcnow()
    
    # Verificar si ya fue usado
    if row["usado"]:
        return None
    
    # Verificar si está vencido
    if row["expires_at"] < now:
        return None
    
    # Verificar intentos máximos
    if row["intentos"] >= 3:
        return None
    
    # Incrementar intentos
    nuevo_intentos = row["intentos"] + 1
    await connection.execute(
        "UPDATE otp_afiliado SET intentos = $1 WHERE id = $2",
        nuevo_intentos, row["id"]
    )
    
    # Verificar si el código coincide
    if row["codigo"] != codigo:
        return None
    
    # Marcar como usado
    await connection.execute(
        "UPDATE otp_afiliado SET usado = TRUE WHERE id = $1",
        row["id"]
    )
    
    return row

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email(destinatario: str, asunto: str, cuerpo: str):
    '''
    Envía un email usando SMTP de Gmail de forma SIMPLE
    '''
    try:
        # Crear mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = "mbcrfull@gmail.com"
        mensaje['To'] = destinatario
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(cuerpo, 'plain'))
        
        # Conectar y enviar
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login("mbcrfull@gmail.com", "zkcb opke cliv ywqm")
        servidor.send_message(mensaje)
        servidor.quit()
        
        logger.info(f"✅ Email enviado a {destinatario}")
        
    except Exception as e:
        logger.error(f"❌ Error al enviar email: {e}")