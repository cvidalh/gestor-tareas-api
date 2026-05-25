# Punto de entrada de la aplicación FastAPI

from contextlib import asynccontextmanager

from fastapi import FastAPI

from aplicacion.base_de_datos import Base, engine
from aplicacion.rutas import tareas


# Crea las tablas al arrancar la app; usar lifespan evita que se ejecute al importar el módulo
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


# Instancia principal de la aplicación
app = FastAPI(title="API de Gestión de Tareas", lifespan=lifespan)

# Registro del router de tareas bajo el prefijo /tasks
app.include_router(tareas.router)
