# Tests de la API de gestión de tareas con pytest y FastAPI TestClient
#
# COBERTURA:
#   Happy path
#     - POST   /tasks       → crear tarea correctamente
#     - GET    /tasks       → listar tareas (vacío y con datos)
#   Casos de error
#     - POST   /tasks       con título vacío o menor de 3 caracteres → 422
#     - GET    /tasks/{id}  con id inexistente → 404
#     - PATCH  /tasks/{id}  sobre una tarea con estado "done" → 400
#     - PATCH  /tasks/{id}  con id inexistente → 404
#     - DELETE /tasks/{id}  con id inexistente → 404
#   Prioridad — happy path
#     - POST   /tasks       → prioridad por defecto "medium"
#     - POST   /tasks       → prioridad explícita "high" / "low"
#     - PATCH  /tasks/{id}  → actualizar prioridad
#     - GET    /tasks?priority= → filtrado por prioridad
#   Prioridad — casos de error
#     - POST   /tasks       con prioridad inválida → 422
#     - PATCH  /tasks/{id}  con prioridad inválida → 422
#     - GET    /tasks?priority= con valor inválido → 422

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
    # 1. Crear tablas en el engine de test antes de instanciar el TestClient;
    #    principal.py ya no llama create_all al importarse (usa lifespan),
    #    así que aquí tenemos control total sobre qué engine se usa
    Base.metadata.create_all(bind=engine_test)

    # 2. Sobreescribir la dependencia de BD para que todas las peticiones usen engine_test
    app.dependency_overrides[get_db] = override_get_db

    # 3. TestClient sin context manager: no dispara el lifespan de la app,
    #    evitando que el create_all de producción interfiera con engine_test
    yield TestClient(app)

    # 4. Limpieza al terminar cada test
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# ---------------------------------------------------------------------------
# Happy path: crear tarea
# ---------------------------------------------------------------------------

def test_crear_tarea_correctamente(client):
    # Verifica que una tarea válida se crea y devuelve los campos esperados
    payload = {
        "title": "Tarea de prueba",
        "description": "Descripción de ejemplo",
        "categoria": "trabajo",
    }
    response = client.post("/tasks/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea de prueba"
    assert data["description"] == "Descripción de ejemplo"
    assert data["status"] == "pending"
    assert data["categoria"] == "trabajo"
    assert "id" in data
    assert "created_at" in data


def test_crear_tarea_sin_categoria(client):
    # Verifica que el campo categoria es opcional y acepta valor nulo
    payload = {"title": "Tarea sin categoría"}
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201
    assert response.json()["categoria"] is None


def test_actualizar_categoria_tarea(client):
    # Verifica que se puede actualizar el campo categoria de una tarea existente
    created = client.post("/tasks/", json={"title": "Tarea", "categoria": "trabajo"})
    task_id = created.json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"categoria": "hogar"})
    assert response.status_code == 200
    assert response.json()["categoria"] == "hogar"


# ---------------------------------------------------------------------------
# Happy path: listar tareas
# ---------------------------------------------------------------------------

def test_listar_tareas_vacio(client):
    # Sin tareas creadas la respuesta debe ser una lista vacía
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert response.json() == []


def test_listar_tareas_con_datos(client):
    # Crea dos tareas y comprueba que ambas aparecen en el listado
    client.post("/tasks/", json={"title": "Primera tarea", "categoria": "personal"})
    client.post("/tasks/", json={"title": "Segunda tarea", "categoria": "personal"})

    response = client.get("/tasks/")

    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Casos de error
# ---------------------------------------------------------------------------

def test_crear_tarea_titulo_vacio(client):
    # Título vacío incumple min_length=3 en TaskCreate → 422 de validación de Pydantic
    response = client.post("/tasks/", json={"title": ""})

    assert response.status_code == 422


def test_crear_tarea_titulo_demasiado_corto(client):
    # Un título de 2 caracteres también incumple min_length=3 → 422
    response = client.post("/tasks/", json={"title": "ab"})

    assert response.status_code == 422


def test_obtener_tarea_no_encontrada(client):
    # GET sobre un id inexistente debe devolver 404 con detalle "Tarea no encontrada"
    response = client.get("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"


def test_actualizar_tarea_completada(client):
    # Crea una tarea ya en estado "done"; cualquier PATCH posterior debe rechazarse
    created = client.post(
        "/tasks/",
        json={"title": "Tarea hecha", "status": "done", "categoria": "trabajo"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo titulo"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot modify a completed task"


def test_actualizar_tarea_no_encontrada(client):
    # PATCH sobre un id inexistente debe devolver 404
    response = client.patch("/tasks/9999", json={"title": "Cualquier cosa"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"


def test_eliminar_tarea_no_encontrada(client):
    # DELETE sobre un id inexistente debe devolver 404
    response = client.delete("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ---------------------------------------------------------------------------
# Prioridad: happy path
# ---------------------------------------------------------------------------

def test_crear_tarea_prioridad_por_defecto(client):
    # Sin indicar prioridad, la tarea se crea con prioridad "medium"
    response = client.post("/tasks/", json={"title": "Tarea sin prioridad"})

    assert response.status_code == 201
    assert response.json()["priority"] == "medium"


def test_crear_tarea_con_prioridad_high(client):
    # Se puede crear una tarea con prioridad explícita "high"
    response = client.post(
        "/tasks/", json={"title": "Tarea urgente", "priority": "high"}
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "high"


def test_crear_tarea_con_prioridad_low(client):
    # Se puede crear una tarea con prioridad explícita "low"
    response = client.post(
        "/tasks/", json={"title": "Tarea tranquila", "priority": "low"}
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "low"


def test_actualizar_prioridad_tarea(client):
    # Se puede cambiar la prioridad de una tarea existente mediante PATCH
    created = client.post("/tasks/", json={"title": "Tarea editable"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"priority": "high"})

    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_listar_tareas_filtrar_por_prioridad(client):
    # El query parameter ?priority= filtra correctamente las tareas
    client.post("/tasks/", json={"title": "Baja prioridad", "priority": "low"})
    client.post("/tasks/", json={"title": "Alta prioridad", "priority": "high"})
    client.post("/tasks/", json={"title": "Media prioridad"})

    response = client.get("/tasks/?priority=high")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority"] == "high"


def test_listar_tareas_sin_filtro_devuelve_todas(client):
    # Sin query parameter se devuelven todas las tareas independientemente de la prioridad
    client.post("/tasks/", json={"title": "Tarea uno", "priority": "low"})
    client.post("/tasks/", json={"title": "Tarea dos", "priority": "high"})

    response = client.get("/tasks/")

    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Prioridad: casos de error
# ---------------------------------------------------------------------------

def test_crear_tarea_prioridad_invalida(client):
    # Un valor de prioridad no válido debe devolver 422
    response = client.post(
        "/tasks/", json={"title": "Tarea rota", "priority": "urgent"}
    )

    assert response.status_code == 422


def test_actualizar_prioridad_invalida(client):
    # Intentar actualizar con un valor de prioridad no válido debe devolver 422
    created = client.post("/tasks/", json={"title": "Tarea para patch"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"priority": "critical"})

    assert response.status_code == 422


def test_filtrar_prioridad_invalida(client):
    # Un query parameter con prioridad no válida debe devolver 422
    response = client.get("/tasks/?priority=urgent")

    assert response.status_code == 422
