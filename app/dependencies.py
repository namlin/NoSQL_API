import app.config as config
from app.repositories.base import AbstractMovieRepository
from app.repositories.mock import InMemoryMovieRepository
from app.repositories.neo4j import Neo4jMovieRepository

_repo: AbstractMovieRepository | None = None


def get_repository() -> AbstractMovieRepository:
    global _repo
    if _repo is None:
        if config.DB_BACKEND == "mock":
            _repo = InMemoryMovieRepository()
        elif config.DB_BACKEND == "neo4j":
            _repo = Neo4jMovieRepository()
        else:
            raise ValueError(
                f"Unknown DB_BACKEND: '{config.DB_BACKEND}'. "
                f"Supported values: 'mock', 'neo4j'."
            )
    return _repo