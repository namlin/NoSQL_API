import asyncio
import uuid
from neo4j import GraphDatabase
import app.config as config
from app.repositories.base import AbstractMovieRepository

class Neo4jMovieRepository(AbstractMovieRepository):
    def __init__(self):
        self.driver = GraphDatabase.driver(config.NEO4J_URI, auth=None)

    def _normalize_movie(self, node: dict, genres: list[str] | None = None) -> dict:
        # Normalize DB node properties to API model fields
        m = dict(node)
        # map 'runtime' (seed data) to 'runtimeMinutes' expected by Pydantic model
        if "runtime" in m and "runtimeMinutes" not in m:
            m["runtimeMinutes"] = m.get("runtime")
        # prefer genres passed from relationship query over node property
        if genres is not None:
            m["genres"] = genres
        elif "genres" not in m or m.get("genres") is None:
            m["genres"] = []
        # Coerce numeric-like fields to proper types or None
        def _to_int(val):
            if val is None:
                return None
            if isinstance(val, int):
                return val
            try:
                s = str(val).strip()
                if s == "\\N" or s == "":
                    return None
                return int(float(s))
            except Exception:
                return None

        def _to_float(val):
            if val is None:
                return None
            if isinstance(val, float):
                return val
            try:
                s = str(val).strip()
                if s == "\\N" or s == "":
                    return None
                return float(s)
            except Exception:
                return None

        m["runtimeMinutes"] = _to_int(m.get("runtimeMinutes"))
        m["year"] = _to_int(m.get("year"))
        m["numVotes"] = _to_int(m.get("numVotes"))
        m["averageRating"] = _to_float(m.get("averageRating"))
        return m

    def close(self):
        """Cierra el pool de conexiones del driver de forma segura."""
        self.driver.close()

    async def create(self, movie_data) -> dict:
        query = """
        CREATE (m:movies {
            id: $id,
            title: $title,
            originalTitle: $originalTitle,
            year: toInteger($year),
            runtime: toInteger($runtimeMinutes),
            averageRating: toFloat($averageRating),
            numVotes: toInteger($numVotes)
        })
        WITH m
        UNWIND CASE WHEN $genres = [] THEN [null] ELSE $genres END AS gen
        FOREACH (_ IN CASE WHEN gen IS NOT NULL THEN [1] ELSE [] END |
            MERGE (g:genres {genre: gen})
            MERGE (m)-[:BELONGS_TO]->(g)
        )
        WITH DISTINCT m
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:genres)
        RETURN m, collect(g.genre) AS genres
        """
        def _create():
            with self.driver.session() as session:
                if hasattr(movie_data, 'model_dump'):
                    movie_dict = movie_data.model_dump()
                else:
                    movie_dict = movie_data
                movie_id = movie_dict.get("id") if isinstance(movie_dict, dict) else None
                if not movie_id:
                    movie_id = str(uuid.uuid4())
                    movie_dict["id"] = movie_id
                params = {
                    "id": movie_dict.get("id"),
                    "title": movie_dict.get("title"),
                    "originalTitle": movie_dict.get("originalTitle"),
                    "year": movie_dict.get("year"),
                    "runtimeMinutes": movie_dict.get("runtimeMinutes"),
                    "averageRating": movie_dict.get("averageRating"),
                    "numVotes": movie_dict.get("numVotes"),
                    "genres": movie_dict.get("genres", []),
                }
                result = session.run(query, **params)
                record = result.single()
                return self._normalize_movie(dict(record["m"]), record["genres"]) if record else {}
        return await asyncio.to_thread(_create)

    async def get_all(self, page: int = 1, limit: int = 10) -> list[dict]:
        skip = (page - 1) * limit
        query = """
        MATCH (m:movies)
        WITH m ORDER BY m.title ASC SKIP $skip LIMIT $limit
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:genres)
        RETURN m, collect(g.genre) AS genres
        """
        def _get_all():
            with self.driver.session() as session:
                result = session.run(query, skip=skip, limit=limit)
                return [self._normalize_movie(dict(record["m"]), record["genres"]) for record in result]
        return await asyncio.to_thread(_get_all)

    async def get_by_id(self, movie_id: str) -> dict | None:
        query = """
        MATCH (m:movies {id: $id})
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:genres)
        RETURN m, collect(g.genre) AS genres
        """
        def _get_by_id():
            with self.driver.session() as session:
                result = session.run(query, id=movie_id)
                record = result.single()
                if not record:
                    return None
                return self._normalize_movie(dict(record["m"]), record["genres"])
        return await asyncio.to_thread(_get_by_id)

    async def update(self, movie_id: str, movie_data: dict) -> dict | None:
        # Build dynamic SET clause only for provided fields to avoid overwriting with nulls
        # movie_data may be a Pydantic model or a dict
        if hasattr(movie_data, "model_dump"):
            data = movie_data.model_dump(exclude_unset=True)
        else:
            data = {k: v for k, v in (movie_data or {}).items() if v is not None}

        if not data:
            return await self.get_by_id(movie_id)

        genres = data.pop("genres", None)

        params = {"id": movie_id, "genres": genres or []}
        set_clauses = []
        for key, value in data.items():
            if key == "year":
                set_clauses.append("m.year = toInteger($%s)" % key)
            elif key == "runtimeMinutes":
                set_clauses.append("m.runtime = toInteger($%s)" % key)
            elif key == "averageRating":
                set_clauses.append("m.averageRating = toFloat($%s)" % key)
            elif key == "numVotes":
                set_clauses.append("m.numVotes = toInteger($%s)" % key)
            else:
                set_clauses.append("m.%s = $%s" % (key, key))
            params[key] = value

        set_clause = ("SET " + ", ".join(set_clauses)) if set_clauses else ""
        genre_clause = """
        WITH m
        FOREACH (_ IN CASE WHEN $genres <> [] THEN [1] ELSE [] END |
            // replace all genre relationships when genres is explicitly provided
        )
        """ if genres is not None else ""

        if genres is not None:
            genre_cypher = """
            WITH m
            OPTIONAL MATCH (m)-[old:BELONGS_TO]->(:genres)
            DELETE old
            WITH DISTINCT m
            UNWIND CASE WHEN $genres = [] THEN [null] ELSE $genres END AS gen
            FOREACH (_ IN CASE WHEN gen IS NOT NULL THEN [1] ELSE [] END |
                MERGE (g:genres {genre: gen})
                MERGE (m)-[:BELONGS_TO]->(g)
            )
            WITH DISTINCT m
            """
        else:
            genre_cypher = "WITH m"

        query = f"""
        MATCH (m:movies {{id: $id}})
        {set_clause}
        {genre_cypher}
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:genres)
        RETURN m, collect(g.genre) AS genres
        """

        def _update():
            with self.driver.session() as session:
                result = session.run(query, **params)
                record = result.single()
                if not record:
                    return None
                return self._normalize_movie(dict(record["m"]), record["genres"])

        return await asyncio.to_thread(_update)

    async def delete(self, movie_id: str) -> bool:
        query = "MATCH (m:movies {id: $id}) DETACH DELETE m RETURN count(m) as deleted_count"
        def _delete():
            with self.driver.session() as session:
                result = session.run(query, id=movie_id)
                record = result.single()
                return record["deleted_count"] > 0 if record else False
        return await asyncio.to_thread(_delete)

    async def search(
        self,
        title: str | None,
        genre: str | None,
        year_min: int | None,
        year_max: int | None,
        rating_min: float | None,
        actor_name: str | None,
        page: int = 1,
        limit: int = 10,
    ) -> list[dict]:

        query = """
        MATCH (m:movies)
        WHERE ($title IS NULL OR toLower(m.title) CONTAINS toLower($title))
        AND ($year_min IS NULL OR m.year >= $year_min)
        AND ($year_max IS NULL OR m.year <= $year_max)
        AND ($rating_min IS NULL OR m.averageRating >= $rating_min)
        AND ($genre IS NULL OR EXISTS {
            MATCH (m)-[:BELONGS_TO]->(g:genres {genre: $genre})
        })
        AND (
            $actor_name IS NULL
            OR EXISTS {
                MATCH (p:persons)-[w:WORKED_IN]->(m)
                WHERE (w.as = 'actor' OR w.as = 'actress')
                AND toLower(p.name) CONTAINS toLower($actor_name)
            }
        )
        WITH DISTINCT m
        SKIP $skip LIMIT $limit
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:genres)
        RETURN m, collect(g.genre) AS genres
        """

        def _search():
            params = {
                "title": title,
                "genre": genre,
                "year_min": year_min,
                "year_max": year_max,
                "rating_min": rating_min,
                "actor_name": actor_name,
                "skip": (page - 1) * limit,
                "limit": limit,
            }

            with self.driver.session() as session:
                result = session.run(query, **params)
                return [
                    self._normalize_movie(dict(record["m"]), record["genres"])
                    for record in result
                ]

        return await asyncio.to_thread(_search)

    async def find_similar(self, movie_id: str, limit: int = 10) -> list[dict]:
        """
        ALERTA DE EXCELENCIA: Consulta de recomendación usando un 
        recorrido de grafo de 2 saltos (Movie -> Atributo/Género/Actor -> SimilarMovie)
        """
        query = """
        MATCH (m:movies {id: $id})-[:WORKED_IN|:BELONGS_TO|:KNOWN_FOR]-(common)
        MATCH (common)--(similar:movies)
        WHERE m <> similar
        WITH similar, count(common) AS score
        ORDER BY score DESC
        LIMIT $limit
        OPTIONAL MATCH (similar)-[:BELONGS_TO]->(g:genres)
        RETURN similar, collect(g.genre) AS genres
        """
        def _find_similar():
            with self.driver.session() as session:
                result = session.run(query, id=movie_id, limit=limit)
                return [self._normalize_movie(dict(record["similar"]), record["genres"]) for record in result]
        return await asyncio.to_thread(_find_similar)
