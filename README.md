# API de Gestión de Tareas

API REST para gestionar el ciclo de vida de tareas (crear, consultar, actualizar y eliminar). Construida con **FastAPI**, **SQLAlchemy 2.0** y **SQLite** como base de datos local. Diseñada como servicio backend para seguimiento de tareas con almacenamiento persistente.

## Requisitos previos

| Requisito | Versión mínima |
|---|---|
| Python | 3.12+ |
| pip | incluido con Python |
| venv | incluido con Python |

## Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/cvidalh/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. Crear y activar el entorno virtual:

   ```bash
   python -m venv venv

   # Linux / macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

## Arranque de la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

| Recurso | URL |
|---|---|
| API base | `http://127.0.0.1:8000` |
| Documentación interactiva (Swagger UI) | `http://127.0.0.1:8000/docs` |

La base de datos SQLite (`tareas.db`) se crea automáticamente en el directorio raíz del proyecto al arrancar la aplicación por primera vez.

## Modelo de datos

### Entidad `Task`

| Campo | Tipo | Obligatorio | Valor por defecto | Descripción |
|---|---|---|---|---|
| `id` | `Integer` | auto | autoincremental | Identificador único de la tarea |
| `title` | `String(255)` | sí | — | Título de la tarea (mínimo 3 caracteres) |
| `description` | `String` | no | `null` | Descripción opcional de la tarea |
| `status` | `TaskStatus` | sí | `pending` | Estado actual de la tarea |
| `created_at` | `DateTime` | auto | fecha/hora UTC actual | Fecha de creación (asignada automáticamente) |

### Enum `TaskStatus`

| Valor | Descripción |
|---|---|
| `pending` | Tarea pendiente |
| `in_progress` | Tarea en progreso |
| `done` | Tarea completada |

## Documentación de endpoints

### `GET /tasks/` — Listar todas las tareas

Devuelve la lista completa de tareas almacenadas.

**Parámetros:** ninguno.

**Ejemplo:**

```bash
curl http://127.0.0.1:8000/tasks/
```

**Response — `200 OK`:**

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Actualizar el README del proyecto",
    "status": "pending",
    "created_at": "2025-01-15T10:30:00"
  }
]
```

---

### `GET /tasks/{task_id}` — Obtener una tarea por id

Devuelve una tarea específica según su identificador.

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `task_id` | `int` | sí | Identificador de la tarea |

**Ejemplo:**

```bash
curl http://127.0.0.1:8000/tasks/1
```

**Response — `200 OK`:**

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "pending",
  "created_at": "2025-01-15T10:30:00"
}
```

**Error — `404 Not Found`:**

```bash
curl http://127.0.0.1:8000/tasks/9999
```

```json
{
  "detail": "Task not found"
}
```

---

### `POST /tasks/` — Crear una nueva tarea

Crea una tarea y devuelve el recurso creado.

**Parámetros del cuerpo (JSON):**

| Campo | Tipo | Obligatorio | Valor por defecto | Descripción |
|---|---|---|---|---|
| `title` | `string` | sí | — | Título de la tarea (mínimo 3 caracteres) |
| `description` | `string` | no | `null` | Descripción de la tarea |
| `status` | `string` | no | `"pending"` | Estado inicial (`pending`, `in_progress`, `done`) |

