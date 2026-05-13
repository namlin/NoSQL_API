import uuid

from app.models.movie import MovieCreate, MovieResponse, MovieUpdate
from app.repositories.base import AbstractMovieRepository

# Almacenamiento en memoria compartido entre todas las instancias
_db: dict[str, dict] = {}


class InMemoryMovieRepository(AbstractMovieRepository):
    """Implementación en memoria para desarrollo. No requiere base de datos."""

    async def create(self, movie: MovieCreate) -> MovieResponse:
        movie_id = movie.id or str(uuid.uuid4())
        data = movie.model_dump()
        data["id"] = movie_id
        _db[movie_id] = data
        return MovieResponse(**data)

    async def get_all(self, page: int = 1, limit: int = 10) -> list[MovieResponse]:
        all_items = list(_db.values())
        start = (page - 1) * limit
        return [MovieResponse(**m) for m in all_items[start : start + limit]]

    async def get_by_id(self, movie_id: str) -> MovieResponse | None:
        data = _db.get(movie_id)
        return MovieResponse(**data) if data else None

    async def update(self, movie_id: str, data: MovieUpdate) -> MovieResponse | None:
        if movie_id not in _db:
            return None
        updates = data.model_dump(exclude_none=True)
        _db[movie_id].update(updates)
        return MovieResponse(**_db[movie_id])

    async def delete(self, movie_id: str) -> bool:
        if movie_id not in _db:
            return False
        del _db[movie_id]
        return True

    async def search(
        self,
        title: str | None = None,
        genre: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        rating_min: float | None = None,
        actor_name: str | None = None,
    ) -> list[MovieResponse]:
        results = []
        for m in _db.values():
            if title and title.lower() not in m.get("title", "").lower():
                continue
            if genre and genre.lower() not in [g.lower() for g in m.get("genres", [])]:
                continue
            if year_min and (m.get("year") is None or m["year"] < year_min):
                continue
            if year_max and (m.get("year") is None or m["year"] > year_max):
                continue
            if rating_min and (m.get("averageRating") is None or m["averageRating"] < rating_min):
                continue
            # actor_name no se puede filtrar sin grafo — se ignora en el mock
            results.append(MovieResponse(**m))
        return results

    async def find_similar(self, movie_id: str, limit: int = 10) -> list[MovieResponse]:
        """Similaridad por géneros compartidos (aproximación sin grafo real)."""
        target = _db.get(movie_id)
        if not target:
            return []
        target_genres = set(target.get("genres", []))
        scored: list[tuple[int, dict]] = []
        for mid, m in _db.items():
            if mid == movie_id:
                continue
            shared = len(target_genres & set(m.get("genres", [])))
            if shared > 0:
                scored.append((shared, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [MovieResponse(**m) for _, m in scored[:limit]]
