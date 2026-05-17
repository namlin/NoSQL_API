from fastapi import FastAPI

from app.routers import movies

app = FastAPI(
    title="Movie Graph API",
    description=(
        "API RESTful para un catálogo de películas respaldado por una base de datos de grafos.\n\n"
        "**CI-0141 Bases de Datos Avanzadas — Universidad de Costa Rica**\n\n"
    ),
    version="1.0.0",
)

app.include_router(movies.router, prefix="/api/movies", tags=["movies"])


@app.get("/", tags=["health"], summary="Health check")
async def root():
    return {"status": "ok", "docs": "/docs", "redoc": "/redoc"}
