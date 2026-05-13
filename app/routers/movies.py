from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_repository
from app.models.movie import MovieCreate, MovieResponse, MovieUpdate
from app.repositories.base import AbstractMovieRepository

router = APIRouter()


@router.post(
    "/",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una película",
)
async def create_movie(
    movie: MovieCreate,
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
):
    return await repo.create(movie)


# IMPORTANTE: /search debe estar definido ANTES de /{movie_id}
# para que FastAPI no lo interprete como un ID con valor "search"
@router.get(
    "/search",
    response_model=list[MovieResponse],
    summary="Buscar películas con filtros",
)
async def search_movies(
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
    title: Annotated[str | None, Query(description="Título (búsqueda parcial, no sensible a mayúsculas)")] = None,
    genre: Annotated[str | None, Query(description="Género exacto (ej: Action, Drama)")] = None,
    year_min: Annotated[int | None, Query(description="Año mínimo de estreno")] = None,
    year_max: Annotated[int | None, Query(description="Año máximo de estreno")] = None,
    rating_min: Annotated[float | None, Query(ge=0.0, le=10.0, description="Rating mínimo IMDb")] = None,
    actor_name: Annotated[
        str | None,
        Query(description="Nombre de actor/actriz (requiere BD de grafos real; ignorado en mock)"),
    ] = None,
):
    return await repo.search(title, genre, year_min, year_max, rating_min, actor_name)


@router.get(
    "/",
    response_model=list[MovieResponse],
    summary="Obtener todas las películas",
)
async def get_all_movies(
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
    page: Annotated[int, Query(ge=1, description="Número de página")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Resultados por página")] = 10,
):
    return await repo.get_all(page, limit)


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Obtener una película por ID",
)
async def get_movie(
    movie_id: str,
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
):
    movie = await repo.get_by_id(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id '{movie_id}' no encontrada.",
        )
    return movie


@router.put(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Actualizar una película",
)
async def update_movie(
    movie_id: str,
    data: MovieUpdate,
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
):
    updated = await repo.update(movie_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id '{movie_id}' no encontrada.",
        )
    return updated


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una película",
)
async def delete_movie(
    movie_id: str,
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
):
    deleted = await repo.delete(movie_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id '{movie_id}' no encontrada.",
        )


@router.get(
    "/{movie_id}/similar",
    response_model=list[MovieResponse],
    summary="Películas similares (traversal de grafo)",
    description=(
        "Devuelve películas similares a la indicada. "
        "En el mock usa géneros compartidos como aproximación. "
        "En la BD de grafos real realiza un traversal de 2 saltos: "
        "Movie → HAS_GENRE → Genre → HAS_GENRE → OtherMovie "
        "y Movie ← ACTED_IN ← Person → ACTED_IN → OtherMovie."
    ),
)
async def get_similar_movies(
    movie_id: str,
    repo: Annotated[AbstractMovieRepository, Depends(get_repository)],
    limit: Annotated[int, Query(ge=1, le=50, description="Máximo de películas similares a retornar")] = 10,
):
    movie = await repo.get_by_id(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Película con id '{movie_id}' no encontrada.",
        )
    return await repo.find_similar(movie_id, limit)
