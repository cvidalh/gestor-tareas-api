# Definición de los modelos ORM que representan las tablas de la base de datos

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String

from aplicacion.base_de_datos import Base


# Enumeración con los estados posibles de una tarea
class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


# Enumeración con los niveles de prioridad de una tarea
class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


# Modelo que representa la tabla "tasks" en la base de datos
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium, nullable=False)
    # La fecha de creación se asigna automáticamente al insertar el registro
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
