# Definición de los endpoints REST para la gestión de tareas

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

# Router con prefijo /tasks; agrupa todos los endpoints de tareas
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    limit: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    """Devuelve la lista de tareas almacenadas, opcionalmente limitada.

    Args:
        limit: Número máximo de tareas a devolver. Si no se indica, devuelve todas.
        db: Sesión de base de datos inyectada por FastAPI.

    Returns:
        Lista de tareas ordenadas por la base de datos.
    """
    query = select(Task)
    if limit is not None:
        query = query.limit(limit)
    return db.scalars(query).all()


# Devuelve una tarea por su identificador; 404 si no existe
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task


# Crea una nueva tarea y devuelve el recurso creado con código 201
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Actualiza parcialmente una tarea; solo modifica los campos enviados en el cuerpo
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    # Una tarea ya completada no admite más cambios
    if task.status == TaskStatus.done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a completed task",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# Elimina una tarea de la base de datos; devuelve 204 sin cuerpo
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
