"""
Script de carga de datos: IMDb + MovieLens → base de datos de grafos.

=== INSTRUCCIONES ===

1. Descargar archivos de datos y colocarlos en ./data/imdb/ y ./data/movielens/:

   IMDb (https://datasets.imdbws.com/):
     data/imdb/title.basics.tsv.gz
     data/imdb/title.ratings.tsv.gz
     data/imdb/title.principals.tsv.gz
     data/imdb/name.basics.tsv.gz

   MovieLens ml-latest-small (https://grouplens.org/datasets/movielens/latest/):
     data/movielens/links.csv
     data/movielens/ratings.csv    (opcional, para nodos User)

2. Configurar .env con DB_BACKEND y DB_URL del motor elegido.

3. Ejecutar:
     python scripts/seed_db.py

=== ORDEN DE CARGA (importante para bases de grafos) ===

  Paso 1 — Nodos Movie    (title.basics filtrado por MovieLens links.csv)
  Paso 2 — Nodos Genre    (géneros únicos extraídos del campo genres de Movie)
  Paso 3 — Nodos Person   (actores/directores de title.principals)
  Paso 4 — Nodos User     (opcional, de MovieLens ratings.csv)
  Paso 5 — Aristas HAS_GENRE   (Movie → Genre)
  Paso 6 — Aristas ACTED_IN    (Person → Movie, category = actor/actress)
  Paso 7 — Aristas DIRECTED    (Person → Movie, category = director)
  Paso 8 — Aristas WROTE       (Person → Movie, category = writer)
  Paso 9 — Aristas RATED       (User → Movie, de MovieLens ratings.csv, opcional)
"""

import csv
import gzip
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
IMDB_DIR = DATA_DIR / "imdb"
MOVIELENS_DIR = DATA_DIR / "movielens"


# ---------------------------------------------------------------------------
# Paso 0 — Leer IDs de MovieLens para filtrar IMDb
# ---------------------------------------------------------------------------

