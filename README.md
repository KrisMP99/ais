# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

To access the docker container for postgres:
```sudo docker exec -ti postgres_db psql -U ais aisdb```

## Running Docker locally
Build both images and containers with ```sudo docker-compose -f ./docker/docker-compose.yml up -d``` in the ais folder from the project

Access python client with: 
```sudo docker exec -ti ais_project bash```

To exit the container, ```exit```
