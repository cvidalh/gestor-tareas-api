# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Contexto

La API de gestión de tareas necesita una base de datos para persistir las tareas creadas por los usuarios. El proyecto es una aplicación de alcance reducido, orientada a un único servidor y con un volumen de datos bajo-moderado. Se requiere una solución que:

- Permita desarrollo local sin dependencias externas.
- Sea fácil de desplegar y configurar.
- Ofrezca un rendimiento adecuado para el patrón de uso esperado (operaciones CRUD sencillas, sin consultas analíticas complejas).
- Sea compatible con SQLAlchemy 2.0 y el stack de Python 3.12+.

## Decisión

Se adopta **SQLite** como motor de base de datos, almacenando los datos en el archivo `tareas.db` en la raíz del proyecto.

### Razones principales

1. **Cero configuración**: SQLite no requiere instalar ni administrar un servidor de base de datos independiente. El archivo se crea automáticamente en el primer arranque.
2. **Portabilidad**: El archivo de la base de datos es autocontenido y puede copiarse, respaldarse o versionarse de forma trivial.
3. **Rendimiento suficiente**: Para el volumen de concurrencia esperado (usuario único o pocos usuarios simultáneos), SQLite ofrece tiempos de respuesta comparables o superiores a soluciones cliente-servidor.
4. **Soporte nativo en Python**: El módulo `sqlite3` forma parte de la biblioteca estándar, eliminando dependencias adicionales.
5. **Ideal para testing**: SQLite en modo `:memory:` con `StaticPool` permite tests rápidos y aislados sin infraestructura adicional.
6. **Coherencia con el alcance del proyecto**: Al tratarse de una API de gestión de tareas de complejidad limitada, no se justifica la sobrecarga operativa de un SGBD completo.

## Alternativas consideradas

### PostgreSQL

| Aspecto | Detalle |
|---------|---------|
| **Ventajas** | Soporte completo de concurrencia (MVCC), tipos de datos avanzados (JSON, arrays, rangos), extensiones (PostGIS, pg_trgm), replicación nativa, amplio ecosistema de herramientas de monitorización y backup. |
| **Inconvenientes** | Requiere instalar y mantener un servidor independiente. Añade complejidad al entorno de desarrollo (Docker o instalación local). Mayor consumo de recursos. Sobredimensionado para el volumen de datos y concurrencia actual del proyecto. |

### MySQL

| Aspecto | Detalle |
|---------|---------|
| **Ventajas** | Amplia adopción en la industria, buena documentación, rendimiento probado en aplicaciones web de lectura intensiva, herramientas maduras de administración (phpMyAdmin, MySQL Workbench). |
| **Inconvenientes** | Requiere servidor independiente al igual que PostgreSQL. Tipado menos estricto que PostgreSQL (modos `STRICT` deben activarse explícitamente). Menor riqueza de tipos nativos. Licencia dual (GPL/comercial) puede ser un factor en algunos contextos. |

## Consecuencias

### Positivas

- El entorno de desarrollo se simplifica: `pip install -r requirements.txt` es suficiente para empezar a trabajar.
- Los tests se ejecutan sin infraestructura externa, lo que acelera el ciclo de feedback.
- El despliegue en entornos sencillos (VPS, contenedor único) no requiere orquestar servicios adicionales.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite usa un bloqueo a nivel de archivo para escrituras. Si el proyecto escala a múltiples escritores concurrentes, habrá contención y errores `database is locked`.
- **Sin replicación nativa**: No es posible configurar réplicas de lectura ni alta disponibilidad sin herramientas externas (Litestream, LiteFS).
- **Funcionalidades SQL reducidas**: Faltan características como `ALTER COLUMN`, soporte parcial de `RIGHT JOIN`, y no hay tipos fecha/hora nativos con aritmética completa.
- **Migración futura**: Si el proyecto crece significativamente, será necesario migrar a PostgreSQL u otro motor. Gracias a SQLAlchemy, el ORM abstrae gran parte de la lógica de acceso a datos, lo que reduce el coste de esta migración.

### Plan de mitigación

- Monitorizar tiempos de respuesta bajo carga. Si se detecta contención, evaluar migración a PostgreSQL.
- Mantener la lógica de acceso a datos desacoplada del motor mediante SQLAlchemy para facilitar el cambio futuro.
- No usar funcionalidades específicas de SQLite que no existan en PostgreSQL, preservando la portabilidad del código.
