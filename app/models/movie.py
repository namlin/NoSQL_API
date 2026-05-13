from pydantic import BaseModel, Field


class MovieBase(BaseModel):
    title: str = Field(..., description="Título principal de la película")
    originalTitle: str | None = Field(None, description="Título en idioma original")
    year: int | None = Field(None, description="Año de estreno")
    runtimeMinutes: int | None = Field(None, description="Duración en minutos")
    averageRating: float | None = Field(None, ge=0.0, le=10.0, description="Rating promedio IMDb (0-10)")
    numVotes: int | None = Field(None, ge=0, description="Número de votos IMDb")


class MovieCreate(MovieBase):
    id: str | None = Field(
        None,
        description="ID opcional. Si se omite se genera un UUID. Para datos IMDb, usar el tconst (ej: tt0111161).",
    )
    genres: list[str] = Field(default=[], description="Lista de géneros (ej: ['Action', 'Drama'])")


class MovieUpdate(BaseModel):
    title: str | None = None
    originalTitle: str | None = None
    year: int | None = None
    runtimeMinutes: int | None = None
    averageRating: float | None = Field(None, ge=0.0, le=10.0)
    numVotes: int | None = Field(None, ge=0)
    genres: list[str] | None = None


class MovieResponse(MovieBase):
    id: str = Field(..., description="Identificador único (tconst de IMDb o UUID)")
    genres: list[str] = Field(default=[], description="Géneros relacionados")

    model_config = {"from_attributes": True}
