# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

To access the docker container for postgres:
```sudo docker exec -ti AIS-database psql -U postgres aisdb```

## Running Docker locally
Build the python image with ```docker build -< docker/python.DockerFile --tag ais_python_project```

Creating the docker container for postgreSQL and postgis:
```sudo docker run --name AIS-database -e POSTGRES_PASSWORD=A401 -d postgis/postgis```

To access the docker container for postgres:
```sudo docker exec -ti AIS-database psql -U postgres```

Create the database with: ```CREATE DATABASE aisdb;```