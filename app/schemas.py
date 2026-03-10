from pydantic import BaseModel


class VentaCreate(BaseModel):
    alumno_id: int
    producto_id: int
    cantidad: int


class AbonoCreate(BaseModel):
    alumno_id: int
    monto: float
    concepto: str | None = None