**Ejemplo:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Comprar café", "description": "Café molido de Colombia"}'
```

**Response — `201 Created`:**

```json
{
  "id": 1,
  "title": "Comprar café",
  "description": "Café molido de Colombia",
  "status": "pending",
  "created_at": "2025-01-15T10:30:00"
}
```

**Error — `422 Unprocessable Entity` (título demasiado corto):**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "ab"}'
```

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 3 characters",
      "input": "ab",
      "ctx": {"min_length": 3}
    }
  ]
}
```

---

### `PATCH /tasks/{task_id}` — Actualizar parcialmente una tarea

Modifica solo los campos enviados en el cuerpo de la petición. No permite modificar tareas con estado `done`.

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `task_id` | `int` | sí | Identificador de la tarea |

**Parámetros del cuerpo (JSON):**

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | `string` | no | Nuevo título (mínimo 3 caracteres) |
| `description` | `string` | no | Nueva descripción |
| `status` | `string` | no | Nuevo estado (`pending`, `in_progress`, `done`) |

**Ejemplo:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Response — `200 OK`:**

```json
{
  "id": 1,
  "title": "Comprar café",
  "description": "Café molido de Colombia",
  "status": "in_progress",
  "created_at": "2025-01-15T10:30:00"
}
```

**Error — `400 Bad Request` (tarea completada):**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Nuevo título"}'
```

```json
{
  "detail": "Cannot modify a completed task"
}
```

**Error — `404 Not Found`:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/9999 \
  -H "Content-Type: application/json" \
  -d '{"title": "Cualquier cosa"}'
```

```json
{
  "detail": "Task not found"
}
```

---

### `PATCH /tasks/{task_id}/complete` — Marcar una tarea como completada

Cambia el estado de la tarea a `done`. No requiere cuerpo en la petición. No permite completar una tarea que ya está en estado `done`.

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `task_id` | `int` | sí | Identificador de la tarea |

**Ejemplo:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1/complete
```

**Response — `200 OK`:**

```json
{
  "id": 1,
  "title": "Comprar café",
  "description": "Café molido de Colombia",
  "status": "done",
  "created_at": "2025-01-15T10:30:00",
  "categoria": null
}
```

**Error — `400 Bad Request` (tarea ya completada):**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1/complete
```

```json
{
  "detail": "La tarea ya está completada"
}
```

**Error — `404 Not Found`:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/9999/complete
```

```json
{
  "detail": "Tarea no encontrada"
}
```

---

### `DELETE /tasks/{task_id}` — Eliminar una tarea

Elimina una tarea de la base de datos. Devuelve `204` sin cuerpo.

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `task_id` | `int` | sí | Identificador de la tarea |

**Ejemplo:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

**Response — `204 No Content`:** sin cuerpo.

**Error — `404 Not Found`:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/9999
```

```json
{
  "detail": "Task not found"
}
```

## Reglas de negocio

- **Tareas completadas inmutables:** una tarea con estado `done` no admite modificaciones vía `PATCH`. La API devuelve `400 Bad Request` con el mensaje `"Cannot modify a completed task"`.
- **Longitud mínima del título:** el campo `title` debe tener al menos 3 caracteres, tanto al crear (`POST`) como al actualizar (`PATCH`). Valores más cortos devuelven `422 Unprocessable Entity`.
- **Estado por defecto:** las tareas se crean con estado `pending` si no se especifica otro.
- **Fecha de creación automática:** el campo `created_at` se asigna automáticamente con la fecha y hora UTC del momento de creación.

## Cómo ejecutar los tests

```bash
pytest tests/ -v
```

Los tests utilizan una base de datos **SQLite en memoria** con `StaticPool` para garantizar aislamiento entre casos de prueba. No tocan el archivo `tareas.db` de producción.

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/                 # Paquete principal de la aplicación
│   ├── principal.py            # Punto de entrada: instancia FastAPI y registro de routers
│   ├── base_de_datos.py        # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py              # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py             # Esquemas Pydantic de entrada y respuesta
│   └── rutas/                  # Directorio de routers
│       └── tareas.py           # Endpoints REST de tareas
├── tests/                      # Suite de tests automatizados
│   └── test_tasks.py           # Tests con pytest y SQLite en memoria
├── AGENTS.md                   # Especificaciones técnicas y convenciones de código
├── requirements.txt            # Dependencias del proyecto
├── .gitignore                  # Archivos excluidos del control de versiones
└── README.md                   # Este archivo
```
