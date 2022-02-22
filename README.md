# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

To access the docker container for postgres:
```sudo docker exec -ti AIS-database psql -U postgres aisdb```

## Running Docker locally
Build both images and containers with ```docker-compose -f ./docker/docker-compose.yml up``` in the ais folder