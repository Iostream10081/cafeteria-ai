from app.database import SessionLocal
from app.models import Producto

db = SessionLocal()

productos = [
    {"nombre": "D1", "precio": 45},
    {"nombre": "D2", "precio": 50},
    {"nombre": "C1", "precio": 50},
    {"nombre": "C2", "precio": 55},
    {"nombre": "A", "precio": 10},
]

for p in productos:
    producto = Producto(nombre=p["nombre"], precio=p["precio"])
    db.add(producto)

db.commit()

print("Productos cargados correctamente")