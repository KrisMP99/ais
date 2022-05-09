# AIS
## Introduction
This project's primary goal is to calculate the estimated time of arrival (ETA) of ships, and present it in a user-friendly vizual form.
The project uses data from the automatic identification system (AIS).

The pipeline works by first (automatically) downloading AIS-data from an FTP-server, which is then loaded into memory. From here, erroneous data is removed (such as ships sailing faster than physically possible or missing data which is needed for the project (e.g., a timestamp)) and then it is split into trips. A trip is defined by consisting of only valid points, along with being within some given thresholds. The data is then loaded into a star-schema in Postgres using the PygramETL library, and finally some additional attributes are calculated and updated for the tables, such as each point's location in a given hexagon or square grid.

The backend is developed in Python, using popular libraries such as Pandas (along with the GeoPandas extension), and the data is stored in a Postgres database, which uses the PostGis extension.
The frontend is developed using React and Typescript.
The entire project (frontend + backend) is setup in Docker, using 4 different containers. See below how to get started.

This project is a bachelors project, developed by the group `cs-22-sw-6-11` at Aalborg University, 2022. 


## Getting started [WIP]
Wether you're setting up locally or on a server, the following is required to be installed on your system:
1. Docker
2. Git

Begin by cloning the project to a location you can easily access. We used `/srv/data/ais/` on our server.
```git clone https://github.com/KrisMP99/ais.git```


## Running Docker on server
Docker is already installed on the server
If it is not running, run: 
```
sudo systemctl start docker
```

If we need to re-instantiate the docker containers, run 
```
sudo docker-compose -f ./docker/docker-compose.yml up -d
```

To access the docker container for postgres:
```
sudo docker exec -ti postgres_db psql -U ais aisdb
```

Access python client with: 
```
sudo docker exec -ti ais_api bash
```

Access react client with: 
```
sudo docker exec -ti ais_client bash
```

Access cleansing container with:
```
sudo docker exec -ti ais_cleansing bash
```

To execute cleansing without entering the container:
```
sudo docker exec -d ais_cleansing python main.py -f True
```

## Running Docker locally
Build both images and containers from the ais folder in the project with: 
```
sudo docker-compose -f ./docker/docker-compose-local.yml up -d
```

Access python client with: 
```
sudo docker exec -ti ais_api bash
```

Access react client with: 
```
sudo docker exec -ti ais_client bash
```
To exit the container, ```exit```

Access cleansing container with:
```
sudo docker exec -ti ais_cleansing bash
```
To exit the container, ```exit```

To access the docker container for postgres:
```
sudo docker exec -ti postgres_db psql -U ais aisdb
```
To exit the container, ```\q```

1. If is says the database does not exists:
    ```
    sudo docker exec -ti postgres_db psql -U ais
    ```
    1. The container will then open. Create the database with 
        ```SQL 
        CREATE DATABASE aisdb;
        ```

    1. Then ```\q```
    1. Then 
        ```
        sudo docker exec -ti postgres_db psql -U ais aisdb;
        ```
    1. ```SQL
        CREATE EXTENSION postgis;
        ```

To exit the container, ```\q```

Access FastAPI on ```http://localhost:8080/``` or ```http://0.0.0.0:8080/```
Access React on ```http://localhost:3000/```

If you wish to install requirements packages and test the python program before running docker, create a virtual enviroment inside the backend folder
```
python -m venv env
```

Run the virtual environment on Mac with:
```
source env/bin/activate
```
On windows with:
```
.\backend\env\Scripts\activate
```

## Database setup map-bounds and hexagrid
### Initial setup
....
