# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

If we need to re-instantiate the docker containers, run 
```sudo docker-compose -f ./docker/docker-compose.yml up -d```

To access the docker container for postgres:
```sudo docker exec -ti postgres_db psql -U ais aisdb```

Access python client with: 
```sudo docker exec -ti ais_api bash```

Access react client with: 
```sudo docker exec -ti ais_client bash```

Access cleansing container with:
```sudo docker exec -ti ais_cleansing bash```

To execute cleansing without entering the container:
```sudo docker exec -d ais_cleansing python main.py -f True```

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

Access FastAPI on ```http://localhost:8080/``` or ```http://0.0.0.0:8080/```
Access React on ```http://localhost:3000/```

If you wish to install requirements packages and test the python program before running docker, create a virtual enviroment inside the backend folder
```python -m venv env```

Run the virtual environment on Mac with 
```source env/bin/activate```
On windows with ```.\backend\env\Scripts\activate```

## Database setup map-bounds and hexagrid
### Initial setup
1. Create table 
```SQL
CREATE TABLE map_bounds(gid serial PRIMARY KEY, geom geometry(POLYGON, 4326));
```

1. Insert the boundaries, covering the area of concern (in our case, it's Denmarks waters + a little extra)
```SQL
INSERT INTO map_bounds(geom) VALUES('POLYGON((3.24 58.35, 3.24 54.32, 16.49 54.32, 16.49 58.35, 3.24 58.35))');
```

1. Convert the table to SRID 3857 
```SQL
ALTER TABLE map_bounds ALTER COLUMN geom TYPE Geometry(Polygon, 3857) USING ST_Transform(geom, 3857); 
```

1. Analayze the table 
```SQL
ANALYZE map_bounds;
```

### Tables for hexagons
We create two hexagon tables, one with radius = 500 meters, and the other with radius = 10.000 meters.
1. Create the two tables:
```SQL
CREATE TABLE hex_500_dim (hex_500_row INTEGER, hex_500_column INTEGER, PRIMARY KEY(hex_500_row, hex_500_column), hexagon geometry);
CREATE TABLE hex_10000_dim (hex_10000_row INTEGER, hex_10000_column INTEGER, PRIMARY KEY(hex_10000_row, hex_10000_column), hexagon geometry);
```

1. Fill the two tables by running the two queries below:
``` SQL
INSERT INTO hex_500_dim(hex_500_row, hex_500_column, hexagon)
SELECT hexes.j, hexes.i, hexes.geom  
FROM ST_HexagonGrid(500, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 3857)) AS hexes  
INNER JOIN map_bounds AS MB ON ST_Intersects(mb.geom, hexes.geom);
```

``` SQL
INSERT INTO hex_10000_dim(hex_10000_row, hex_10000_column, hexagon)
SELECT hexes.j, hexes.i, hexes.geom  
FROM ST_HexagonGrid(10000, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 3857)) AS hexes  
INNER JOIN map_bounds AS MB ON ST_Intersects(mb.geom, hexes.geom);
```
1. Convert back to 4326:
 ```SQL
 ALTER TABLE hex_500_dim ALTER COLUMN hexagon TYPE Geometry(Polygon, 4326) 
 USING ST_Transform(hexagon, 4326);
 ```
 
```SQL
 ALTER TABLE hex_10000_dim ALTER COLUMN hexagon TYPE Geometry(Polygon, 4326) USING ST_Transform(hexagon, 4326);
 ```