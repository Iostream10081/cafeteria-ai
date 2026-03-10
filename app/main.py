import pandas as pd
from fastapi.responses import FileResponse
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
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


@app.get("/alumnos")
def listar_alumnos(db: Session = Depends(get_db)):
    alumnos = db.query(models.Alumno).all()

    resultado = []
    for a in alumnos:
        resultado.append({
            "id": a.id,
            "alumno": a.alumno,
            "grupo": a.grupo
        })

    return resultado

@app.get("/alumnos/buscar")
def buscar_alumnos(nombre: str, db: Session = Depends(get_db)):
    alumnos = (
        db.query(models.Alumno)
        .filter(models.Alumno.alumno.ilike(f"%{nombre}%"))
        .all()
    )

    resultado = []
    for a in alumnos:
        resultado.append({
            "id": a.id,
            "alumno": a.alumno,
            "grupo": a.grupo
        })

    return resultado


@app.get("/productos")
def listar_productos(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()

    resultado = []
    for p in productos:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio
        })

    return resultado

@app.get("/productos/buscar")
def buscar_productos(nombre: str, db: Session = Depends(get_db)):
    productos = (
        db.query(models.Producto)
        .filter(models.Producto.nombre.ilike(f"%{nombre}%"))
        .all()
    )

    resultado = []
    for p in productos:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio
        })

    return resultado


@app.post("/ventas")
def crear_venta(venta: schemas.VentaCreate, db: Session = Depends(get_db)):
    alumno = db.query(models.Alumno).filter(models.Alumno.id == venta.alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    producto = db.query(models.Producto).filter(models.Producto.id == venta.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    total = venta.cantidad * producto.precio

    nueva_venta = models.Venta(
        alumno_id=venta.alumno_id,
        producto_id=venta.producto_id,
        cantidad=venta.cantidad,
        total=total
    )

    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)

    return {
        "mensaje": "Venta registrada correctamente",
        "venta": {
            "id": nueva_venta.id,
            "alumno_id": nueva_venta.alumno_id,
            "producto_id": nueva_venta.producto_id,
            "cantidad": nueva_venta.cantidad,
            "total": nueva_venta.total,
            "fecha": nueva_venta.fecha
        }
    }


@app.get("/ventas")
def listar_ventas(db: Session = Depends(get_db)):
    ventas = db.query(models.Venta).all()

    resultado = []
    for v in ventas:
        alumno = db.query(models.Alumno).filter(models.Alumno.id == v.alumno_id).first()
        producto = db.query(models.Producto).filter(models.Producto.id == v.producto_id).first()

        resultado.append({
            "id": v.id,
            "alumno_id": v.alumno_id,
            "alumno": alumno.alumno if alumno else None,
            "grupo": alumno.grupo if alumno else None,
            "producto_id": v.producto_id,
            "producto": producto.nombre if producto else None,
            "cantidad": v.cantidad,
            "total": v.total,
            "fecha": v.fecha
        })

    return resultado

@app.get("/ventas/excel")
def exportar_ventas_excel(db: Session = Depends(get_db)):
    ventas = db.query(models.Venta).all()

    datos = []
    for v in ventas:
        alumno = db.query(models.Alumno).filter(models.Alumno.id == v.alumno_id).first()
        producto = db.query(models.Producto).filter(models.Producto.id == v.producto_id).first()

        datos.append({
            "id_venta": v.id,
            "alumno_id": v.alumno_id,
            "alumno": alumno.alumno if alumno else None,
            "grupo": alumno.grupo if alumno else None,
            "producto_id": v.producto_id,
            "producto": producto.nombre if producto else None,
            "cantidad": v.cantidad,
            "total": v.total,
            "fecha": v.fecha
        })

    df = pd.DataFrame(datos)

    nombre_archivo = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(nombre_archivo, index=False)

    return FileResponse(
        path=nombre_archivo,
        filename=nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.post("/abonos")
def crear_abono(abono: schemas.AbonoCreate, db: Session = Depends(get_db)):
    alumno = db.query(models.Alumno).filter(models.Alumno.id == abono.alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    if abono.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0")

    nuevo_abono = models.Abono(
        alumno_id=abono.alumno_id,
        monto=abono.monto,
        concepto=abono.concepto
    )

    db.add(nuevo_abono)
    db.commit()
    db.refresh(nuevo_abono)

    return {
        "mensaje": "Abono registrado correctamente",
        "abono": {
            "id": nuevo_abono.id,
            "alumno_id": nuevo_abono.alumno_id,
            "monto": nuevo_abono.monto,
            "concepto": nuevo_abono.concepto,
            "fecha": nuevo_abono.fecha
        }
    }

@app.get("/alumnos/{alumno_id}/saldo")
def consultar_saldo(alumno_id: int, db: Session = Depends(get_db)):
    alumno = db.query(models.Alumno).filter(models.Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    ventas = db.query(models.Venta).filter(models.Venta.alumno_id == alumno_id).all()
    abonos = db.query(models.Abono).filter(models.Abono.alumno_id == alumno_id).all()

    total_ventas = sum(v.total for v in ventas)
    total_abonos = sum(a.monto for a in abonos)
    saldo_pendiente = total_ventas - total_abonos

    return {
        "alumno_id": alumno.id,
        "alumno": alumno.alumno,
        "grupo": alumno.grupo,
        "total_ventas": total_ventas,
        "total_abonos": total_abonos,
        "saldo_pendiente": saldo_pendiente
    }

@app.get("/alumnos/{alumno_id}/estado_cuenta")
def consultar_estado_cuenta(alumno_id: int, db: Session = Depends(get_db)):
    alumno = db.query(models.Alumno).filter(models.Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    ventas = db.query(models.Venta).filter(models.Venta.alumno_id == alumno_id).all()
    abonos = db.query(models.Abono).filter(models.Abono.alumno_id == alumno_id).all()

    detalle_ventas = []
    for v in ventas:
        producto = db.query(models.Producto).filter(models.Producto.id == v.producto_id).first()

        detalle_ventas.append({
            "id": v.id,
            "producto_id": v.producto_id,
            "producto": producto.nombre if producto else None,
            "cantidad": v.cantidad,
            "total": v.total,
            "fecha": v.fecha
        })

    detalle_abonos = []
    for a in abonos:
        detalle_abonos.append({
            "id": a.id,
            "monto": a.monto,
            "concepto": a.concepto,
            "fecha": a.fecha
        })

    total_ventas = sum(v.total for v in ventas)
    total_abonos = sum(a.monto for a in abonos)
    saldo_pendiente = total_ventas - total_abonos

    return {
        "alumno_id": alumno.id,
        "alumno": alumno.alumno,
        "grupo": alumno.grupo,
        "ventas": detalle_ventas,
        "abonos": detalle_abonos,
        "total_ventas": total_ventas,
        "total_abonos": total_abonos,
        "saldo_pendiente": saldo_pendiente
    }