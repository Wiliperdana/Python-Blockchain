import hashlib
import json
import time
import random
from flask import Flask, jsonify, request
import requests
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from typing import List

app = Flask(__name__)

class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def sign_transaction(self, transaction_data):
        return self.private_key.sign(transaction_data.encode()).hex()

    def get_public_key(self):
        return self.public_key.to_string().hex()

def verify_signature(public_key_hex, message, signature):
    public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
    try:
        return public_key.verify(bytes.fromhex(signature), message.encode())
    except:
        return False

class Transaction:
    def __init__(self, sender, recipient, amount, signature=None, timestamp=None, nonce=None, transaction_id=None, chain_id="excoin"):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature
        self.timestamp = timestamp or int(time.time())
        self.nonce = nonce or random.randint(1, 1000000)
        self.transaction_id = transaction_id or self.generate_transaction_id()
        self.chain_id = chain_id

    def generate_transaction_id(self):
        transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}{self.nonce}"
        return hashlib.sha256(transaction_data.encode()).hexdigest()

    def to_dict(self, include_signature=False):
        base = {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'transaction_id': self.transaction_id,
            'chain_id': self.chain_id
        }
        if include_signature:
            base['signature'] = self.signature
        return base

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            sender=d.get('sender'),
            recipient=d.get('recipient'),
            amount=d.get('amount'),
            signature=d.get('signature'),
            timestamp=d.get('timestamp'),
            nonce=d.get('nonce'),
            transaction_id=d.get('transaction_id'),
            chain_id=d.get('chain_id', 'excoin')
        )

    def is_valid(self):
        if self.sender == "Network":  # Mining reward doesn't need signature validation
            return True
        if not self.signature or not self.sender:
            return False
        transaction_data = json.dumps(self.to_dict(), sort_keys=True)
        return verify_signature(self.sender, transaction_data, self.signature)

def calculate_merkle_root(transactions: List[Transaction]) -> str:
    if not transactions:
        return ''
    
    transaction_hashes = [hashlib.sha256(json.dumps(tx.to_dict(), sort_keys=True).encode()).hexdigest() for tx in transactions]

    while len(transaction_hashes) > 1:
        if len(transaction_hashes) % 2 == 1:
            transaction_hashes.append(transaction_hashes[-1])
        
        new_hashes = []
        for i in range(0, len(transaction_hashes), 2):
            combined_hash = hashlib.sha256((transaction_hashes[i] + transaction_hashes[i + 1]).encode()).hexdigest()
            new_hashes.append(combined_hash)
        transaction_hashes = new_hashes

    return transaction_hashes[0]

