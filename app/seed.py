from app.database import SessionLocal
from app.models import Producto


def seed_products():
    db = SessionLocal()

    productos = [
        {"nombre": "D1", "precio": 45},
        {"nombre": "D2", "precio": 50},
        {"nombre": "C1", "precio": 50},
        {"nombre": "C2", "precio": 55},
        {"nombre": "A", "precio": 10},
    ]

    try:
        for p in productos:
            existente = db.query(Producto).filter(Producto.nombre == p["nombre"]).first()
            if not existente:
                db.add(Producto(nombre=p["nombre"], precio=p["precio"]))

        db.commit()
        print("Productos cargados correctamente")
    finally:
        db.close()


if __name__ == "__main__":
    seed_products()