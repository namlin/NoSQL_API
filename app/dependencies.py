import app.config as config
from app.repositories.base import AbstractMovieRepository
from app.repositories.mock import InMemoryMovieRepository

_repo: AbstractMovieRepository | None = None


def get_repository() -> AbstractMovieRepository:
    global _repo
    if _repo is None:
        if config.DB_BACKEND == "mock":
            _repo = InMemoryMovieRepository()
        else:
            raise ValueError(
                f"Unknown DB_BACKEND: '{config.DB_BACKEND}'. "
                "Supported values: mock. "
                "Add the real DB repository in dependencies.py when ready."
            )
    return _repo
