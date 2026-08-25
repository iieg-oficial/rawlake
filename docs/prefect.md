# Prefect local con Docker Compose

## Configuración

Antes de iniciar los servicios, cree el archivo de configuración local y ajuste
las credenciales, puertos o ruta de almacenamiento si el entorno lo requiere:

```bash
cp .env.example .env
```

## Arquitectura

`docker compose up -d --build` inicia `postgres`, `prefect-server` y
`prefect-worker`. El servidor publica la API y la interfaz en
[http://localhost:4200](http://localhost:4200); el worker atiende el work pool
de tipo `process` llamado `rawlake-worker` y ejecuta `run_ingestion`.

PostgreSQL conserva los metadatos de RawLake y las tablas internas de Prefect.
El worker usa el hostname interno `postgres`, mientras que la CLI de RawLake en
el anfitrión conserva `localhost` como predeterminado. La imagen contiene el
paquete RawLake y los manifiestos; los despliegues usan `/app` como ruta.

## Inicio y detención

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f prefect-server prefect-worker
docker compose down
```

`RAWLAKE_LOCAL_ROOT` se monta en el worker como `/mnt/datalake`. Su valor
predeterminado es `/mnt/datalake`; cámbielo antes de arrancar Compose si los
archivos crudos deben vivir en otra ruta del anfitrión. Docker debe poder
escribir en esa ruta.

## Publicar y ejecutar despliegues

Cuando el servidor y worker estén saludables, publique los despliegues:

```bash
set -a
source .env
set +a
export PREFECT_API_URL="$PREFECT_SERVER_UI_API_URL"
just cli flows deploy
prefect deploy --all
```

El primer arranque del worker crea `rawlake-worker` si no existe. Los manifiestos
con `schedule.enabled: true` crean corridas según su cron y zona horaria.

Para una corrida manual, abra la UI, seleccione `ingest-<dataset_key>` y cree
una corrida personalizada. Use `dry_run: true` para una prueba segura.

## Diagnóstico

- Si la UI no carga, compruebe el puerto 4200 y `docker compose logs prefect-server`.
- Si una corrida queda pendiente, confirme que `rawlake-worker` está listo y
  revise `docker compose logs prefect-worker`.
- Si falla la escritura, compruebe `RAWLAKE_LOCAL_ROOT` y los permisos de Docker.
- Tras cambiar código, dependencias o manifiestos, ejecute
  `docker compose up -d --build` antes de volver a publicar despliegues.
