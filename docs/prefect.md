# Prefect local con Docker Compose

## Configuración

Antes de iniciar los servicios, cree el archivo de configuración local y ajuste
las credenciales, puertos o ruta de almacenamiento si el entorno lo requiere:

```bash
cp .env.example .env
```

## Arquitectura

`docker compose up -d --build` inicia `postgres`, `prefect-server`,
`prefect-worker` y `prefect-deploy`. El servidor publica la API y la interfaz en
[http://localhost:4200](http://localhost:4200); el worker atiende el work pool
de tipo `process` llamado `rawlake-worker` y ejecuta `run_ingestion`.

Ambos sistemas comparten la instancia de PostgreSQL pero **no** la base de
datos: RawLake usa `DB_NAME` y Prefect usa `PREFECT_DB_NAME`. La separación es
obligatoria porque los dos ejecutan migraciones de Alembic sobre la tabla
`alembic_version`, y compartirla deja al servidor de Prefect sin poder crear sus
tablas. `scripts/init-prefect-db.sh` crea esa base al inicializar el volumen.

El worker usa el hostname interno `postgres`, mientras que la CLI de RawLake en
el anfitrión conserva `localhost` como predeterminado. La imagen contiene el
paquete RawLake y los manifiestos; los despliegues usan `/app` como ruta y los
contenedores leen los manifiestos desde `RAWLAKE_CONFIGS_DIR`.

`prefect-deploy` es un servicio de un solo uso: espera a que el servidor esté
saludable, genera `prefect.yaml` a partir de los manifiestos, publica los
despliegues y termina. Es idempotente, así que vuelve a correr en cada
`docker compose up` sin efectos adicionales. Va como servicio aparte y no dentro
del arranque del worker para que un fallo al publicar no impida que el worker
atienda corridas.

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

No hay pasos manuales: `docker compose up -d --build` publica los despliegues a
través del servicio `prefect-deploy`. Para revisar el resultado:

```bash
docker compose logs prefect-deploy
```

Para volver a publicar sin reiniciar el resto de los servicios, por ejemplo tras
editar un manifiesto:

```bash
docker compose up -d --build prefect-deploy
```

El primer arranque del worker crea `rawlake-worker` si no existe. Los manifiestos
con `schedule.enabled: true` crean corridas según su cron y zona horaria. Los
manifiestos con `schedule.enabled: false` no generan despliegue, así que esos
productos no aparecen en la interfaz ni siquiera para corridas manuales; use
`just cli ingest run --dataset <dataset_key>` para ejecutarlos.

Para una corrida manual, abra la UI, seleccione `ingest-<dataset_key>` y cree
una corrida personalizada. Use `dry_run: true` para una prueba segura.

## Diagnóstico

- Si la UI no carga, compruebe el puerto 4200 y `docker compose logs prefect-server`.
- Si una corrida queda pendiente, confirme que `rawlake-worker` está listo y
  revise `docker compose logs prefect-worker`.
- Si falla la escritura, compruebe `RAWLAKE_LOCAL_ROOT` y los permisos de Docker.
- Si el servidor no llega a estado saludable con un error de Alembic sobre
  tablas inexistentes, la base de Prefect no existe o se está compartiendo con
  la de RawLake. En un entorno local desechable, `docker compose down -v`
  recrea el volumen y ejecuta `scripts/init-prefect-db.sh`.
- Si un despliegue no aparece en la interfaz, revise
  `docker compose logs prefect-deploy`.
- Tras cambiar código, dependencias o manifiestos, ejecute
  `docker compose up -d --build` para reconstruir la imagen y volver a publicar.
