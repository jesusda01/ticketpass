# App de Control y Compra de Tickets a Eventos.

Aplicación web responsiva para gestionar la compra de tickets a eventos, compuesta por:

- Backend en **Python FastAPI** con base de datos **SQLite**.
- Frontend en **HTML, CSS y JavaScript**.

---

## Tecnologías utilizadas

- Python 3.x  
- FastAPI  
- Uvicorn (servidor ASGI para desarrollo)  
- SQLite (base de datos embebida)  
- HTML5, CSS3 y JavaScript

--- 

## BackEnd - Instrucciones

### Instalar dependencias:
pip install fastapi uvicorn sqlalchemy pydantic

### Ejecutar el backend:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload