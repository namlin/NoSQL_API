# Plan: FastAPI CRUD API — Base de datos de grafos de películas

## Context

Proyecto para CI-0141 Bases de Datos Avanzadas (UCR). El grupo usa una base de datos de **grafos** (probablemente Amazon Neptune, pero podría cambiar a Neo4j o ArangoDB). La temática es un **catálogo de películas** poblado con datos reales de IMDb + MovieLens. El objetivo es construir la API primero con un repositorio ficticio (en memoria), para que al conectar la BD real solo se cambie la capa de acceso a datos, sin tocar los endpoints.

---

## Parte 1 — Estructura de la Base de Datos (para los compañeros a cargo de la BD)

### Origen de los datos

| Dataset | URL | Qué aporta |
|---------|-----|------------|
| IMDb title.basics.tsv | https://datasets.imdbws.com/ | Títulos, año, género, duración |
| IMDb title.ratings.tsv | https://datasets.imdbws.com/ | Rating promedio y número de votos |
| IMDb title.principals.tsv | https://datasets.imdbws.com/ | Relación película ↔ persona (actor, director, escritor) |
| IMDb name.basics.tsv | https://datasets.imdbws.com/ | Info de actores y directores |
| MovieLens ml-latest-small | https://grouplens.org/datasets/movielens/latest/ | 9,742 películas + 100,836 ratings de usuarios reales |
| MovieLens links.csv | incluido en el zip anterior | Vincula movieId de MovieLens con tconst de IMDb |

---

### Nodos (Vértices)

#### `Movie`
Fuente: `title.basics.tsv` + `title.ratings.tsv`, filtrado por MovieLens `links.csv`

| Propiedad | Tipo | Fuente | Notas |
|-----------|------|--------|-------|
| `id` | string | title.basics → `tconst` | Ej: `"tt0111161"` |
| `title` | string | title.basics → `primaryTitle` | |
| `originalTitle` | string | title.basics → `originalTitle` | |
| `year` | int | title.basics → `startYear` | Ignorar `\N` |
| `runtimeMinutes` | int | title.basics → `runtimeMinutes` | Ignorar `\N` |
| `averageRating` | float | title.ratings → `averageRating` | `null` si no tiene votos |
| `numVotes` | int | title.ratings → `numVotes` | `null` si no tiene votos |
| `movielensId` | int | links.csv → `movieId` | Para cruzar con ratings de usuarios |

#### `Person`
Fuente: `name.basics.tsv`, solo las personas que aparecen en `title.principals.tsv` para las películas incluidas

| Propiedad | Tipo | Fuente | Notas |
|-----------|------|--------|-------|
| `id` | string | name.basics → `nconst` | Ej: `"nm0000062"` |
| `name` | string | name.basics → `primaryName` | |
| `birthYear` | int | name.basics → `birthYear` | Ignorar `\N` |
| `deathYear` | int | name.basics → `deathYear` | Ignorar `\N` |
| `primaryProfession` | string | name.basics → `primaryProfession` | Primera profesión del pipe-separated |

#### `Genre`
Fuente: `title.basics → genres` (campo pipe-separated, ej: `"Action|Drama|Thriller"`)

| Propiedad | Tipo | Notas |
|-----------|------|-------|
| `name` | string | Ej: `"Action"`, `"Drama"`, `"Comedy"` — crear un nodo por género único |

#### `User` *(opcional, añade valor gráfico)*
Fuente: `MovieLens ratings.csv`

| Propiedad | Tipo | Fuente |
|-----------|------|--------|
| `id` | string | ratings → `userId` (convertir a `"u1"`, `"u2"`, etc.) |

---

### Aristas (Relaciones)

Estas son **las que demuestran las fortalezas de una BD de grafos**. Son la parte más importante del diseño.

#### `(Person)-[:ACTED_IN {characters, ordering}]->(Movie)`
Fuente: `title.principals.tsv` donde `category = "actor"` o `"actress"`

