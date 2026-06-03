---
name: test-api
description: Ejecutar los tests de la API gestor-tareas-api y verificar que pasan correctamente.
---

## Configuración

1. Activa el entorno virtual: `venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Linux/Mac)
2. Instala las dependencias si es necesario: `pip install -r requirements.txt`

## Ejecución de tests

1. Ejecuta la suite completa: `python -m pytest tests/ -v`
2. Lee el output completo — presta atención a los FAILED y ERROR
3. Si algún test falla, identifica el archivo y la línea del fallo

## Verificación de cobertura

1. Ejecuta: `python -m pytest tests/ --cov=aplicacion --cov-report=term-missing`
2. Anota los módulos con cobertura inferior al 80%

## Antes de abrir un PR

1. Todos los tests deben pasar (0 failed, 0 error)
2. La cobertura no debe haber disminuido respecto al estado anterior
3. Si añadiste código nuevo, debe tener al menos un test
EOF
