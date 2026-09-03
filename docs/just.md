# Comandos de just

`just` es el ejecutor de tareas del proyecto. Reúne en un solo lugar los comandos
de entorno, calidad, base de datos, Compose y CLI, para que nadie tenga que
recordar la invocación exacta de `uv`, `alembic` o `docker compose`.

## Instalación en Linux

El proyecto requiere **`just` 1.27 o superior**, porque agrupa las recetas con el
atributo `[group('...')]`, disponible a partir de esa versión.

La forma recomendada es el instalador oficial, que descarga el binario
precompilado y no depende del gestor de paquetes de la distribución:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh \
  | bash -s -- --to ~/.local/bin
```

Asegúrese de que `~/.local/bin` esté en su `PATH` y confirme la versión:

```bash
just --version
```

Alternativas, siempre que ofrezcan 1.27 o superior:

| Método | Comando |
|---|---|
| Cargo | `cargo install just` |
| Arch | `pacman -S just` |
| Debian / Ubuntu | `apt install just` |
| Fedora | `dnf install just` |

Los repositorios de Debian y Ubuntu suelen ir por detrás de la versión actual.
Verifique con `just --version` antes de asumir que sirve.

## Uso

Ejecutar `just` sin argumentos lista todas las recetas disponibles con su
descripción, agrupadas por área:

```bash
just
```

La lista se genera a partir del propio `justfile`, así que siempre refleja el
estado real del repositorio. Esta tabla es una referencia de lectura; ante
cualquier discrepancia, la salida de `just` manda.

## Entorno

| Comando | Descripción |
|---|---|
| `just setup` | Instala dependencias y registra los git hooks. |
| `just install` | Sincroniza dependencias sin tocar los hooks. |

## Calidad

| Comando | Descripción |
|---|---|
| `just lint` | Reporta errores de lint en código y tests. |
| `just format` | Reescribe código y tests con el formateador del proyecto. |
| `just test` | Ejecuta la suite de pruebas. |
| `just hooks` | Ejecuta todos los hooks de pre-commit sobre el repositorio completo. |

## Base de datos

| Comando | Descripción |
|---|---|
| `just migrate` | Aplica las migraciones pendientes de Alembic. |
| `just revision <mensaje>` | Autogenera una migración a partir de los modelos actuales. |
| `just psql` | Abre una sesión de psql contra la base de RawLake. |

## Compose

| Comando | Descripción |
|---|---|
| `just up` | Construye las imágenes y levanta toda la pila en segundo plano. |
| `just down` | Detiene la pila conservando el volumen de la base de datos. |
| `just ps` | Muestra el estado de cada servicio, incluidos los que terminaron. |
| `just logs [servicio]` | Sigue los logs de un servicio, o de todos si no se indica ninguno. |
| `just deploy` | Reconstruye la imagen y vuelve a publicar los deployments de Prefect. |
| `just ingest <dataset> [dry_run]` | Dispara una corrida de ingesta a través del deployment de Prefect. |

`just ingest` usa `dry_run=true` de forma predeterminada, para que una prueba
accidental no escriba en disco ni en la base:

```bash
just ingest inegi_imaief          # corrida seca
just ingest inegi_imaief false    # corrida real
```

## CLI

| Comando | Descripción |
|---|---|
| `just cli <args>` | Ejecuta la CLI de RawLake en el anfitrión. |
