# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

If we need in re-instantiate the docker containers, run 
```sudo docker-compose -f ./docker/docker-compose.yml up -d```

To access the docker container for postgres:
```sudo docker exec -ti postgres_db psql -U ais aisdb```

Access python client with: 
```sudo docker exec -ti ais_project bash```

## Running Docker locally
Build both images and containers with ```sudo docker-compose -f ./docker/docker-compose-local.yml up -d``` in the ais folder from the project

Access python client with: 
```sudo docker exec -ti ais_project bash```

To exit the container, ```exit```

If you wish to install requirements packages and test the python program before running docker, create a virtual enviroment inside the backend folder
```python -m venv env```

Run the virtual environment on Mac with 
```source env/bin/activate```
On windows with ```venv\Scripts\activate```