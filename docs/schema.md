# Esquema de Base de Datos

## Esquema

![ERD](../assets/erd.svg)

## Tablas

### datasets

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | integer | Primary key |
| nombre_corto | varchar(100) | Nombre único del dataset |
| nombre | text | Nombre completo |
| fuente | text | Fuente de los datos |
| descripcion | text | Descripción opcional |
| periodicidad | text | Frecuencia de actualización |
| desagregacion_geografica | text | Nivel geográfico |
| inicio_cobertura_temporal | text | Inicio de datos históricos |
| created_at | datetime | Fecha de creación |
| updated_at | datetime | Última modificación |

### distribuciones

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | integer | Primary key |
| dataset_id | integer | FK → datasets.id |
| nombre | text | Nombre de la distribución |
| descripcion | text | Descripción opcional |
| tipo_de_acceso | enum | MANUAL_UPLOAD, HTTP_FILE, API_JSON |
| manual_upload_allowed | boolean | Permite carga manual |
| url | text | URL del recurso |
| created_at | datetime | Fecha de creación |
| updated_at | datetime | Última modificación |

### ingestion_configs

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | integer | Primary key |
| distribucion_id | integer | FK → distribuciones.id |
| extractor_class | varchar(100) | Clase del extractor |
| period_type | enum | DAILY, WEEKLY, MONTHLY, etc. |
| ingestion_mode | enum | MANUAL, AUTOMATED, HYBRID |
| expected_file_types | array | Tipos de archivo esperados |
| schedule | varchar(100) | Expresión cron |
| is_active | boolean | Si está activa |
| created_at | datetime | Fecha de creación |
| updated_at | datetime | Última modificación |

### ingestions

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | integer | Primary key |
| run_id | varchar(100) | ID único de ejecución |
| dataset_id | integer | FK → datasets.id |
| distribucion_id | integer | FK → distribuciones.id |
| period_label | varchar(50) | Etiqueta del periodo |
| status | enum | RUNNING, SUCCESS, FAILED, etc. |
| trigger_type | enum | SCHEDULED, MANUAL_CLI, etc. |
| ingestion_mode | enum | MANUAL, AUTOMATED, HYBRID |
| created_by | varchar(100) | Usuario que inició |
| nombre_archivo | text | Nombre del archivo |
| dropzone_path | text | Ruta del dropzone |
| manifest_path | text | Ruta del manifiesto |
| started_at | datetime | Inicio de ejecución |
| finished_at | datetime | Fin de ejecución |
| error_message | text | Mensaje de error |
| orchestrator_name | varchar(100) | Nombre del orquestador |
| orchestrator_flow_id | varchar(100) | ID del flow/DAG |
| orchestrator_run_id | varchar(100) | ID de la ejecución |
| created_at | datetime | Fecha de creación |

### archivos

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | integer | Primary key |
| ingestion_id | integer | FK → ingestions.id |
| distribucion_id | integer | FK → distribuciones.id |
| nombre_archivo | text | Nombre del archivo |
| file_size_bytes | bigint | Tamaño en bytes |
| hash_sha256 | varchar(64) | Hash SHA256 |
| period_label | varchar(50) | Etiqueta del periodo |
| version_number | integer | Número de versión |
| version_timestamp | datetime | Timestamp de versión |
| is_latest_for_period | boolean | Última versión del periodo |
| storage_backend | varchar(50) | Backend de almacenamiento |
| storage_path | text | Ruta en el storage |
| file_extension | varchar(20) | Extensión del archivo |
| mime_type | varchar(100) | Tipo MIME |
| source_url | text | URL de origen |
| uploaded_by | varchar(100) | Usuario que subió |
| ingestion_mode | enum | MANUAL, AUTOMATED, HYBRID |
| fecha_ingesta | datetime | Fecha de ingesta |
| created_at | datetime | Fecha de creación |

## Relaciones

- `datasets` → `distribuciones` (1:N)
- `datasets` → `ingestions` (1:N)
- `distribuciones` → `ingestion_configs` (1:1)
- `distribuciones` → `ingestions` (1:N)
- `distribuciones` → `archivos` (1:N)
- `ingestions` → `archivos` (1:N)

> **Nota:** La relación `distribuciones` → `ingestion_configs` es técnicamente 1:1 (implementada con `uselist=False` en SQLAlchemy). ERDAlchemy no detecta esta cardinalidad y la muestra como 1:N en el diagrama, pero el modelo garantiza que cada distribución tenga como máximo una configuración de ingestión.
