import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
USERNAME = os.getenv("STREAMLIT_USERNAME")
PASSWORD = os.getenv("STREAMLIT_PASSWORD")

st.set_page_config(page_title="Cafetería Tesla", layout="wide")

# ---------------------------------------------------
# Estado de sesión
# ---------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "venta_pendiente" not in st.session_state:
    st.session_state.venta_pendiente = None

if "abono_pendiente" not in st.session_state:
    st.session_state.abono_pendiente = None


# ---------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------
def api_get(endpoint: str, params: dict | None = None):
    return requests.get(f"{API_URL}{endpoint}", params=params, timeout=30)


def api_post(endpoint: str, payload: dict):
    return requests.post(f"{API_URL}{endpoint}", json=payload, timeout=30)


def get_students():
    resp = api_get("/alumnos")
    if resp.status_code == 200:
        return resp.json()
    return []


def get_products():
    resp = api_get("/productos")
    if resp.status_code == 200:
        return resp.json()
    return []


def login():
    st.title("Inicio de sesión - Colegio Tesla")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")


def logout():
    st.session_state.authenticated = False
    st.session_state.venta_pendiente = None
    st.session_state.abono_pendiente = None
    st.rerun()


def mostrar_error_respuesta(resp):
    try:
        st.error(resp.json())
    except Exception:
        st.error("Ocurrió un error al comunicarse con el servidor.")


def obtener_opciones_alumnos():
    students = get_students()
    return {
        f"{s['alumno']} - {s['grupo']} (ID: {s['id']})": s
        for s in students
    }


def obtener_opciones_productos():
    products = get_products()
    return {
        f"{p['nombre']} - ${p['precio']}": p
        for p in products
    }


# ---------------------------------------------------
# Login
# ---------------------------------------------------
if not st.session_state.authenticated:
    login()
    st.stop()


# ---------------------------------------------------
# Encabezado principal
# ---------------------------------------------------
st.title("Panel de administración - Cafetería Tesla")

menu = st.sidebar.selectbox(
    "Selecciona una opción",
    [
        "Registrar venta",
        "Registrar abono",
        "Consultar saldo",
        "Estado de cuenta",
        "Deudores",
        "Descargar reporte Excel",
    ],
)

if st.sidebar.button("Cerrar sesión"):
    logout()


# ---------------------------------------------------
# Registrar venta
# ---------------------------------------------------
if menu == "Registrar venta":
    st.header("Registrar venta")

    student_options = obtener_opciones_alumnos()
    product_options = obtener_opciones_productos()

    selected_students = st.multiselect(
        "Selecciona uno o varios alumnos",
        options=list(student_options.keys()),
    )

    selected_product = st.selectbox(
        "Selecciona un producto",
        options=list(product_options.keys()) if product_options else [],
    )

    cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)

    if st.button("Preparar venta"):
        if not selected_students:
            st.warning("Selecciona al menos un alumno.")
        elif not selected_product:
            st.warning("Selecciona un producto.")
        else:
            producto = product_options[selected_product]
            total_individual = producto["precio"] * cantidad

            st.session_state.venta_pendiente = {
                "student_labels": selected_students,
                "students_data": [student_options[label] for label in selected_students],
                "producto_id": producto["id"],
                "producto_nombre": producto["nombre"],
                "precio_unitario": producto["precio"],
                "cantidad": cantidad,
                "total_individual": total_individual,
                "total_general": total_individual * len(selected_students),
            }

    if st.session_state.venta_pendiente:
        venta = st.session_state.venta_pendiente

        st.subheader("Confirmación de venta")
        st.write(f"**Producto:** {venta['producto_nombre']}")
        st.write(f"**Precio unitario:** ${venta['precio_unitario']}")
        st.write(f"**Cantidad por alumno:** {venta['cantidad']}")
        st.write(f"**Total por alumno:** ${venta['total_individual']}")
        st.write(f"**Alumnos seleccionados:** {len(venta['students_data'])}")
        st.write(f"**Total general:** ${venta['total_general']}")

        with st.expander("Ver alumnos seleccionados"):
            for alumno in venta["students_data"]:
                st.write(f"- {alumno['alumno']} ({alumno['grupo']})")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Confirmar venta", key="confirmar_venta"):
                success_count = 0
                errors = []

                for alumno in venta["students_data"]:
                    resp = api_post(
                        "/ventas",
                        {
                            "alumno_id": alumno["id"],
                            "producto_id": venta["producto_id"],
                            "cantidad": venta["cantidad"],
                        },
                    )

                    if resp.status_code == 200:
                        success_count += 1
                    else:
                        try:
                            error_detail = resp.json()
                        except Exception:
                            error_detail = "Error desconocido"
                        errors.append(
                            {
                                "alumno": alumno["alumno"],
                                "grupo": alumno["grupo"],
                                "error": error_detail,
                            }
                        )

                if success_count > 0:
                    st.success(f"Venta registrada correctamente para {success_count} alumno(s).")

                if errors:
                    st.error("Algunas ventas no pudieron registrarse.")
                    st.json(errors)

                st.session_state.venta_pendiente = None
                st.rerun()

        with col2:
            if st.button("Cancelar venta", key="cancelar_venta"):
                st.session_state.venta_pendiente = None
                st.info("Venta cancelada.")
                st.rerun()


