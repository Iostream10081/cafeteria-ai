from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import models, schemas

app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"status": "cafeteria-ai running"}


@app.post("/ventas")
def crear_venta(venta: schemas.VentaCreate, db: Session = Depends(get_db)):
    total = venta.cantidad * venta.precio_unitario

    nueva_venta = models.Venta(
        producto=venta.producto,
        cantidad=venta.cantidad,
        precio_unitario=venta.precio_unitario,
        total=total
    )

    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)

    return {
        "mensaje": "Venta registrada",
        "venta_id": nueva_venta.id,
        "total": nueva_venta.total
    }

@app.get("/ventas")
def listar_ventas(db: Session = Depends(get_db)):
    ventas = db.query(models.Venta).all()

    resultado = []
    for v in ventas:
        resultado.append({
            "id": v.id,
            "producto": v.producto,
            "cantidad": v.cantidad,
            "precio_unitario": v.precio_unitario,
            "total": v.total,
            "fecha": v.fecha
        })

    return resultado