# AIS

## Running Docker on server
Docker is already installed on the server
If it is not running, run: ```sudo systemctl start docker```

## Running Docker locally
Creating the docker container:
docker run --name PostgreSQLContainer -e POSTGRES_PASSWORD=mysecretpassword -d postgres