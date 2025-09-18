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