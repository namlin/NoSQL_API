import asyncio
from neo4j import GraphDatabase
import app.config as config
from app.repositories.base import AbstractMovieRepository

class Neo4jMovieRepository(AbstractMovieRepository):
    def __init__(self):
        self.driver = GraphDatabase.driver(config.NEO4J_URI, auth=None)

    def close(self):
        """Cierra el pool de conexiones del driver de forma segura."""
        self.driver.close()

    async def create(self, movie_data) -> dict:
        query = """
        CREATE (m:Movie {
            id: $id, 
            title: $title, 
            originalTitle: $originalTitle,
            year: toInteger($year), 
            runtimeMinutes: toInteger($runtimeMinutes), 
            averageRating: toFloat($averageRating),
            numVotes: toInteger($numVotes),
            genres: $genres
        })
        RETURN m
        """
        def _create():
            with self.driver.session() as session:
                # Convert Pydantic model to dict if needed
                if hasattr(movie_data, 'model_dump'):
                    movie_dict = movie_data.model_dump()
                else:
                    movie_dict = movie_data
                result = session.run(query, **movie_dict)
                record = result.single()
                return dict(record["m"]) if record else {}
        return await asyncio.to_thread(_create)

    async def get_all(self, page: int = 1, limit: int = 10) -> list[dict]:
        skip = (page - 1) * limit
        query = """
        MATCH (m:Movie)
        RETURN m
        ORDER BY m.title ASC
        SKIP $skip LIMIT $limit
        """
        def _get_all():
            with self.driver.session() as session:
                result = session.run(query, skip=skip, limit=limit)
                return [dict(record["m"]) for record in result]
        return await asyncio.to_thread(_get_all)

    async def get_by_id(self, movie_id: str) -> dict | None:
        query = "MATCH (m:Movie {id: $id}) RETURN m"
        def _get_by_id():
            with self.driver.session() as session:
                result = session.run(query, id=movie_id)
                record = result.single()
                return dict(record["m"]) if record else None
        return await asyncio.to_thread(_get_by_id)

    async def update(self, movie_id: str, movie_data: dict) -> dict | None:
        query = """
        MATCH (m:Movie {id: $id})
        SET m.title = $title,
            m.year = toInteger($year),
            m.runtime = toInteger($runtime),
            m.rating = toFloat($rating),
            m.genres = $genres
        RETURN m
        """
        def _update():
            payload = {**movie_data, "id": movie_id}
            with self.driver.session() as session:
                result = session.run(query, **payload)
                record = result.single()
                return dict(record["m"]) if record else None
        return await asyncio.to_thread(_update)

    async def delete(self, movie_id: str) -> bool:
        query = "MATCH (m:Movie {id: $id}) DETACH DELETE m RETURN count(m) as deleted_count"
        def _delete():
            with self.driver.session() as session:
                result = session.run(query, id=movie_id)
                record = result.single()
                return record["deleted_count"] > 0 if record else False
        return await asyncio.to_thread(_delete)

    async def search(self, filters: dict) -> list[dict]:
        """Búsqueda dinámica multi-filtro usando Cypher adaptable."""
        query = """
        MATCH (m:Movie)
        WHERE ($title IS NULL OR toLower(m.title) CONTAINS toLower($title))
          AND ($genre IS NULL OR $genre IN m.genres)
          AND ($year_min IS NULL OR m.year >= toInteger($year_min))
          AND ($year_max IS NULL OR m.year <= toInteger($year_max))
          AND ($rating_min IS NULL OR m.rating >= toFloat($rating_min))
        RETURN m
        LIMIT 50
        """
        def _search():
            params = {
                "title": filters.get("title"),
                "genre": filters.get("genre"),
                "year_min": filters.get("year_min"),
                "year_max": filters.get("year_max"),
                "rating_min": filters.get("rating_min")
            }
            
            with self.driver.session() as session:
                result = session.run(query, **params)
                return [dict(record["m"]) for record in result]
        return await asyncio.to_thread(_search)

    async def find_similar(self, movie_id: str, limit: int = 10) -> list[dict]:
        """
        ALERTA DE EXCELENCIA: Consulta de recomendación usando un 
        recorrido de grafo de 2 saltos (Movie -> Atributo/Género/Actor -> SimilarMovie)
        """
        query = """
        MATCH (m:Movie {id: $id})-[:ACTED_IN|DIRECTED|HAS_GENRE]-(common)-(similar:Movie)
        WHERE m <> similar
        RETURN similar, count(common) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        def _find_similar():
            with self.driver.session() as session:
                result = session.run(query, id=movie_id, limit=limit)
                return [dict(record["similar"]) for record in result]
        return await asyncio.to_thread(_find_similar)