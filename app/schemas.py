from pydantic import BaseModel


class VentaCreate(BaseModel):
    producto: str
    cantidad: int
    precio_unitario: float