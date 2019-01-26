# Block-Chain Based Auction Manager

This project consists in a system that supports creating auctions, making bids, listing bids and auctions and all the relevant operations in this context. All this features are implemented in a totally secure maner.

## How to run the project

To run the system execute the following commands(inside the git repository):
```
docker network create --subnet=172.18.0.0/16 sio
docker build -t repo .
```
After this you have to modify the Dockerfile to generate the image of the second server. There are 2 ENTRYPOINT lines, one is commented, you just need to uncomment the commented line and comment the other one. Then execute the following commands:
```
docker build -t man .
docker run -d -p 8765:8765 --network=sio --ip=172.18.0.10 --name mc man
docker run -d -p 7654:7654 --network=sio --ip=172.18.0.11 --name rc repo
```
And the instanciate a client you just need to run:
```
python3 sioClient.py
```