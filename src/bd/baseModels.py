from pydantic import BaseModel
from typing import Optional
from datetime import date

class Afiliado(BaseModel):
    """Modelo para representar un afiliado de la obra social"""
    afiliado_id: int
    tipo_doc: str
    nro_doc: str
    nombre: str
    apellido: str
    fecha_nac: Optional[date] = None
    email: Optional[str] = None
    tel: Optional[str] = None
    plan_id: Optional[int] = None
    
    class Config:
        from_attributes = True  # Para poder crear desde dict/row

class Practica(BaseModel):
    """Modelo para representar una práctica médica"""
    practica_id: int
    codigo: str
    nombre: str
    requiere_autorizacion: int  # 0 o 1
    
    class Config:
        from_attributes = True  # Para poder crear desde dict/row