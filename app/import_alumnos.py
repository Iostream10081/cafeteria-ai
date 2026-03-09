import pandas as pd

from app.database import SessionLocal
from app.models import Alumno


def importar_alumnos_desde_excel(ruta_excel: str):
    df = pd.read_excel(ruta_excel)

    columnas_esperadas = {"id", "alumno", "grupo"}
    columnas_archivo = set(df.columns.str.strip().str.lower())

    if not columnas_esperadas.issubset(columnas_archivo):
        raise ValueError(
            f"El archivo debe contener las columnas: {columnas_esperadas}. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    db = SessionLocal()

    try:
        for _, fila in df.iterrows():
            alumno_existente = db.query(Alumno).filter(Alumno.id == int(fila["id"])).first()

            if alumno_existente:
                continue

            nuevo_alumno = Alumno(
                id=int(fila["id"]),
                alumno=str(fila["alumno"]).strip(),
                grupo=str(fila["grupo"]).strip()
            )

            db.add(nuevo_alumno)

        db.commit()
        print("Alumnos importados correctamente")

    except Exception as e:
        db.rollback()
        print(f"Error al importar alumnos: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    ruta = "alumnos.xlsx"
    importar_alumnos_desde_excel(ruta)
