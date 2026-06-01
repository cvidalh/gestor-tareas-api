# Tests de regresión para validaciones de negocio en tareas
#
# COBERTURA:
#   Validación de título
#     - POST   /tasks       con título vacío → 422
#     - POST   /tasks       con título < 3 caracteres → 422
#     - PATCH  /tasks/{id}  con título < 3 caracteres → 422
#   Inmutabilidad de tareas completadas
#     - PATCH  /tasks/{id}  sobre tarea con estado "done" → 400
#   Happy path básico
#     - POST   /tasks       con datos válidos → 201
#     - GET    /tasks/      listar tareas
#     - GET    /tasks/{id}  obtener tarea existente
#     - PATCH  /tasks/{id}  actualizar tarea pendiente → 200
#   Casos de error adicionales
#     - GET    /tasks/{id}  con id inexistente → 404
#     - PATCH  /tasks/{id}  con id inexistente → 404
#     - DELETE /tasks/{id}  con id inexistente → 404

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# StaticPool garantiza que todas las sesiones comparten la misma conexión en memoria;
# sin él cada sesión abriría una conexión nueva y vería una base de datos vacía distinta
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    # Sustituye la dependencia de BD real por la sesión de test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine_test)
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# ---------------------------------------------------------------------------
# Regresión: validación min_length=3 en título (POST)
# ---------------------------------------------------------------------------

def test_crear_tarea_titulo_vacio_rechazado(client):
    # Un título vacío debe ser rechazado por la validación min_length=3
    response = client.post("/tasks/", json={"title": ""})

    assert response.status_code == 422


def test_crear_tarea_titulo_corto_rechazado(client):
    # Un título de 2 caracteres incumple min_length=3 → 422
    response = client.post("/tasks/", json={"title": "ab"})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Regresión: validación min_length=3 en título (PATCH)
# ---------------------------------------------------------------------------

def test_actualizar_titulo_corto_rechazado(client):
    # Crear tarea válida y luego intentar actualizar con título < 3 caracteres
    created = client.post("/tasks/", json={"title": "Tarea válida"})
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "ab"})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Regresión: bloquear modificación de tareas completadas
# ---------------------------------------------------------------------------

def test_modificar_tarea_completada_rechazado(client):
    # Crea una tarea con estado "done"; cualquier PATCH posterior debe rechazarse
    created = client.post(
        "/tasks/",
        json={"title": "Tarea hecha", "status": "done"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo titulo"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot modify a completed task"


def test_modificar_descripcion_tarea_completada_rechazado(client):
    # Incluso cambiar solo la descripción de una tarea done debe bloquearse
    created = client.post(
        "/tasks/",
        json={"title": "Tarea terminada", "status": "done"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}", json={"description": "Nueva descripción"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot modify a completed task"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_crear_tarea_correctamente(client):
    # Verifica que una tarea válida se crea y devuelve los campos esperados
    payload = {
        "title": "Tarea de prueba",
        "description": "Descripción de ejemplo",
    }
    response = client.post("/tasks/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea de prueba"
    assert data["description"] == "Descripción de ejemplo"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


def test_listar_tareas_vacio(client):
    # Sin tareas creadas la respuesta debe ser una lista vacía
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert response.json() == []


def test_listar_tareas_con_datos(client):
    # Crea dos tareas y comprueba que ambas aparecen en el listado
    client.post("/tasks/", json={"title": "Primera tarea"})
    client.post("/tasks/", json={"title": "Segunda tarea"})

    response = client.get("/tasks/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_actualizar_tarea_pendiente(client):
    # Actualizar una tarea pendiente debe permitirse sin problemas
    created = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = created.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}", json={"title": "Tarea actualizada"}
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Tarea actualizada"


# ---------------------------------------------------------------------------
# Casos de error: recurso no encontrado
# ---------------------------------------------------------------------------

def test_obtener_tarea_no_encontrada(client):
    # GET sobre un id inexistente debe devolver 404
    response = client.get("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_actualizar_tarea_no_encontrada(client):
    # PATCH sobre un id inexistente debe devolver 404
    response = client.patch("/tasks/9999", json={"title": "Cualquier cosa"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_eliminar_tarea_no_encontrada(client):
    # DELETE sobre un id inexistente debe devolver 404
    response = client.delete("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
