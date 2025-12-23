# Simple Blockchain in Python

This project is a basic implementation of a cryptocurrency blockchain using Python and the Flask web framework. It demonstrates core blockchain concepts such as wallets, transactions, blocks, mining (Proof-of-Work), and a decentralized peer-to-peer network.

## Core Concepts

-   **Wallet**: Uses ECDSA (Elliptic Curve Digital Signature Algorithm) with the SECP256k1 curve (the same one used by Bitcoin) to generate public/private key pairs. Private keys are used to sign transactions, and public keys serve as wallet addresses.
-   **Transaction**: A record of the transfer of value from a sender to a recipient. It is cryptographically signed by the sender to ensure authenticity.
-   **Block**: A collection of transactions, a timestamp, and a reference to the previous block (previous hash). Blocks are chained together to form the blockchain.
-   **Proof-of-Work**: A simple mining algorithm where a "miner" must find a nonce that results in a block hash with a certain number of leading zeros. This process is required to add a new block to the chain.
-   **P2P Network**: The blockchain can run on multiple nodes. Nodes can register with each other, broadcast new transactions, and resolve conflicts by agreeing on the longest valid chain (consensus).

## Installation

1.  **Clone the repository and create a virtual environment:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Flask application:**
    ```bash
    python main.py --port 5000
    ```
    You can specify a different port using the `--port` or `-p` argument.

## Running a Network

To test the decentralization features, you can run multiple nodes on different ports.

**Terminal 1:**
```bash
source .venv/bin/activate
python main.py --port 5001
```

**Terminal 2:**
```bash
source .venv/bin/activate
python main.py --port 5002
```

Then, you can register node 5002 with node 5001:
```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "nodes": ["localhost:5002"]
}' http://localhost:5001/nodes/register
```
Now, when you mine a block or create a transaction on one node, it will be propagated to the other.

## API Endpoints

### Wallet Management

#### `GET /wallet/create`
Creates a new wallet with a unique private/public key pair.

**Example Response:**
```json
{
  "private_key": "...",
  "public_key": "...",
  "balance": 0
}
```

#### `GET /wallet/balance`
Retrieves the balance of a specific wallet.

**Example Request:**
```bash
curl "http://localhost:5001/wallet/balance?public_key=<your-public-key>"
```
**Example Response:**
```json
{
    "balance": 50,
    "public_key": "..."
}
```

### Transactions

#### `POST /transaction/sign`
Signs a transaction with the sender's private key.

**Example Request:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "private_key": "<your-private-key>",
    "recipient": "<recipient-public-key>",
    "amount": 10
}' http://localhost:5001/transaction/sign
```
**Example Response:**
```json
{
    "signature": "...",
    "transaction": {
        "amount": 10,
        "chain_id": "excoin",
        "nonce": 883584,
        "recipient": "...",
        "sender": "...",
        "timestamp": 1678886400,
        "transaction_id": "..."
    }
}
```

#### `POST /transactions/add`
Submits a signed transaction to the node's pending transaction pool.

**Example Request:**
```bash
# Body should contain the full output from /transaction/sign
curl -X POST -H "Content-Type: application/json" -d '{
    "sender": "...",
    "recipient": "...",
    "amount": 10,
    "timestamp": 1678886400,
    "nonce": 883584,
    "transaction_id": "...",
    "chain_id": "excoin",
    "signature": "..."
}' http://localhost:5001/transactions/add
```

### Blockchain & Mining

#### `GET /mine`
Mines a new block, which includes all pending transactions and a mining reward. The new block is added to the chain.

**Example Request:**
```bash
curl "http://localhost:5001/mine?address=<your-public-key-for-reward>"
```

#### `GET /chain`
Returns the entire blockchain stored on the node.

#### `GET /transactions/pending`
Returns a list of all transactions currently in the pending pool.

### Network

#### `POST /nodes/register`
Registers one or more new peer nodes with the current node.

**Example Request:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "nodes": ["localhost:5002", "localhost:5003"]
}' http://localhost:5001/nodes/register
```

#### `GET /nodes/resolve`
Runs the consensus algorithm. The node will query its peers and replace its own chain if it finds a longer, valid chain on the network.
