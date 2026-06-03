---
name: run-local
description: Arrancar la API localmente, verificar que responde y ejecutar una prueba básica de los endpoints.
---

## Contexto actual

- Rama activa: !`git branch --show-current`
- Último commit: !`git log --oneline -1`

## Arranque

1. Activa el entorno virtual
2. Instala dependencias: `pip install -r requirements.txt`
3. Arranca la API: `uvicorn aplicacion.principal:app --reload --port 8000`
4. Espera a que aparezca "Application startup complete"

## Verificación básica

1. Comprueba que la API responde: `curl http://localhost:8000/tasks/`
2. Crea una tarea de prueba:
  `curl -X POST http://localhost:8000/tasks/ -H "Content-Type: application/json" -d "{\"title\": \"Test skill\"}"`
3. Verifica que la tarea aparece en el listado
4. Elimina la tarea de prueba

## Resultado esperado

- La API arranca sin errores
- El endpoint GET /tasks/ devuelve 200
- El endpoint POST /tasks/ crea la tarea correctamente