| Propiedad | Tipo | Fuente |
|-----------|------|--------|
| `characters` | string | title.principals → `characters` (puede ser `\N`) |
| `ordering` | int | title.principals → `ordering` (importancia del crédito) |

#### `(Person)-[:DIRECTED]->(Movie)`
Fuente: `title.principals.tsv` donde `category = "director"`

*(Sin propiedades extra)*

#### `(Person)-[:WROTE]->(Movie)`
Fuente: `title.principals.tsv` donde `category = "writer"`

*(Sin propiedades extra)*

#### `(Movie)-[:HAS_GENRE]->(Genre)`
Fuente: derivado de `title.basics → genres`, separar por `|` y crear una arista por género

*(Sin propiedades extra)*

#### `(User)-[:RATED {rating, timestamp}]->(Movie)` *(opcional pero recomendado)*
Fuente: `MovieLens ratings.csv`, cruzando `movieId` con `links.csv → tconst`

| Propiedad | Tipo | Fuente |
|-----------|------|--------|
| `rating` | float | ratings → `rating` (escala 0.5–5.0) |
| `timestamp` | int | ratings → `timestamp` (Unix epoch) |

---

### Escala recomendada para la demo

Para que la BD sea manejable durante el demo y no tarde horas en poblar:

1. Partir de MovieLens ml-latest-small (`links.csv`) → esto da exactamente **9,742 películas** como subconjunto.
2. Usar los `imdbId` de ese archivo para filtrar `title.basics`, `title.ratings`, `title.principals` y `name.basics` de IMDb.
3. Resultado esperado:
   - ~9,742 nodos `Movie`
   - ~10,000–30,000 nodos `Person` (actores + directores de esas películas)
   - ~19 nodos `Genre`
   - ~610 nodos `User` (si se incluyen ratings)
   - ~50,000–100,000 aristas en total

---

### Script de carga (`scripts/seed_db.py`)

El repositorio requiere un script de inicialización. Debe:

1. Leer `links.csv` de MovieLens → obtener lista de `imdbId` válidos
2. Filtrar `title.basics.tsv` por esos IDs → crear nodos `Movie`
3. Cruzar con `title.ratings.tsv` → agregar `averageRating` y `numVotes` a cada `Movie`
4. Filtrar `title.principals.tsv` por los mismos IDs → obtener relaciones
5. Filtrar `name.basics.tsv` por las personas de esas relaciones → crear nodos `Person`
6. Parsear el campo `genres` (pipe-separated) → crear nodos `Genre` únicos + aristas `HAS_GENRE`
7. Crear aristas `ACTED_IN`, `DIRECTED`, `WROTE` a partir de `title.principals`
8. *(Opcional)* Leer `ratings.csv` → crear nodos `User` + aristas `RATED`
9. Imprimir resumen: cuántos nodos y aristas se crearon

**Orden de inserción importante:** Primero todos los nodos, luego las aristas. Si la BD no permite insertar aristas a nodos inexistentes, respetar este orden.

---

### Consulta avanzada de grafo para la demo (requisito del enunciado)

El enunciado pide demostrar "una característica particular del motor". Para grafos, implementar:

**"Películas similares a X"** — dado el `id` de una película, encontrar otras películas que comparten actores o géneros, ordenadas por número de conexiones compartidas. Traversal de 2 saltos:

```
Movie → [HAS_GENRE] → Genre → [HAS_GENRE] → OtherMovie
Movie ← [ACTED_IN] ← Person → [ACTED_IN] → OtherMovie
```

Esto va en el endpoint `GET /api/movies/{id}/similar`.

---

## Parte 2 — Estructura del Proyecto API