# ---------------------------------------------------
# Registrar abono
# ---------------------------------------------------
elif menu == "Registrar abono":
    st.header("Registrar abono")

    student_options = obtener_opciones_alumnos()

    selected_student = st.selectbox(
        "Selecciona un alumno",
        options=list(student_options.keys()) if student_options else [],
    )

    monto = st.number_input("Monto", min_value=0.0, value=0.0, step=1.0)
    concepto = st.text_input("Concepto (opcional)")

    if st.button("Preparar abono"):
        if not selected_student:
            st.warning("Selecciona un alumno.")
        elif monto <= 0:
            st.warning("El monto debe ser mayor a 0.")
        else:
            alumno = student_options[selected_student]

            st.session_state.abono_pendiente = {
                "alumno_id": alumno["id"],
                "alumno_nombre": alumno["alumno"],
                "grupo": alumno["grupo"],
                "monto": monto,
                "concepto": concepto if concepto else None,
            }

    if st.session_state.abono_pendiente:
        abono = st.session_state.abono_pendiente

        st.subheader("Confirmación de abono")
        st.write(f"**Alumno:** {abono['alumno_nombre']}")
        st.write(f"**Grupo:** {abono['grupo']}")
        st.write(f"**Monto:** ${abono['monto']}")
        st.write(f"**Concepto:** {abono['concepto'] if abono['concepto'] else 'Sin concepto'}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Confirmar abono", key="confirmar_abono"):
                resp = api_post(
                    "/abonos",
                    {
                        "alumno_id": abono["alumno_id"],
                        "monto": abono["monto"],
                        "concepto": abono["concepto"],
                    },
                )

                if resp.status_code == 200:
                    st.success("Abono registrado correctamente.")
                    st.json(resp.json())
                else:
                    mostrar_error_respuesta(resp)

                st.session_state.abono_pendiente = None
                st.rerun()

        with col2:
            if st.button("Cancelar abono", key="cancelar_abono"):
                st.session_state.abono_pendiente = None
                st.info("Abono cancelado.")
                st.rerun()


# ---------------------------------------------------
# Consultar saldo
# ---------------------------------------------------
elif menu == "Consultar saldo":
    st.header("Consultar saldo")

    student_options = obtener_opciones_alumnos()

    selected_student = st.selectbox(
        "Selecciona un alumno",
        options=list(student_options.keys()) if student_options else [],
    )

    if st.button("Consultar saldo"):
        if not selected_student:
            st.warning("Selecciona un alumno.")
        else:
            alumno_id = student_options[selected_student]["id"]
            resp = api_get(f"/alumnos/{alumno_id}/saldo")

            if resp.status_code == 200:
                saldo = resp.json()
                st.success("Saldo consultado correctamente.")
                st.write(f"**Alumno:** {saldo['alumno']}")
                st.write(f"**Grupo:** {saldo['grupo']}")
                st.write(f"**Total de ventas:** ${saldo['total_ventas']}")
                st.write(f"**Total de abonos:** ${saldo['total_abonos']}")
                st.write(f"**Saldo pendiente:** ${saldo['saldo_pendiente']}")
            else:
                mostrar_error_respuesta(resp)


# ---------------------------------------------------
# Estado de cuenta
# ---------------------------------------------------
elif menu == "Estado de cuenta":
    st.header("Estado de cuenta")

    student_options = obtener_opciones_alumnos()

    selected_student = st.selectbox(
        "Selecciona un alumno",
        options=list(student_options.keys()) if student_options else [],
    )

    if st.button("Consultar estado de cuenta"):
        if not selected_student:
            st.warning("Selecciona un alumno.")
        else:
            alumno_id = student_options[selected_student]["id"]
            resp = api_get(f"/alumnos/{alumno_id}/estado_cuenta")

            if resp.status_code == 200:
                estado = resp.json()

                st.success("Estado de cuenta cargado correctamente.")

                st.subheader("Información del alumno")
                st.write(f"**Alumno:** {estado['alumno']}")
                st.write(f"**Grupo:** {estado['grupo']}")
                st.write(f"**Total de ventas:** ${estado['total_ventas']}")
                st.write(f"**Total de abonos:** ${estado['total_abonos']}")
                st.write(f"**Saldo pendiente:** ${estado['saldo_pendiente']}")

                st.subheader("Ventas")
                st.dataframe(estado["ventas"], use_container_width=True)

                st.subheader("Abonos")
                st.dataframe(estado["abonos"], use_container_width=True)
            else:
                mostrar_error_respuesta(resp)


# ---------------------------------------------------
# Deudores
# ---------------------------------------------------
elif menu == "Deudores":
    st.header("Lista de deudores")

    resp = api_get("/deudores")

    if resp.status_code == 200:
        deudores = resp.json()

        if len(deudores) == 0:
            st.success("No hay deudores registrados.")
        else:
            tabla = [
                {
                    "Alumno": d["alumno"],
                    "Grupo": d["grupo"],
                    "Total ventas": d["total_ventas"],
                    "Total abonos": d["total_abonos"],
                    "Saldo pendiente": d["saldo_pendiente"],
                }
                for d in deudores
            ]

            st.write(f"**Total de alumnos con adeudo:** {len(deudores)}")
            st.dataframe(tabla, use_container_width=True)
    else:
        mostrar_error_respuesta(resp)


# ---------------------------------------------------
# Descargar reporte Excel
# ---------------------------------------------------
elif menu == "Descargar reporte Excel":
    st.header("Descargar reporte Excel")

    if st.button("Generar y descargar reporte"):
        resp = api_get("/estado-cuenta/excel")

        if resp.status_code == 200:
            st.success("Reporte generado correctamente.")

            st.download_button(
                label="Descargar Excel",
                data=resp.content,
                file_name="estado_cuenta.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            mostrar_error_respuesta(resp)