class Block:
    def __init__(self, index, previous_hash, transactions, nonce=0, hash=None):
        self.index = index
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.merkle_root = calculate_merkle_root(transactions)
        self.nonce = nonce
        self.hash = hash

    def calculate_hash(self):
        block_data = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def mine_block(self, difficulty=4):
        target = '0' * difficulty
        while self.hash is None or self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions: List[Transaction] = []
        self.wallet_balances = {}
        self.nodes = set()
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_transactions = []
        genesis_block = Block(0, "0", genesis_transactions, 0)
        genesis_block.timestamp = 1672531200 
        genesis_block.mine_block()
        self.chain.append(genesis_block)
        # Initialize Network with 0 balance
        self.wallet_balances["Network"] = 0

    def add_block(self, block: Block):
        # Validate all transactions in the block before adding
        for tx in block.transactions:
            if tx.sender != "Network":
                # Check if sender has enough balance
                sender_balance = self.wallet_balances.get(tx.sender, 0)
                if sender_balance < tx.amount:
                    print(f"Transaction {tx.transaction_id} invalid: insufficient funds")
                    return False

        # If all transactions are valid, apply them to balances
        for tx in block.transactions:
            if tx.sender != "Network":
                # Initialize sender balance to 0 if not exists
                if tx.sender not in self.wallet_balances:
                    self.wallet_balances[tx.sender] = 0
                # Subtract amount from sender
                self.wallet_balances[tx.sender] -= tx.amount
                print(f"Subtracted {tx.amount} from {tx.sender[:50]}..., new balance: {self.wallet_balances[tx.sender]}")
            
            # Initialize recipient balance to 0 if not exists
            if tx.recipient not in self.wallet_balances:
                self.wallet_balances[tx.recipient] = 0
            # Add amount to recipient
            self.wallet_balances[tx.recipient] += tx.amount
            print(f"Added {tx.amount} to {tx.recipient[:50]}..., new balance: {self.wallet_balances[tx.recipient]}")

        # Add block to chain
        self.chain.append(block)

        # Remove processed transactions from pending pool
        block_tx_ids = set(tx.transaction_id for tx in block.transactions)
        self.pending_transactions = [tx for tx in self.pending_transactions if tx.transaction_id not in block_tx_ids]

        return True

    def add_transaction(self, transaction: Transaction):
        # For regular transactions, validate the sender has enough balance
        if transaction.sender != "Network":
            sender_balance = self.wallet_balances.get(transaction.sender, 0)
            if sender_balance < transaction.amount:
                print(f"Insufficient funds: {transaction.sender} has {sender_balance}, needs {transaction.amount}")
                return False
        
        if transaction.is_valid():
            # Check for duplicate transaction_id in pending pool
            if any(tx.transaction_id == transaction.transaction_id for tx in self.pending_transactions):
                print("Duplicate transaction in pending pool")
                return False

            self.pending_transactions.append(transaction)
            print(f"Transaction added to pending pool: {transaction.to_dict(include_signature=True)}")
            
            # Broadcast transaction to other nodes
            for node in list(self.nodes):
                try:
                    requests.post(f'http://{node}/transactions/receive', 
                                 json=transaction.to_dict(include_signature=True), 
                                 timeout=3)
                except requests.exceptions.RequestException:
                    pass
            return True
        print("Invalid transaction")
        return False

    def receive_remote_transaction(self, transaction: Transaction):
        if any(tx.transaction_id == transaction.transaction_id for tx in self.pending_transactions):
            return False
        if transaction.is_valid():
            self.pending_transactions.append(transaction)
            print("Received and added remote transaction to pending pool:", transaction.transaction_id)
            return True
        return False

    def _gather_pending_from_network(self):
        gathered = {tx.transaction_id: tx for tx in self.pending_transactions}
        for node in self.nodes:
            try:
                resp = requests.get(f'http://{node}/transactions/pending', timeout=3)
                if resp.status_code == 200:
                    remote_list = resp.json().get('pending', [])
                    for txd in remote_list:
                        tx = Transaction.from_dict(txd)
                        if tx.transaction_id not in gathered:
                            gathered[tx.transaction_id] = tx
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch pending from {node}: {e}")
        return list(gathered.values())

    def mine_pending_transactions(self, miner_address):
        # Gather pending transactions from network
        merged_pending = self._gather_pending_from_network()

        # Create mining reward transaction
        reward_transaction = Transaction("Network", miner_address, 50)

        # Prepare block transactions
        block_transactions = merged_pending.copy()
        block_transactions.append(reward_transaction)

        # Create and mine the block
        last_block = self.chain[-1]
        new_block = Block(len(self.chain), last_block.hash, block_transactions)
        new_block.mine_block()

        # Add block to chain
        if self.add_block(new_block):
            print(f"Block {new_block.index} mined successfully with {len(block_transactions)} transactions")
            return new_block
        else:
            print(f"Failed to add block {new_block.index} - invalid transactions")
            return None

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def register_node(self, address):
        self.nodes.add(address)

    def resolve_conflicts(self):
        longest_chain = None
        max_length = len(self.chain)

        print("Starting resolve_conflicts: Checking with registered nodes for longer chain...")

        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain', timeout=5)
                if response.status_code == 200:
                    length = response.json()['length']
                    chain_data = response.json()['chain']
                    
                    if length > max_length:
                        max_length = length
                        longest_chain = chain_data
                        print(f"New longer chain found at {node} with length {length}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch chain from {node}: {e}")

        if longest_chain:
            # Rebuild wallet balances from the new chain
            temp_wallet_balances = {}
            new_chain = []
            
            for block_data in longest_chain:
                block = Block(
                    index=block_data['index'],
                    previous_hash=block_data['previous_hash'],
                    transactions=[Transaction.from_dict(tx) for tx in block_data['transactions']],
                    nonce=block_data['nonce'],
                    hash=block_data['current_hash']
                )
                new_chain.append(block)

                # Replay all transactions to rebuild balances
                for tx in block.transactions:
                    if tx.sender != "Network":
                        # Initialize sender balance to 0 if not exists
                        if tx.sender not in temp_wallet_balances:
                            temp_wallet_balances[tx.sender] = 0
                        # Subtract amount from sender
                        temp_wallet_balances[tx.sender] -= tx.amount
                    
                    # Initialize recipient balance to 0 if not exists
                    if tx.recipient not in temp_wallet_balances:
                        temp_wallet_balances[tx.recipient] = 0
                    # Add amount to recipient
                    temp_wallet_balances[tx.recipient] += tx.amount

            # Update chain and wallet balances
            self.chain = new_chain
            self.wallet_balances = temp_wallet_balances

            # Clean up pending transactions that are already in the new chain
            chain_tx_ids = set()
            for blk in self.chain:
                for tx in blk.transactions:
                    chain_tx_ids.add(tx.transaction_id)
            self.pending_transactions = [tx for tx in self.pending_transactions if tx.transaction_id not in chain_tx_ids]

            print("Chain replaced with the longer chain from network.")
            return True

        print("Our chain is authoritative. No changes made.")
        return False

blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine_block():
    miner_address = request.args.get('address', 'default_miner')
    block = blockchain.mine_pending_transactions(miner_address)
    
    if block:
        response = {
            'message': 'Block mined',
            'index': block.index,
            'current_hash': block.hash,
            'previous_hash': block.previous_hash,
            'merkle_root': block.merkle_root,
            'nonce': block.nonce,
            'transactions': [tx.to_dict(include_signature=True) for tx in block.transactions]
        }
        
        print("Mining successful, attempting broadcast to other nodes.")
        
        # Broadcast to trigger consensus in other nodes
        for node in blockchain.nodes:
            try:
                print(f"Broadcasting to {node} to resolve conflicts...")
                res = requests.get(f'http://{node}/nodes/resolve', timeout=5)
                print(f"Response from {node}: {res.status_code} - {res.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Could not resolve conflicts with node {node}: {e}")
    else:
        response = {'message': 'No transactions to mine or invalid transactions'}
    return jsonify(response), 200

@app.route('/transactions/add', methods=['POST'])
def add_transaction():
    values = request.get_json()
    required = [
        'sender', 'recipient', 'amount',
        'timestamp', 'nonce', 'transaction_id', 'chain_id', 'signature'
    ]
    if not values or not all(k in values for k in required):
        return 'Missing values', 400

    transaction = Transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount'],
        signature=values['signature'],
        timestamp=values['timestamp'],
        nonce=values['nonce'],
        transaction_id=values['transaction_id'],
        chain_id=values['chain_id']
    )
    if blockchain.add_transaction(transaction):
        response = {'message': 'Transaction will be added to Block'}
    else:
        response = {'message': 'Invalid transaction'}
    return jsonify(response), 201

@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    values = request.get_json()
    if not values:
        return 'Missing values', 400
    tx = Transaction.from_dict(values)
    accepted = blockchain.receive_remote_transaction(tx)
    if accepted:
        return jsonify({'message': 'Transaction received and added to pending'}), 201
    else:
        return jsonify({'message': 'Transaction invalid or duplicate'}), 400

@app.route('/transactions/pending', methods=['GET'])
def get_pending_transactions():
    pending = [tx.to_dict(include_signature=True) for tx in blockchain.pending_transactions]
    return jsonify({'pending': pending}), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = [{
        'index': block.index,
        'current_hash': block.hash,
        'previous_hash': block.previous_hash,
        'merkle_root': block.merkle_root,
        'nonce': block.nonce,
        'transactions': [tx.to_dict(include_signature=True) for tx in block.transactions]
    } for block in blockchain.chain]
    response = {
        'chain': chain_data,
        'length': len(chain_data)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': [{
                'index': block.index,
                'current_hash': block.hash,
                'previous_hash': block.previous_hash,
                'merkle_root': block.merkle_root,
                'nonce': block.nonce,
                'transactions': [tx.to_dict(include_signature=True) for tx in block.transactions]
            } for block in blockchain.chain]
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': [{
                'index': block.index,
                'current_hash': block.hash,
                'previous_hash': block.previous_hash,
                'merkle_root': block.merkle_root,
                'nonce': block.nonce,
                'transactions': [tx.to_dict(include_signature=True) for tx in block.transactions]
            } for block in blockchain.chain]
        }
    return jsonify(response), 200

@app.route('/wallet/create', methods=['GET'])
def create_wallet():
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    public_key_hex = public_key.to_string().hex()

    # Initialize wallet with 0 balance
    blockchain.wallet_balances[public_key_hex] = 0

    response = {
        'private_key': private_key.to_string().hex(),
        'public_key': public_key_hex,
        'balance': 0
    }
    return jsonify(response), 200

@app.route('/transaction/sign', methods=['POST'])
def sign_transaction():
    values = request.get_json()
    required = ['private_key', 'recipient', 'amount']
    
    if not all(k in values for k in required):
        return 'Missing values', 400

    private_key_hex = values['private_key']
    recipient = values['recipient']
    amount = values['amount']
    
    # Get private and public keys from sender
    private_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    public_key = private_key.get_verifying_key().to_string().hex()
    
    # Create transaction
    transaction = Transaction(
        sender=public_key,
        recipient=recipient,
        amount=amount
    )

    # Sign the transaction
    transaction_data = json.dumps(transaction.to_dict(), sort_keys=True)
    signature = private_key.sign(transaction_data.encode()).hex()
    
    # Return transaction data and signature
    response = {
        "transaction": transaction.to_dict(),
        "signature": signature
    }
    return jsonify(response), 200

@app.route('/wallet/balance', methods=['GET'])
def get_balance():
    public_key = request.args.get('public_key')
    if not public_key:
        return jsonify({'message': 'Missing public key'}), 400
    
    # Get balance (0 if wallet doesn't exist)
    balance = blockchain.wallet_balances.get(public_key, 0)
    
    response = {
        'public_key': public_key,
        'balance': balance
    }
    return jsonify(response), 200

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='0.0.0.0', port=port)