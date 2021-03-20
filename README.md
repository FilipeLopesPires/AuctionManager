# Auction Manager
A Blockchain-Based Auction Management System

## Description 

The goal of this project is to provide a system that enables users to create and participate in auctions protected by tight security mechanisms with great emphasis on the blockchain technology.
The resulting product allows for the users to manage auctions, make bids and validate results using their citizen cards for authentication and a command-line interface to interact
with the program.

The basic structure of the program is as follows.
- There are 3 main entities: an auction manager, an auction repository and auction clients.
- The software was designed to support 4 main security features: bids’ confidentiality, integrity and authentication, bid acceptance control and confirmation, bid author identity and anonymity and finally honesty assurance. 
- The messaging system is composed of 2 main sheds: multiple client-interfaces, through which users interact; and two servers, which serve as rendezvous points for all clients to connect. All messages are in JSON format, due to its user-friendly nature, and protected with a hybrid encryption.

## Repository Structure 

/certificates - contains used certificates and revocation lists

/docs - contains the written reports on the conducted work

/keys - contains generated encryption keys

/src - contains the source code written in Python

## Entities

- Auction Client: an application that interacts with a user, enabling them to create and participate in auctions.
- Auction Manager: a server that exposes a connection endpoint through which clients can exchange structured requests/responses with it; the user communicates with the auction manager everytime he chooses to create or close an auction.
- Auction Repository: a server that exposes a connection endpoint through which clients can exchange structured requests/responses with it; the user communicates with the auction repository everytime he chooses to: list auctions (active and closed), list all bids of an auction (only available once the auction has closed), list the user’s bids on all auctions (only available those whose auctions have closed), find out the outcome of an auction and make a bid. 

<img src="https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/SA.png" width="480px">
High level architecture diagram of the Auction Management System.

## Auction Types

- English Auction - a.k.a the Ascending Price Auction, characterized for each bid only being valid if it overcomes the value of the previous one. The user with the latest (highest) bid will be considered the winner and a new bidder receives the information about the current auction value before making his bid.
- Blind Auction - a.k.a the Sealed First-Price Auction, characterized for no bidder knowing the current auction value (hence the name). The user with the highest bid will be considered the winner and a new bidder receives only the information about the auction’s minimum value before making his bid. 
- Reversed Auction - characterized for working in the opposite way of the English Auction, by starting with a high value and each bid only being valid if it’s value is lower than the value of the previous one. The user with the lowest bid by the end of the auction will be considered the winner and a new bidder receives the information about the auction’s maximum, current and minimum values before making his bid. 

## Security Mechanisms

### Author Identification

The first security mechanism lies on the side of the user. It is with a user authentication mechanism that the software assures the existence of a real person on the client end-point.

This authentication is achieved by the connection between the system’s AC and a smartcard reader connected to the user’s host machine with a valid CC inserted. This is done with the help of the Python Library [PyKCS11](https://pypi.org/project/PyKCS11/). All users are identified by a unique username (given to the AC once the program is running) that is intrinsically connected to the CC’s public key, found in the smartcard’s contents. This is crucial for the encryptions needed to communicate with the servers. The CC’s private key is never seen by any entity. This characteristic is assured by the smartcard itself.

### Message Protection

As any system made for end users must be, ours is developed based on the assurance of secure communication channels and complete integrity of every message traded by all entities envolved.

Regarding the security mechanism linked with the messages passed through the sockets’ tunnels, we implemented a hybrid encryption approach. The encryption goes through 2 phases - the first one requires a symmetric key, and the second an asymmetric key-pair. All keys are generated using the Python Library [cryptography](https://pypi.org/project/cryptography/) that ensures the secure implementation of the cryptographic algorithms AES (for the symmetric key) with mode OFB and RSA (for the asymmetric key-pair). 

<img src="https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/ME.png" width="640px">
Message exchange between an AC and the AM.

### Bid Protection & Blockchain Construction

The general idea of how bids are dealt with and stored is as follows: all bids are sent by the AC to the AR, which runs a scan to verify them (regarding the integrity and validity of the bids), and inserts them into the list reserved for the auction to which each belongs; each auction therefore contains a list, and this list suffers from several operations that turn it into a fully encrypted and secure Blockchain.

### Cryptopuzzle Deployment

Cryptopuzzles are an important asset to the Auction Management System since they help regulating the rate at which bids are sent by each user. The main characteristic of a well implemented cryptopuzzle is that it presents a challenge that requires a certain amount of time and effort to be solved. In our case, the cryptopuzzle is a simple comparison of bytes. 

### Dynamic Code: Bid Validation & Valid Bid Modification

Our Auction Management System supports two types of dynamic code - bid validation and valid bid modification - each delimited by a single function. Users may give assign these two functions (or just one, or none) to an auction on creation by writing them in the AC interface according to a specific format.

The validation function will be executed everytime a bid is sent to the AR and validated by the program as the final step to completely validate the bid. This step is ignored if the validation function is empty. The auction creator may apply conditions inside this function such as: preventing bidders from increasing the auction’s current value in very low percentages, making calculations that may be of his interest (with limited scope), etc.

When a user makes a bid, he may choose to subscribe to that auction and define how much is he willing to pay - in this case, the modification function will be activated for him and a thread dedicated to the update of his bids will start. The modification function will be executed by this thread everytime a bid is sent to the AR and completely validated by the server, if the new bid is not from the same user as the one linked to the thread (i.e. if the thread’s original bidder isn’t the one bidding).

### Bid Exposure & Auction Validation

The bid exposure is the security mechanism that allows the system to prove to any user that no corruption takes place during the auctions - by giving the bidder all that the server stores and the keys needed to decrypt and validate the content (if applied).

Our Auction Management System makes available 2 sorts of bid exposure: the exposure of all information about a specific closed auction (excluding the private information about each bidder) and the exposure of all information about all bids made by the user that asks for it. In this subsection we will discuss them individually 

###  Bid Receipts

Receipts are created by the AR when the system consolidates the users’ bids. They are sent as response to the user in the same secure communication channel between the AR and AC. A receipt is a JSON object containing the serial number of the auction, the username, the bid’s amount and the evidence of the operation’s completion. 

It is important to mention that the way the communication channel is built is enough to ensure that the receipt was created by the AR. However, we decided to include a signature inside the receipt as an extra security measure and a more direct proof for the user that reads the receipt. This signature is basically the name of the bid’s owner signed by the AR.

## User Interface

<p float="left">
  <img src="https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/UI.png" width="360px">
  <img src="https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/CP.png" width="360px">
</p>

<p float="left">
  <img src="https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/BE.png" width="360px">
  <img src="https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/BR.png" width="360px">
</p>

## Deployment Instructions

### Requirements

In order to completely deploy the Auction Management System, a person must have:
1. Linux OS or VM (may work with other OS such as Windows but requires changes to the
deployment script)
2. Python 3.6 installed (older versions may work but no guarantees are given)
3. Python PKCS11 module installed
4. Docker Platform installed
5. Smartcard Reader and up-to-date Citizen Card

### Execution

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

## Authors

The authors of this repository are Filipe Pires and João Alegria, and the project was developed for the Computer and Organization Security Course of the licenciate's degree in Informatics Engineering of the University of Aveiro.

For further information, please read our [report](https://github.com/FilipePires98/AuctionManager/blob/master/docs/FinalReport/Report.pdf) or contact us at filipesnetopires@ua.pt or joao.p@ua.pt.




