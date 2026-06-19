<div align="center">

# 📋 Convención de Commits - RawLake

<img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" alt="Git"/>
<img src="https://img.shields.io/badge/Conventional_Commits-FE5196?style=for-the-badge&logo=conventionalcommits&logoColor=white" alt="Conventional Commits"/>
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>

---

### Mensajes claros, historial rastreable, equipo en sincronía 🎯

</div>

---

## 🚀 Formato

RawLake sigue [Conventional Commits](https://www.conventionalcommits.org/).
Cada mensaje de commit debe tener esta estructura:

```
<tipo>(<scope>): <descripción en imperativo>
```

- **tipo**: Obligatorio. Uno de los tipos de la tabla.
- **scope**: Opcional pero preferido. Uno de los scopes de la tabla. Omítelo solo cuando el cambio realmente abarca muchos módulos.
- **descripción**: Obligatoria. En imperativo, en minúsculas, sin punto final. En inglés.

```bash
# Ejemplos
git commit -m "feat(storage): add MinIO backend for raw assets"
git commit -m "fix(metadata): handle missing checksum on ingestion"
git commit -m "refactor(config): add pydantic BaseConfig for env vars"
git commit -m "docs(guide): add commit convention to docs/"
```

---

## 📝 Tipos

<div align="center">

| Tipo | Úsalo cuando... | Ejemplo |
|:----:|:------------|:--------|
| `feat` | Agregas comportamiento o capacidad nueva para el usuario | `feat(storage): add MinIO backend for raw assets` |
| `fix` | Corriges un bug | `fix(metadata): handle missing checksum on ingestion` |
| `refactor` | Cambias código **sin** cambiar su comportamiento | `refactor(services): extract versioning into helper` |
| `perf` | Mejoras rendimiento sin cambiar comportamiento | `perf(storage): stream large assets instead of buffering` |
| `docs` | Cambias solo documentación (README, docstrings, este archivo) | `docs: add contributing guide` |
| `test` | Agregas o corriges tests, sin cambio en código de producción | `test(services): cover checksum mismatch path` |
| `build` | Cambias el empaquetado o el sistema de build | `build: configure uv build backend` |
| `deps` | Agregas, quitas o actualizas dependencias (`pyproject.toml`, `uv.lock`) | `deps: bump prefect to 3.1.0` |
| `ci` | Cambias pipelines de CI o hooks de pre-commit | `ci: add ruff check to pipeline` |
| `style` | Cambias solo formato (ruff format, espacios): sin lógica | `style: apply ruff format` |
| `chore` | Mantenimiento del repo que no encaja en otro tipo (`.gitignore`, tooling) | `chore: update .gitignore` |

</div>

> **Breaking change** → agrega `!` después del scope (`feat(storage)!: ...`) **y** un footer `BREAKING CHANGE:` explicando la migración.

---

## 🗂️ Scopes

Los scopes mapean 1:1 con el layout de paquetes bajo `src/rawlake/` más las preocupaciones de infraestructura.

<div align="center">

| Scope | Aplica a |
|:-----:|:---------|
| `cli` | `cli/`: comandos CLI y entry points |
| `config` | `config.py`: variables de entorno, `BaseConfig` |
| `metadata` | `metadata/`: `db.py`, `models.py`, `repository.py` |
| `services` | `services/`: ingestión, checksum, versionado |
| `storage` | `storage/`: `base.py`, `local.py`, futuro MinIO |
| `extractors` | `extractors/`: extracción de datos |
| `schemas` | `schemas/`: modelos Pydantic |
| `utils` | `utils/`: logger y helpers compartidos |
| `flows` | `flows/`: definiciones de flows de Prefect |
| `migrations` | Migraciones Alembic bajo `migrations/versions/` |
| `infra` | `docker-compose.yml`, PostgreSQL, contenedores |

</div>

---

## 📚 Ejemplos por área

<details>
<summary><strong>📥 Ingestión y storage</strong></summary>

```bash
feat(storage): add MinIO backend for raw assets
fix(storage): handle path collision on duplicate asset
refactor(services): extract ingestion pipeline into stages
perf(storage): stream large assets instead of buffering
```

</details>

<details>
<summary><strong>🗃️ Metadata y migraciones</strong></summary>

```bash
feat(metadata): add asset_version table and repository
fix(metadata): handle missing checksum on ingestion
feat(migrations): add raw_asset registry table
fix(migrations): correct nullable constraint on checksum column
```

</details>

<details>
<summary><strong>⚙️ Config y CLI</strong></summary>

```bash
refactor(config): add pydantic BaseConfig for env vars
feat(cli): add register-raw-asset command
fix(cli): validate source path before ingestion
```

</details>

<details>
<summary><strong>🔁 Flows y utilidades</strong></summary>

```bash
feat(flows): add Prefect flow for batch asset registration
refactor(utils): add Logger class and remove prompt template
test(services): cover checksum mismatch path
```

</details>

---

## ✅ Reglas

<table>
<tr>
<td width="50%">

**1. Tipo y scope en minúsculas**
`feat(storage)` ✅ - `Feat(Storage)` ❌

**2. Descripción en inglés, imperativo**
`"add MinIO backend"` ✅
`"added MinIO backend"` ❌
`"agrega backend de MinIO"` ❌

**3. Máximo ~72 caracteres en la primera línea**
El detalle va en el cuerpo del commit.

</td>
<td width="50%">

**4. No inventes scopes de un solo uso**
Usa un scope de la tabla o ninguno. Un scope solo sirve si se repite.

**5. Un commit = un cambio lógico**
No mezcles un feature, un pase de formato y un bump de dependencias.

**6. Sin commits `WIP` en el PR final**

</td>
</tr>
</table>

---

<div align="center">

<sub>Convención de commits - RawLake - IIEG Jalisco</sub>

</div>
