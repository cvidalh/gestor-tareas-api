# Instrucciones para Devin — API de Gestión de Tareas

## Descripción del proyecto

API REST para gestionar tareas construida con FastAPI y SQLAlchemy. Permite crear, consultar, actualizar y eliminar tareas. Cada tarea tiene un identificador, título, descripción opcional, estado (`pending`, `in_progress`, `done`) y fecha de creación automática.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework web | FastAPI 0.136 |
| ORM | SQLAlchemy 2.0 |
| Validación | Pydantic 2 |
| Base de datos | SQLite (archivo `tareas.db`) |
| Servidor | Uvicorn |
| Tests | pytest + httpx (TestClient de FastAPI) |
| Python | 3.12+ |

## Estructura del proyecto

```
task-manager-api/
├── aplicacion/
│   ├── principal.py       # Punto de entrada: instancia FastAPI y registra routers
│   ├── base_de_datos.py   # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py         # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py        # Esquemas Pydantic de entrada y respuesta
│   └── rutas/
│       └── tareas.py      # Endpoints REST de tareas
├── tests/
│   └── test_tasks.py      # Tests con pytest y SQLite en memoria
├── requirements.txt
└── .devin/
    └── instructions.md
```

## Cómo arrancar la API

1. Crear y activar el entorno virtual:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Arrancar el servidor de desarrollo:
   ```bash
   uvicorn aplicacion.principal:app --reload
   ```

La API quedará disponible en `http://127.0.0.1:8000`.
La documentación interactiva (Swagger UI) en `http://127.0.0.1:8000/docs`.

## Cómo ejecutar los tests

```bash
pytest tests/ -v
```

Los tests usan una base de datos SQLite en memoria con `StaticPool` para garantizar aislamiento entre casos. No tocan el archivo `tareas.db` de producción.

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/tasks/` | Lista todas las tareas |
| GET | `/tasks/{id}` | Obtiene una tarea por id |
| POST | `/tasks/` | Crea una nueva tarea |
| PATCH | `/tasks/{id}` | Actualiza parcialmente una tarea |
| DELETE | `/tasks/{id}` | Elimina una tarea |

## Convenciones de código que Devin debe respetar

### Idioma
- El **código** (variables, funciones, clases, rutas de URL) se escribe en **inglés**.
- Los **comentarios** y la **documentación** se escriben en **castellano**.
- Los nombres de **archivos y carpetas** del proyecto están en **castellano** (`modelos.py`, `esquemas.py`, `rutas/`).

### Estilo
- Seguir PEP 8. Sin líneas de más de 100 caracteres.
- Importaciones agrupadas: stdlib → third-party → proyecto, separadas por línea en blanco.
- No añadir comentarios que expliquen lo que ya dice el nombre del símbolo; solo comentar el **por qué** cuando no es obvio.

### Base de datos
- Toda lógica de acceso a datos va en las funciones de `aplicacion/rutas/tareas.py` usando la sesión inyectada por `get_db`.
- No crear sesiones manualmente fuera de `get_db`.

### Esquemas y modelos
- Los esquemas Pydantic de entrada (`TaskCreate`, `TaskUpdate`) son los únicos que Devin debe modificar para añadir campos nuevos; el modelo ORM `Task` en `modelos.py` debe actualizarse en paralelo.
- `TaskResponse` debe incluir siempre todos los campos que devuelve la BD.

### Tests
- Cada test nuevo debe usar el fixture `client` definido en `test_tasks.py`.
- No conectar a la base de datos de producción (`tareas.db`) desde los tests.
- Los tests de casos de error deben verificar tanto el código de estado HTTP como el campo `detail` del cuerpo de respuesta.

### Git
- Un commit por cambio lógico; mensaje en formato `tipo: descripción breve` (feat, fix, refactor, docs, pruebas).
- No hacer commit de `tareas.db`, `__pycache__/` ni archivos `.pyc`.

### Nuevos endpoints
- Todos los endpoints nuevos deben incluir al menos un test de caso error además del happy path obligatoriamente.
