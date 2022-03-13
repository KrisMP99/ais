# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

If we need in re-instantiate the docker containers, run 
```sudo docker-compose -f ./docker/docker-compose.yml up -d```

To access the docker container for postgres:
```sudo docker exec -ti postgres_db psql -U ais aisdb```

Access python client with: 
```sudo docker exec -ti ais_api bash```

Access react client with: 
```sudo docker exec -ti ais_client bash```

## Running Docker locally
Build both images and containers with ```sudo docker-compose -f ./docker/docker-compose-local.yml up -d``` in the ais folder from the project

Access python client with: 
```sudo docker exec -ti ais_api bash```

Access react client with: 
```sudo docker exec -ti ais_client bash```
To exit the container, ```exit```

To access the docker container for postgres:
```sudo docker exec -ti postgres_db psql -U ais aisdb```
To exit the container, ```exit```

1. If is says the database does not exists:
```sudo docker exec -ti postgres_db psql -U ais```
1.1 The container will then open. Create the database with ```CREATE DATABASE aisdb```
1.1 Then ```\q```
1.1 Then ```sudo docker exec -ti postgres_db psql -U ais aisdb;```
1.1 ```CREATE EXTENSION postgis;```

To exit the container, ```\q```

Access FastAPI on ```http://localhost:8008/```
Access React on ```http://localhost:3000/```

If you wish to install requirements packages and test the python program before running docker, create a virtual enviroment inside the backend folder
```python -m venv env```

Run the virtual environment on Mac with 
```source env/bin/activate```
On windows with ```.\backend\env\Scripts\activate```

## Database setup map-bounds
1. Create table ```CREATE TABLE map_bounds(gid serial PRIMARY KEY, geom geometry(POLYGON,4326));```
1. Insert data into table 
```INSERT INTO map_bounds(geom) VALUES('POLYGON((3.24 58.35, 3.24 54.32, 16.49 54.32, 16.49 58.35, 3.24 58.35))');```
1. Analayze the table ```ANALYZE map_bounds;```
1. Create this table too ```CREATE TABLE feature_json_collection(json_collection json));```
1. Then write this dumb query: ```WITH geometry_hexagons AS (SELECT mb.gid, hexes.geom FROM ST_HexagonGrid (0.01, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 4326)) AS hexes INNER JOIN map_bounds AS mb ON ST_Intersects(mb.geom, ST_Transform(hexes.geom, 4326 ) GROUP BY (hexes.geom, mb.gid)) INSERT INTO feature_json_collection SELECT ('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM geometry_hexagons AS t(id, geom);```