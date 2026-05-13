from abc import ABC, abstractmethod

from app.models.movie import MovieCreate, MovieResponse, MovieUpdate


class AbstractMovieRepository(ABC):

    @abstractmethod
    async def create(self, movie: MovieCreate) -> MovieResponse: ...

    @abstractmethod
    async def get_all(self, page: int, limit: int) -> list[MovieResponse]: ...

    @abstractmethod
    async def get_by_id(self, movie_id: str) -> MovieResponse | None: ...

    @abstractmethod
    async def update(self, movie_id: str, data: MovieUpdate) -> MovieResponse | None: ...

    @abstractmethod
    async def delete(self, movie_id: str) -> bool: ...

    @abstractmethod
    async def search(
        self,
        title: str | None,
        genre: str | None,
        year_min: int | None,
        year_max: int | None,
        rating_min: float | None,
        actor_name: str | None,
    ) -> list[MovieResponse]: ...

    @abstractmethod
    async def find_similar(self, movie_id: str, limit: int) -> list[MovieResponse]: ...
