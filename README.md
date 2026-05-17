# Movie Graph API

API RESTful para un catálogo de películas respaldado por una base de datos de grafos.
Desarrollada con **FastAPI + Python** para CI-0141 Bases de Datos Avanzadas — UCR.

## Requisitos

- Python 3.11+
- pip

## Instalación de base de datos

Antes de configurar la API, inicia el contenedor de Neo4j de forma aislada:

```bash
cd neo4j
docker compose up -d
cd ..
```

*Esto levantará el motor de grafos en segundo plano:*

* **Interfaz Web (Neo4j Browser):** http://localhost:7474 (para ver visualmente los nodos y aristas).
* **Puerto de Comunicación (Bolt):** `7687` (usado internamente por la API).


## Instalación de front?(AYUDA CON EL NOMBRE)

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd NoSQL_API
```

* ### Windows

   ```bash
   # 2. Crear y activar entorno virtual
   python -m venv venv
   venv\Scripts\activate

   # 3. Instalar dependencias
   pip install -r requirements.txt

   # 4. Copiar el archivo de configuración
   cp .env.example .env
   ```


* ### Linux (Debian & Ubuntu) / macOS 

   ```bash
   # 2. Crear y activar entorno virtual
   python3 -m venv venv
   source venv/bin/activate

   # 3. Instalar dependencias
   pip install -r requirements.txt

   # 4. Copiar el archivo de configuración
   cp .env.example .env
   ```

## Configuración de la base de datos

Abre tu archivo `.env` recién creado y asegúrate de que tenga las siguientes variables asignadas para activar Neo4j:

```env
DB_BACKEND=neo4j
NEO4J_URI=bolt://localhost:7687
```

*(Si deseas probar con datos temporales simulados sin usar Docker, puedes cambiar temporalmente a `DB_BACKEND=mock`).*

## Ejecutar el servidor

   ```bash
   uvicorn app.main:app --reload
   ```

- La API queda disponible en `http://localhost:8000`.
- Swagger UI: `http://localhost:8000/docs`

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

* ### Parámetros de búsqueda (`/api/movies/search`)

   | Parámetro | Tipo | Descripción |
   |-----------|------|-------------|
   | `title` | string | Búsqueda parcial por título |
   | `genre` | string | Filtro por género (ej: `Action`, `Drama`) |
   | `year_min` | int | Año mínimo de estreno |
   | `year_max` | int | Año máximo de estreno |
   | `rating_min` | float | Rating mínimo IMDb (0.0 – 10.0) |
   | `actor_name` | string | Nombre de actor (solo con BD de grafos real) |


## Carga de datos (seed)

(PROCESO...)

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
│   │   └── neo4j.py         # Implementación de Neo4j con Cypher
│   └── routers/movies.py    # Endpoints
├── scripts/seed_db.py       # Carga de datos IMDb + MovieLens
├── requirements.txt
├── .env.example
└── PLAN.md                  # Diseño de BD y arquitectura del proyecto
```