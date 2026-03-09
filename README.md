Cafeteria AI Assistant

Backend system for managing sales in a school cafeteria. The system stores students and products in a database, registers purchases, and generates Excel reports automatically. It is designed to evolve into a Telegram bot powered by AI that can register sales using natural language.

Problem
Many school cafeterias track sales manually or with unstructured spreadsheets. This often causes inaccurate records, difficulty generating reports, lack of traceability by student or group, and slow purchase registration. This project provides a structured backend system that records purchases and generates automated reports.

Features
•	Product catalog management
•	Student import from Excel
•	Purchase registration
•	Automatic price calculation
•	Sales queries
•	Excel report generation
•	Automatic API documentation with Swagger

Tech Stack
•	Python
•	FastAPI
•	SQLAlchemy
•	SQLite
•	Pandas
•	OpenPyXL

Architecture
User / Telegram Bot → FastAPI API → SQLAlchemy ORM → SQLite Database → Excel Reports (Pandas)

Project Structure
cafeteria-ai
│
├── app
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   └── import_alumnos.py
│
├── cafeteria.db
├── alumnos.xlsx
├── requirements.txt
├── README.md
└── .gitignore

Database Schema
Students
Fields: id, alumno, grupo
Products
Fields: id, nombre, precio
Sales
Fields: id, alumno_id, producto_id, cantidad, total, fecha

API Endpoints
•	GET /  → API status
•	GET /alumnos → list students
•	GET /productos → list products
•	POST /ventas → register a sale
•	GET /ventas → list sales
•	GET /ventas/excel → generate Excel report

How to Run the Project
Install dependencies:
py -m pip install -r requirements.txt
Load initial products:
py -m app.seed
Import students from Excel:
py -m app.import_alumnos
Start the API server:
py -m uvicorn app.main:app --reload
Open API documentation in browser:
http://127.0.0.1:8000/docs

Future Improvements
•	Telegram bot integration
•	AI-powered natural language purchase input
•	Automatic disambiguation when students share the same name
•	Filtered reports by group
•	Filtered reports by date
•	Web dashboard for administrators

Author
Gerardo Olivares
Software Engineering Student.

License
MIT License
