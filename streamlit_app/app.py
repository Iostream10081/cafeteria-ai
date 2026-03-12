import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
USERNAME = os.getenv("STREAMLIT_USERNAME")
PASSWORD = os.getenv("STREAMLIT_PASSWORD")


def login():
    st.title("Login Colegio Tesla")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid credentials")

def get_students():
    resp = requests.get(f"{API_URL}/alumnos")
    if resp.status_code == 200:
        return resp.json()
    return []

def get_products():
    resp = requests.get(f"{API_URL}/productos")
    if resp.status_code == 200:
        return resp.json()
    return []

st.set_page_config(page_title="Cafeteria Admin", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()
st.title("Cafetería Tesla")

menu = st.sidebar.selectbox(
    "Select an option",
    [
        "Register Sale",
        "Register Payment",
        "Check Balance",
        "Account Statement",
        "Download Excel Report"
    ]
)

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

# ---------------------------------------------------
# Register Sale
# ---------------------------------------------------
if menu == "Register Sale":
    st.header("Register Sale")

    students = get_students()
    products = get_products()

    student_options = {
        f"{s['alumno']} - {s['grupo']} (ID: {s['id']})": s["id"]
        for s in students
    }

    product_options = {
        f"{p['nombre']} - ${p['precio']}": p["id"]
        for p in products
    }

    selected_students = st.multiselect(
        "Select one or more students",
        options=list(student_options.keys())
    )

    selected_product = st.selectbox(
        "Select product",
        options=list(product_options.keys()) if product_options else []
    )

    cantidad = st.number_input("Quantity", min_value=1, value=1)

    if st.button("Register Sale"):
        if not selected_students:
            st.error("Please select at least one student")
        elif not selected_product:
            st.error("Please select a product")
        else:
            producto_id = product_options[selected_product]

            success_count = 0
            errors = []

            for student_label in selected_students:
                alumno_id = student_options[student_label]

                venta_resp = requests.post(
                    f"{API_URL}/ventas",
                    json={
                        "alumno_id": alumno_id,
                        "producto_id": producto_id,
                        "cantidad": cantidad
                    }
                )

                if venta_resp.status_code == 200:
                    success_count += 1
                else:
                    errors.append({
                        "student": student_label,
                        "error": venta_resp.json()
                    })

            if success_count > 0:
                st.success(f"Sale registered for {success_count} student(s)")

            if errors:
                st.error("Some sales could not be registered")
                st.json(errors)

# ---------------------------------------------------
# Register Payment
# ---------------------------------------------------
elif menu == "Register Payment":
    st.header("Register Payment")

    students = get_students()

    student_options = {
        f"{s['alumno']} - {s['grupo']} (ID: {s['id']})": s["id"]
        for s in students
    }

    selected_student = st.selectbox(
        "Select student",
        options=list(student_options.keys()) if student_options else []
    )

    monto = st.number_input("Amount", min_value=0.0, value=0.0, step=1.0)
    concepto = st.text_input("Concept (optional)")

    if st.button("Register Payment"):
        if not selected_student:
            st.error("Please select a student")
        else:
            alumno_id = student_options[selected_student]

            abono_resp = requests.post(
                f"{API_URL}/abonos",
                json={
                    "alumno_id": alumno_id,
                    "monto": monto,
                    "concepto": concepto if concepto else None
                }
            )

            if abono_resp.status_code == 200:
                st.success("Payment registered successfully")
                st.json(abono_resp.json())
            else:
                st.error("Error registering payment")
                st.json(abono_resp.json())

# ---------------------------------------------------
# Check Balance
# ---------------------------------------------------
elif menu == "Check Balance":
    st.header("Check Balance")

    students = get_students()

    student_options = {
        f"{s['alumno']} - {s['grupo']} (ID: {s['id']})": s["id"]
        for s in students
    }

    selected_student = st.selectbox(
        "Select student",
        options=list(student_options.keys()) if student_options else []
    )

    if st.button("Check Balance"):
        if not selected_student:
            st.error("Please select a student")
        else:
            alumno_id = student_options[selected_student]
            saldo_resp = requests.get(f"{API_URL}/alumnos/{alumno_id}/saldo")

            if saldo_resp.status_code == 200:
                saldo = saldo_resp.json()
                st.success("Balance found")
                st.write(f"Student: {saldo['alumno']}")
                st.write(f"Group: {saldo['grupo']}")
                st.write(f"Total Sales: {saldo['total_ventas']}")
                st.write(f"Total Payments: {saldo['total_abonos']}")
                st.write(f"Pending Balance: {saldo['saldo_pendiente']}")
            else:
                st.error("Error getting balance")
                st.json(saldo_resp.json())

# ---------------------------------------------------
# Account Statement
# ---------------------------------------------------
elif menu == "Account Statement":
    st.header("Account Statement")

    students = get_students()

    student_options = {
        f"{s['alumno']} - {s['grupo']} (ID: {s['id']})": s["id"]
        for s in students
    }

    selected_student = st.selectbox(
        "Select student",
        options=list(student_options.keys()) if student_options else []
    )

    if st.button("Get Account Statement"):
        if not selected_student:
            st.error("Please select a student")
        else:
            alumno_id = student_options[selected_student]
            estado_resp = requests.get(f"{API_URL}/alumnos/{alumno_id}/estado_cuenta")

            if estado_resp.status_code == 200:
                estado = estado_resp.json()
                st.success("Account statement loaded")

                st.subheader("Student Information")
                st.write(f"Student: {estado['alumno']}")
                st.write(f"Group: {estado['grupo']}")
                st.write(f"Total Sales: {estado['total_ventas']}")
                st.write(f"Total Payments: {estado['total_abonos']}")
                st.write(f"Pending Balance: {estado['saldo_pendiente']}")

                st.subheader("Sales")
                st.dataframe(estado["ventas"])

                st.subheader("Payments")
                st.dataframe(estado["abonos"])
            else:
                st.error("Error getting account statement")
                st.json(estado_resp.json())

# ---------------------------------------------------
# Download Excel Report
# ---------------------------------------------------
elif menu == "Download Excel Report":
    st.header("Download Excel Report")

    if st.button("Generate and Download Report"):
        resp = requests.get(f"{API_URL}/estado-cuenta/excel")

        if resp.status_code == 200:
            st.success("Report generated successfully")

            st.download_button(
                label="Download Excel Report",
                data=resp.content,
                file_name="estado_cuenta.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Error generating report")