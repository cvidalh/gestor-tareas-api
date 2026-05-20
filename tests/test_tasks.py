import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _create_task(title="Test task", description="desc", status="pending"):
    return client.post(
        "/tasks/",
        json={"title": title, "description": description, "status": status},
    )


def test_update_task_with_done_status_returns_400():
    """Updating a task that already has status 'done' must return 400."""
    resp = _create_task(status="done")
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "new title"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot modify a completed task"


def test_update_pending_task_succeeds():
    """Updating a task with status 'pending' must succeed normally."""
    resp = _create_task(status="pending")
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "updated"


def test_update_in_progress_task_succeeds():
    """Updating a task with status 'in_progress' must succeed normally."""
    resp = _create_task(status="in_progress")
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"description": "new desc"})
    assert resp.status_code == 200
    assert resp.json()["description"] == "new desc"


def test_transition_to_done_then_reject_further_updates():
    """A task moved to 'done' via PATCH must reject any subsequent update."""
    resp = _create_task(status="pending")
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"

    resp = client.patch(f"/tasks/{task_id}", json={"title": "should fail"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot modify a completed task"


def test_list_tasks_by_status_returns_filtered_results():
    """GET /tasks/status/{status} devuelve solo las tareas con ese estado."""
    _create_task(title="Pending task", status="pending")
    _create_task(title="Done task", status="done")
    _create_task(title="In progress task", status="in_progress")

    resp = client.get("/tasks/status/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Pending task"
    assert data[0]["status"] == "pending"

    resp = client.get("/tasks/status/done")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Done task"

    resp = client.get("/tasks/status/in_progress")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "In progress task"


def test_list_tasks_by_status_returns_empty_list_when_no_matches():
    """GET /tasks/status/{status} devuelve lista vacía si no hay tareas con ese estado."""
    _create_task(title="Done task", status="done")

    resp = client.get("/tasks/status/pending")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_by_status_rejects_invalid_status():
    """GET /tasks/status/{status} con un valor no válido devuelve 422."""
    resp = client.get("/tasks/status/invalid_value")
    assert resp.status_code == 422
