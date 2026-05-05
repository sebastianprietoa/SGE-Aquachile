# SGE Aquachile

Aplicación web para monitoreo y gestión de Sistemas de Gestión de Energía basada en ISO 50001 y el Decreto 28 de Eficiencia Energética de Chile.

El foco del sistema es la **carga manual o asistida** de información energética mensual, con trazabilidad completa, cálculo de desempeño, alertas y dashboards.

## Alcance MVP

- Dos sistemas energéticos separados:
  - ELF - Exportadora Los Fiordos
  - Empresas AquaChile / AquaChile Magallanes
- Gestión de:
  - sistemas energéticos
  - áreas o instalaciones
  - usos energéticos
  - líneas base energéticas
  - variables asociadas a cada línea base
  - IDEs
  - mediciones mensuales
  - auditoría de cambios
  - alertas
  - dashboard operativo
- Autenticación inicial simple con JWT y usuario seed.

## Stack

- Backend: FastAPI + Python
- Frontend: Next.js + TypeScript + TailwindCSS + shadcn/ui style components + Recharts
- Base de datos: PostgreSQL
- ORM: SQLAlchemy
- Validación: Pydantic
- Contenedores: Docker Compose

## Estructura

```text
/backend
  /app
    /api
    /core
    /db
    /models
    /schemas
    /services
    /repositories
    /utils
    main.py
  requirements.txt
  Dockerfile
/frontend
  /app
  /components
  /lib
  /types
  package.json
  Dockerfile
/docker-compose.yml
/.env.example
```

## Datos seed

Se crean datos iniciales para:

- ELF
- AquaChile / AquaChile Magallanes

Incluye:

- 2 áreas por sistema
- 2 usos energéticos por sistema
- 1 línea base por sistema
- variables asociadas a cada línea base
- 1 IDE por sistema
- registros mensuales de ejemplo
- alertas de ejemplo
- usuario seed:
  - `admin`
  - `Admin1234!`

## Endpoints principales

- `GET /systems`
- `GET /systems/{system_id}`
- `GET /systems/{system_id}/areas`
- `POST /systems/{system_id}/areas`
- `PUT /areas/{area_id}`
- `GET /systems/{system_id}/energy-uses`
- `POST /systems/{system_id}/energy-uses`
- `PUT /energy-uses/{energy_use_id}`
- `GET /systems/{system_id}/baselines`
- `GET /baselines/{baseline_id}`
- `POST /systems/{system_id}/baselines`
- `PUT /baselines/{baseline_id}`
- `GET /baselines/{baseline_id}/variables`
- `POST /baselines/{baseline_id}/variables`
- `PUT /baseline-variables/{variable_id}`
- `GET /systems/{system_id}/ides`
- `POST /systems/{system_id}/ides`
- `PUT /ides/{ide_id}`
- `GET /systems/{system_id}/measurements`
- `GET /measurements/{measurement_id}`
- `POST /systems/{system_id}/measurements`
- `PUT /measurements/{measurement_id}`
- `POST /measurements/{measurement_id}/submit`
- `POST /measurements/{measurement_id}/approve`
- `POST /measurements/{measurement_id}/reject`
- `GET /measurements/{measurement_id}/audit-log`
- `GET /systems/{system_id}/alerts`
- `GET /measurements/{measurement_id}/alerts`
- `POST /alert-rules`
- `PUT /alert-rules/{alert_rule_id}`
- `GET /systems/{system_id}/dashboard`
- `GET /systems/{system_id}/performance-summary`
- `GET /systems/{system_id}/monthly-trends`

## Cálculo

### Consumo esperado

```text
expected_consumption = intercept + suma(coeficiente_i * variable_i)
```

### Diferencia

```text
difference = real_consumption - expected_consumption
```

### Desviación porcentual

```text
percentage_difference = difference / expected_consumption * 100
```

### Cumplimiento

- `compliant`: desviación menor o igual a 10%
- `warning`: desviación mayor a 10% y menor o igual a 20%
- `non_compliant`: desviación mayor a 20%
- `incomplete`: faltan datos o no se puede calcular

## Ejecución local

### Modo CSV local

Para desarrollo local rápido, la aplicación usa CSV como backend de datos.

```bash
cd backend
python -m app.utils.seed_csv --reset
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

En otra terminal:

```bash
cd frontend
npm run dev
```

Abrir:

```text
http://localhost:3000
```

Variables relevantes:

- `DATA_BACKEND=csv`
- Los CSV quedan en `backend/data/csv/`

### Con Docker

```bash
docker compose up --build
```

Servicios:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

### Seed de acceso

```text
usuario: admin
password: Admin1234!
```

## Desarrollo sin Docker

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pytest
```

## Notas de diseño

- El Excel queda solo como referencia histórica.
- El flujo principal es carga manual/asistida.
- Las variables permitidas se restringen por línea base.
- Cada edición deja trazabilidad en `MeasurementAuditLog`.
- Los registros aprobados no dependen de cambios automáticos de la línea base.
