from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

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

class Reintegro(BaseModel):
    """Modelo para representar un reintegro médico"""
    reintegro_id: Optional[int] = Field(None, description="ID del reintegro (autogenerado)")
    afiliado_id: int = Field(..., description="ID del afiliado asociado al reintegro")
    estado: str = Field("pendiente", description="Estado del reintegro (pendiente, en_revision, etc.)")
    fecha_presentacion: Optional[datetime] = Field(None, description="Fecha de presentación del reintegro")
    total_presentado: float = Field(0.0, description="Monto total presentado por el afiliado")
    total_aprobado: float = Field(0.0, description="Monto total aprobado por la obra social")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales sobre el reintegro")
    updated_at: Optional[datetime] = Field(None, description="Última fecha de actualización")

    class Config:
        from_attributes = True  # Permite crear instancias desde dict/row

class ReintegroItem(BaseModel):
    """Modelo para representar un ítem asociado a un reintegro"""
    item_id: Optional[int] = Field(None, description="ID del ítem (autogenerado)")
    reintegro_id: int = Field(..., description="ID del reintegro al que pertenece el ítem")
    tipo: str = Field(..., description="Tipo del ítem ('practica' o 'medicamento')")
    practica_id: Optional[int] = Field(None, description="ID de la práctica médica asociada (si aplica)")
    medicamento_id: Optional[int] = Field(None, description="ID del medicamento asociado (si aplica)")
    fecha_prestacion: date = Field(..., description="Fecha en la que se realizó la prestación")
    monto_presentado: float = Field(..., description="Monto presentado para el ítem")
    monto_aprobado: Optional[float] = Field(None, description="Monto aprobado para el ítem")
    cobertura_aplicada: Optional[float] = Field(None, description="Porcentaje de cobertura aplicado al ítem")
    copago: Optional[float] = Field(None, description="Monto del copago realizado por el afiliado")
    prestador_txt: Optional[str] = Field(None, description="Texto descriptivo del prestador (si aplica)")
    comprobante_txt: Optional[str] = Field(None, description="Texto descriptivo del comprobante (si aplica)")

    class Config:
        from_attributes = True  # Permite crear instancias desde dict/row

class Documento(BaseModel):
    """Modelo para representar un documento asociado a un reintegro"""
    documento_id: Optional[int] = Field(None, description="ID del documento (autogenerado)")
    reintegro_id: int = Field(..., description="ID del reintegro al que pertenece el documento")
    tipo: str = Field(..., description="Tipo de documento ('FACTURA' o 'SOPORTE')")
    filename: str = Field(..., description="Nombre del archivo del documento")
    ruta_local: str = Field(..., description="Ruta local donde se almacena el archivo")
    estado: str = Field("recibido", description="Estado del documento ('recibido', 'vinculado', 'reemplazado')")
    checksum: Optional[str] = Field(None, description="Checksum del archivo para verificar integridad")
    creado_en: Optional[datetime] = Field(None, description="Fecha de creación del documento")
    actualizado_en: Optional[datetime] = Field(None, description="Última fecha de actualización del documento")

    class Config:
        from_attributes = True  # Permite crear instancias desde dict/row