"""
Amazon Neptune (Gremlin/TinkerPop) repository — a implementar cuando la BD esté lista.

Para activar:
  1. pip install gremlinpython
  2. En .env: DB_BACKEND=neptune, DB_URL=wss://<neptune-endpoint>:8182/gremlin
  3. Implementar cada método con las consultas Gremlin correspondientes
  4. En dependencies.py: importar NeptuneMovieRepository y usarlo cuando DB_BACKEND == "neptune"

Consultas Gremlin de referencia:
  - Crear nodo:   g.addV('Movie').property('id', id).property('title', title)...
  - Buscar por ID: g.V().has('Movie', 'id', movie_id).elementMap()
  - Similares:    g.V().has('Movie','id',id).both('HAS_GENRE').in_('HAS_GENRE')
                        .where(neq(source)).groupCount().order(by(values,desc))
"""

from app.models.movie import MovieCreate, MovieResponse, MovieUpdate
from app.repositories.base import AbstractMovieRepository


class NeptuneMovieRepository(AbstractMovieRepository):

    def __init__(self, url: str, user: str = "", password: str = ""):
        # from gremlin_python.driver import client as gremlin_client
        # self._client = gremlin_client.Client(url, "g", username=user, password=password)
        raise NotImplementedError(
            "NeptuneMovieRepository aún no está implementado. "
            "Agrega las consultas Gremlin en cada método."
        )

    async def create(self, movie: MovieCreate) -> MovieResponse:
        raise NotImplementedError

    async def get_all(self, page: int, limit: int) -> list[MovieResponse]:
        raise NotImplementedError

    async def get_by_id(self, movie_id: str) -> MovieResponse | None:
        raise NotImplementedError

    async def update(self, movie_id: str, data: MovieUpdate) -> MovieResponse | None:
        raise NotImplementedError

    async def delete(self, movie_id: str) -> bool:
        raise NotImplementedError

    async def search(
        self,
        title: str | None,
        genre: str | None,
        year_min: int | None,
        year_max: int | None,
        rating_min: float | None,
        actor_name: str | None,
    ) -> list[MovieResponse]:
        raise NotImplementedError

    async def find_similar(self, movie_id: str, limit: int = 10) -> list[MovieResponse]:
        # Ejemplo de traversal de 2 saltos en Gremlin:
        # g.V().has('Movie','id', movie_id)
        #  .both('HAS_GENRE').in_('HAS_GENRE')
        #  .where(neq('source'))
        #  .groupCount().order(by(values, desc)).limit(limit)
        raise NotImplementedError