```
NoSQL_API/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, registra routers, configura Swagger
│   ├── config.py            # Settings (DB_URL, DB_USER, etc. desde .env)
│   ├── dependencies.py      # Dependency injection: get_repository()
│   ├── models/
│   │   ├── __init__.py
│   │   └── movie.py         # MovieCreate, MovieUpdate, MovieResponse (Pydantic)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py          # AbstractMovieRepository (interfaz abstracta)
│   │   ├── mock.py          # InMemoryMovieRepository (dict, para desarrollo)
│   │   └── neptune.py       # NeptuneMovieRepository (vacío, a completar luego)
│   └── routers/
│       ├── __init__.py
│       └── movies.py        # Los 7 endpoints requeridos
├── scripts/
│   └── seed_db.py           # Script de carga de datos
├── requirements.txt
├── .env.example
└── README.md
```

---

## Endpoints a implementar

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/movies` | Crear una película (nodo) |
| GET | `/api/movies` | Obtener todas (con `page` y `limit`) |
| GET | `/api/movies/{id}` | Obtener una por ID |
| PUT | `/api/movies/{id}` | Actualizar una película |
| DELETE | `/api/movies/{id}` | Eliminar una película |
| GET | `/api/movies/search` | Filtrar por `title`, `genre`, `year_min/max`, `rating_min`, `actor_name` |
| GET | `/api/movies/{id}/similar` | Películas similares via traversal de grafo *(consulta avanzada)* |

Todos retornan JSON con códigos HTTP apropiados (200, 201, 404, 422).

---

## Modelos Pydantic

```python
# app/models/movie.py
class MovieBase(BaseModel):
    title: str
    originalTitle: str | None = None
    year: int | None = None
    runtimeMinutes: int | None = None
    averageRating: float | None = None
    numVotes: int | None = None

class MovieCreate(MovieBase): pass

class MovieUpdate(BaseModel):   # todos opcionales para PATCH
    title: str | None = None
    year: int | None = None
    runtimeMinutes: int | None = None
    averageRating: float | None = None

class MovieResponse(MovieBase):
    id: str                     # tconst de IMDb, ej: "tt0111161"
    genres: list[str] = []      # nombres de géneros relacionados
```

---

## Patrón Repository (clave para desacoplar la BD)

```
Router → llama método del repositorio
Repositorio (abstracto) → InMemoryRepo (ahora) → NeptuneRepo (luego)
```

`dependencies.py` decide qué implementación inyectar según `DB_BACKEND=mock|neptune` en el `.env`.

Cuando conecten Neptune / Neo4j / ArangoDB:
1. Instalar el driver (`gremlinpython` para Neptune, `neo4j` para Neo4j, `python-arango` para ArangoDB)
2. Rellenar `repositories/neptune.py` implementando `AbstractMovieRepository`
3. Cambiar `.env`: `DB_BACKEND=neptune` + `DB_URL=wss://...`
4. Los routers y modelos **no cambian**

---

## Stack técnico

```
fastapi
uvicorn[standard]
pydantic>=2.0
python-dotenv
# Más adelante (según BD elegida):
# gremlinpython     ← Amazon Neptune (Gremlin/TinkerPop)
# neo4j             ← Neo4j (Cypher)
# python-arango     ← ArangoDB (AQL)
```

Swagger UI generado automáticamente por FastAPI en `http://localhost:8000/docs`.

---

## Orden de implementación (API)

1. `requirements.txt` + `.env.example`
2. `app/models/movie.py` — Pydantic models
3. `app/repositories/base.py` — interfaz abstracta con métodos: `create`, `get_all`, `get_by_id`, `update`, `delete`, `search`, `find_similar`
4. `app/repositories/mock.py` — implementación en memoria (dict + UUID)
5. `app/dependencies.py` — inyección del repositorio
6. `app/routers/movies.py` — los 7 endpoints
7. `app/main.py` — montar router, configurar título/versión para Swagger
8. `app/config.py` — leer `.env`
9. `README.md` — instrucciones `uvicorn app.main:app --reload`
