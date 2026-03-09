from pydantic import BaseModel


class VentaCreate(BaseModel):
    alumno_id: int
    producto_id: int
    cantidad: int