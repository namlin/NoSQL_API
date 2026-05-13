# Movie Graph API

API RESTful para un catálogo de películas respaldado por una base de datos de grafos.
Desarrollada con **FastAPI + Python** para CI-0141 Bases de Datos Avanzadas — UCR.

## Requisitos

- Python 3.11+
- pip

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd NoSQL_API

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar el archivo de configuración
cp .env.example .env
```

## Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`.
Swagger UI: `http://localhost:8000/docs`

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/api/movies` | Crear una película |
| GET | `/api/movies` | Listar todas (paginado: `?page=1&limit=10`) |
| GET | `/api/movies/search` | Buscar con filtros |
| GET | `/api/movies/{id}` | Obtener una por ID |
| PUT | `/api/movies/{id}` | Actualizar una película |
| DELETE | `/api/movies/{id}` | Eliminar una película |
| GET | `/api/movies/{id}/similar` | Películas similares (traversal de grafo) |

### Parámetros de búsqueda (`/api/movies/search`)

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `title` | string | Búsqueda parcial por título |
| `genre` | string | Filtro por género (ej: `Action`, `Drama`) |
| `year_min` | int | Año mínimo de estreno |
| `year_max` | int | Año máximo de estreno |
| `rating_min` | float | Rating mínimo IMDb (0.0 – 10.0) |
| `actor_name` | string | Nombre de actor (solo con BD de grafos real) |

## Configuración de la base de datos

El backend se controla con la variable `DB_BACKEND` en el archivo `.env`:

| Valor | Descripción |
|-------|-------------|
| `mock` | Almacenamiento en memoria (default, sin BD real) |
| `neptune` | Amazon Neptune (Gremlin) — implementar en `app/repositories/neptune.py` |

Para conectar la BD real:
1. Instalar el driver: `pip install gremlinpython` (Neptune) o `pip install neo4j`
2. Implementar los métodos en `app/repositories/neptune.py`
3. Actualizar `.env`:
   ```
   DB_BACKEND=neptune
   DB_URL=wss://<neptune-endpoint>:8182/gremlin
   ```

## Carga de datos (seed)

```bash
# 1. Crear carpetas de datos
mkdir -p data/imdb data/movielens

# 2. Descargar MovieLens ml-latest-small
#    https://grouplens.org/datasets/movielens/latest/
#    Extraer links.csv y ratings.csv en data/movielens/

# 3. Descargar archivos IMDb
#    https://datasets.imdbws.com/
#    Descargar y colocar en data/imdb/:
#      title.basics.tsv.gz, title.ratings.tsv.gz,
#      title.principals.tsv.gz, name.basics.tsv.gz

# 4. Ejecutar el script de carga
python scripts/seed_db.py
```

## Estructura del proyecto

```
NoSQL_API/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Variables de entorno
│   ├── dependencies.py      # Inyección de dependencias
│   ├── models/movie.py      # Esquemas Pydantic
│   ├── repositories/
│   │   ├── base.py          # Interfaz abstracta
│   │   ├── mock.py          # Implementación en memoria
│   │   └── neptune.py       # Implementación Neptune (pendiente)
│   └── routers/movies.py    # Endpoints
├── scripts/seed_db.py       # Carga de datos IMDb + MovieLens
├── requirements.txt
├── .env.example
└── PLAN.md                  # Diseño de BD y arquitectura del proyecto
```