def load_movielens_imdb_ids(links_path: Path) -> set[str]:
    """Devuelve el conjunto de tconst (ej: 'tt0111161') que están en MovieLens."""
    imdb_ids = set()
    with open(links_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # MovieLens almacena el imdbId sin el prefijo 'tt' y sin ceros a la izquierda
            imdb_id = f"tt{row['imdbId'].zfill(7)}"
            imdb_ids.add(imdb_id)
    print(f"  MovieLens links.csv: {len(imdb_ids)} películas encontradas.")
    return imdb_ids


# ---------------------------------------------------------------------------
# Paso 1 — Leer nodos Movie desde IMDb title.basics
# ---------------------------------------------------------------------------

def load_movies(imdb_ids: set[str]) -> list[dict]:
    """Filtra title.basics.tsv.gz por los IDs de MovieLens."""
    movies = []
    path = IMDB_DIR / "title.basics.tsv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["tconst"] not in imdb_ids:
                continue
            if row["titleType"] != "movie":
                continue
            movies.append({
                "id": row["tconst"],
                "title": row["primaryTitle"],
                "originalTitle": row["originalTitle"],
                "year": int(row["startYear"]) if row["startYear"] != "\\N" else None,
                "runtimeMinutes": int(row["runtimeMinutes"]) if row["runtimeMinutes"] != "\\N" else None,
                "genres_raw": row["genres"],  # se procesa en Paso 2
            })
    print(f"  title.basics: {len(movies)} películas cargadas.")
    return movies


# ---------------------------------------------------------------------------
# Paso 2 — Enriquecer con ratings y extraer géneros únicos
# ---------------------------------------------------------------------------

def load_ratings(imdb_ids: set[str]) -> dict[str, dict]:
    """Devuelve {tconst: {averageRating, numVotes}}."""
    ratings = {}
    path = IMDB_DIR / "title.ratings.tsv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["tconst"] in imdb_ids:
                ratings[row["tconst"]] = {
                    "averageRating": float(row["averageRating"]),
                    "numVotes": int(row["numVotes"]),
                }
    print(f"  title.ratings: {len(ratings)} entradas cargadas.")
    return ratings


def extract_genres(movies: list[dict]) -> set[str]:
    genres = set()
    for m in movies:
        if m["genres_raw"] != "\\N":
            for g in m["genres_raw"].split("|"):
                genres.add(g)
    print(f"  Géneros únicos encontrados: {len(genres)}")
    return genres


# ---------------------------------------------------------------------------
# Pasos 3, 6-8 — Leer relaciones desde title.principals
# ---------------------------------------------------------------------------

def load_principals(imdb_ids: set[str]) -> tuple[list[dict], set[str]]:
    """
    Devuelve (lista de relaciones, conjunto de nconst necesarios).
    Filtra solo las categorías relevantes: actor, actress, director, writer.
    """
    relations = []
    person_ids = set()
    path = IMDB_DIR / "title.principals.tsv.gz"
    relevant = {"actor", "actress", "director", "writer"}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["tconst"] not in imdb_ids:
                continue
            if row["category"] not in relevant:
                continue
            relations.append({
                "tconst": row["tconst"],
                "nconst": row["nconst"],
                "category": row["category"],
                "characters": row["characters"] if row["characters"] != "\\N" else None,
                "ordering": int(row["ordering"]),
            })
            person_ids.add(row["nconst"])
    print(f"  title.principals: {len(relations)} relaciones, {len(person_ids)} personas únicas.")
    return relations, person_ids


# ---------------------------------------------------------------------------
# Paso 3 — Leer nodos Person desde name.basics
# ---------------------------------------------------------------------------

def load_persons(person_ids: set[str]) -> list[dict]:
    persons = []
    path = IMDB_DIR / "name.basics.tsv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["nconst"] not in person_ids:
                continue
            professions = row["primaryProfession"].split(",") if row["primaryProfession"] != "\\N" else []
            persons.append({
                "id": row["nconst"],
                "name": row["primaryName"],
                "birthYear": int(row["birthYear"]) if row["birthYear"] != "\\N" else None,
                "deathYear": int(row["deathYear"]) if row["deathYear"] != "\\N" else None,
                "primaryProfession": professions[0] if professions else None,
            })
    print(f"  name.basics: {len(persons)} personas cargadas.")
    return persons


# ---------------------------------------------------------------------------
# Paso 4 — Leer nodos User y aristas RATED desde MovieLens (opcional)
# ---------------------------------------------------------------------------

def load_user_ratings(links_path: Path, ratings_path: Path) -> tuple[set[str], list[dict]]:
    """Devuelve (set de userIds, lista de {userId, tconst, rating, timestamp})."""
    # Construir mapeo movieId → tconst
    movielens_to_imdb: dict[str, str] = {}
    with open(links_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            movielens_to_imdb[row["movieId"]] = f"tt{row['imdbId'].zfill(7)}"

    user_ids = set()
    rated_edges = []
    with open(ratings_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tconst = movielens_to_imdb.get(row["movieId"])
            if not tconst:
                continue
            user_ids.add(row["userId"])
            rated_edges.append({
                "userId": row["userId"],
                "tconst": tconst,
                "rating": float(row["rating"]),
                "timestamp": int(row["timestamp"]),
            })
    print(f"  ratings.csv: {len(user_ids)} usuarios, {len(rated_edges)} calificaciones.")
    return user_ids, rated_edges


# ---------------------------------------------------------------------------
# Main — TODO: conectar al motor de grafos y hacer las inserciones
# ---------------------------------------------------------------------------

def main():
    print("=== Iniciando carga de datos ===\n")

    links_path = MOVIELENS_DIR / "links.csv"
    ratings_path = MOVIELENS_DIR / "ratings.csv"

    if not links_path.exists():
        print(f"ERROR: no se encontró {links_path}")
        print("Descarga MovieLens ml-latest-small y coloca los archivos en data/movielens/")
        return

    print("Paso 0 — Leyendo IDs de MovieLens...")
    imdb_ids = load_movielens_imdb_ids(links_path)

    print("\nPaso 1 — Cargando películas de IMDb...")
    movies = load_movies(imdb_ids)

    print("\nPaso 2 — Cargando ratings y extrayendo géneros...")
    ratings_map = load_ratings(imdb_ids)
    genres = extract_genres(movies)

    print("\nPaso 3 — Cargando relaciones y personas...")
    relations, person_ids = load_principals(imdb_ids)
    persons = load_persons(person_ids)

    include_users = ratings_path.exists()
    user_ids, rated_edges = set(), []
    if include_users:
        print("\nPaso 4 — Cargando usuarios y ratings de MovieLens...")
        user_ids, rated_edges = load_user_ratings(links_path, ratings_path)

    print("\n=== Resumen de datos preparados ===")
    print(f"  Nodos Movie:  {len(movies)}")
    print(f"  Nodos Genre:  {len(genres)}")
    print(f"  Nodos Person: {len(persons)}")
    print(f"  Nodos User:   {len(user_ids)}")
    print(f"  Aristas HAS_GENRE: (derivadas de {len(movies)} películas)")
    print(f"  Aristas de personas (ACTED_IN/DIRECTED/WROTE): {len(relations)}")
    print(f"  Aristas RATED: {len(rated_edges)}")

    print("\n=== TODO: insertar en la base de datos de grafos ===")
    print("  Implementar las funciones de inserción con el driver correspondiente:")
    print("  - gremlinpython (Neptune)")
    print("  - neo4j (Neo4j)")
    print("  - python-arango (ArangoDB)")
    print("  y llamarlas aquí en el orden de carga documentado arriba.")


if __name__ == "__main__":
    main()
