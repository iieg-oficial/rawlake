# feat: reducir esquema de metadatos a modelo beta (3 entidades)

## Resumen

Este PR acota el alcance del esquema de metadatos de RawLake a tres entidades principales (`datasets`, `ingestions`, `archivos`) para habilitar la primera beta operativa del sistema.

El objetivo es tener un flujo mínimo funcional que permita descargar o registrar insumos, almacenarlos en la landing zone, y mantener una auditoría básica para que los ETLs del warehouse puedan consultar la última descarga exitosa y localizar los archivos disponibles.

Las funcionalidades de catalogación más fina (distribuciones, configuración de extractores, recursos lógicos internos, esquemas de columnas) se posponen para iteraciones posteriores, una vez que existan casos reales corriendo sobre esta base.

## Cambios

### Modelo de datos

| Antes (7 tablas) | Después (3 tablas) |
|---|---|
| `datasets` | `datasets` (con `is_active`) |
| `distribuciones` | ❌ Eliminada |
| `ingestion_configs` | ❌ Eliminada |
| `ingestions` | `ingestions` (sin `distribucion_id`, con `notes`) |
| `archivos` | `archivos` (sin `distribucion_id`, sin versionado por periodo) |
| `recurso_datos` | ❌ Eliminada |
| `archivo_recurso` | ❌ Eliminada |

Relaciones: `Dataset` 1→N `Ingestion` 1→N `Archivo`

Enums eliminados: `SourceType`, `PeriodType`, `LocatorType`
Enums simplificados: `RunStatus` (sin `REJECTED`/`PARTIAL`)

### Migraciones

- Eliminadas las 3 migraciones anteriores (`0e8b8b1a6e04`, `79cb92f10975`, `f525df572702`)
- Nueva migración única (`a1b2c3d4e5f6`) que crea el esquema beta desde cero
- Upgrade y downgrade verificados desde base vacía

### Código

- **`models.py`:** Eliminadas clases `Distribucion`, `IngestionConfig`, `RecursoDatos`, `ArchivoRecurso`. Agregado `is_active` a `Dataset` y `notes` a `Ingestion`.
- **`repository.py`:** Eliminados métodos de distribuciones, configs y recursos. Nuevos métodos: `get_latest_successful_ingestion()`, `get_archivos_by_ingestion()`, `get_latest_archivo_by_dataset()`. Detección de duplicados por hash + dataset.
- **`ingestion_service.py`:** Eliminado parámetro `distribucion_key`. Flujo simplificado: validar dataset → calcular hash → detectar duplicados → crear ejecución → almacenar → registrar archivo → cerrar ejecución.
- **`storage/base.py` y `local.py`:** Paths simplificados a `dataset={key}/periodo={period}/version={timestamp}/original.{ext}`.
- **`cli/app.py`:** Eliminado grupo `distribuciones`. Comando `register` ya no requiere `--distribucion`. Comando `archivos latest` consulta por dataset directamente.

### Documentación

- **`docs/schema.md`:** Actualizado con las 3 tablas y nota explícita sobre el alcance beta
- **`assets/erd.svg`:** Regenerado con `sqlalchemy-erd`

## Instrucciones para verificación

### 1. Levantar base de datos limpia

```bash
# Si la BD tiene migraciones anteriores, limpiar primero:
docker compose exec postgres psql -U rawlake -d rawlake -c \
  "DROP TABLE IF EXISTS archivo_recurso, archivos, recurso_datos, ingestion_configs, ingestions, distribuciones, datasets CASCADE;"
docker compose exec postgres psql -U rawlake -d rawlake -c \
  "DROP TYPE IF EXISTS ingestionmode, runstatus, triggertype, sourcetype, periodtype, locatortype CASCADE;"

# Aplicar migración
just migrate

# Verificar: solo deben existir datasets, ingestions, archivos
docker compose exec postgres psql -U rawlake -d rawlake -c "\dt"
```

### 2. Verificar upgrade y downgrade

```bash
uv run alembic downgrade base
uv run alembic upgrade head
```

### 3. Lint y tests

```bash
just lint
just test
```

### 4. Probar CLI (opcional)

```bash
just cli datasets list
just cli ingestions list
just cli archivos latest --dataset <dataset_key>
just cli register --dataset <dataset_key> --period 2026-01 --file /ruta/archivo.csv
```

## Alcance

### ✅ Incluido en esta beta

- Registro de archivos con auditoría (quién, cuándo, cómo)
- Detección de duplicados por hash + dataset
- Consulta de última ejecución exitosa por dataset
- Soporte para carga manual (CLI) y automática (orquestador)
- Paths organizados por dataset y periodo
- metadata.json junto a cada archivo almacenado

### ⏸️ Pospuesto para iteraciones futuras

- **Distribuciones:** Múltiples formatos o accesos por dataset
- **Ingestion Configs:** Configuración dinámica de extractores y schedules en BD
- **Recurso Datos:** Catalogación de entidades lógicas (hojas de Excel, miembros de ZIP)
- **Schema Registry:** Análisis y validación de estructuras de columnas
- **Versionado por periodo:** Control de versiones y flags de "último válido"

Estas funcionalidades no se descartan; se posponen hasta tener evidencia de uso real sobre la beta.

## Criterios de aceptación

- [x] Modelo reducido a 3 entidades con FKs, relaciones ORM e índices
- [x] Sin tablas de distribuciones, configs, recursos ni archivo_recurso
- [x] Una ejecución puede registrar uno o varios archivos
- [x] Consultable la última ejecución exitosa por dataset
- [x] Flujo manual y automático soportados
- [x] Migración aplica limpia desde BD vacía (upgrade y downgrade)
- [x] Documentación y ERD coinciden con los modelos
- [x] `just lint` sin errores
- [x] `just test` pasa completo
