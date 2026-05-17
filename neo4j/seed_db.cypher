//Cargar peliculas de title.basics
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=1MvgGgqUAVDdaivIs9idcmBPILmj5Z7mm'
AS row
CREATE (m:movies {id: row.tconst, title: row.primaryTitle, runtime: row.runtimeMinutes})
RETURN m LIMIT 50;


//Crear indice que agiliza equivalencias 
CREATE INDEX movies_range_index_id FOR (m:movies) ON (m.id);


//Agregar rating promedio a peliculas desde title.rating
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=1bnIRLmg0RyNWi8A5mjsZEq-CTaoT_pCe'
AS row
MATCH (m:movies {id: row.tconst})
SET m.averageRating = row.averageRating
RETURN m LIMIT 50;


//Cargar actores de name.basics
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=16bRmF2MPYlPjD6rD3vrXCjQgl4jcRdAQ'
AS row
CREATE (p:persons {id: row.nconst, name: row.primaryName, birthYear: row.birthYear})
RETURN p LIMIT 50;


//Crear indice que agiliza equivalencias 
CREATE INDEX persons_range_index_id FOR (p:persons) ON (p.id);


//Crear relaciones entre actores, directores, cinematografos, etc. y peliculas desde title.principals
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=1RNvh3HNHkaACMAQx31mxWhGub965f3BQ'
AS row
MATCH (p:persons {id: row.nconst})
MATCH (m:movies {id: row.tconst})
MERGE (p)-[r:WORKED_IN {as: row.category}]->(m)
RETURN p, r, m LIMIT 100;


//Crear nodos con generos desde title.basics
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=1MvgGgqUAVDdaivIs9idcmBPILmj5Z7mm'
AS row
UNWIND split(row.genres, ',') AS gen
WITH DISTINCT gen
MERGE (g:genres {genre: gen})
RETURN g LIMIT 100;


//Crear relaciones entre peliculas y generos desde title.basics
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=1MvgGgqUAVDdaivIs9idcmBPILmj5Z7mm'
AS row
UNWIND split(row.genres, ',') AS gen
MATCH (g:genres {genre: gen})
MATCH (m:movies {id: row.tconst})
MERGE (m)-[r:BELONGS_TO]->(g)
RETURN m, r, g LIMIT 100;


//Crear relacion entre personas y sus trabajos famosos desde name.basics
LOAD CSV WITH HEADERS
FROM 'https://drive.google.com/uc?export=download&id=16bRmF2MPYlPjD6rD3vrXCjQgl4jcRdAQ'
AS row
UNWIND split(row.knownForTitles, ',') AS knownFor
MATCH (p:persons {id: row.nconst})
MATCH (m:movies {id: knownFor})
MERGE (p)-[r:KNOWN_FOR]->(m)
RETURN p, r, m LIMIT 100;