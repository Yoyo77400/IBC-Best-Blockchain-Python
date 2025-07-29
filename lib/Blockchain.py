import json
import os
from time import time
from lib.Block import Block
from lib.Transaction import Transaction


class Blockchain:
    def __init__(self, difficulty=2, filename="blockchain.json"):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = difficulty
        self.filename = filename
        self.load_from_file()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time(), "0")
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, recipient, amount):
        if not sender or not recipient or amount <= 0:
            raise ValueError("Transaction invalide")
        transaction = Transaction(sender, recipient, amount)
        self.pending_transactions.append(transaction)

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def mine_pending_transactions(self):
        # if not self.pending_transactions:
        #     return False
        transactions_list  = self.pending_transactions
        transactions_list.append(Transaction("System", "Miner", 1))
        last_block = self.get_last_block()
        new_block = Block(index=last_block.index + 1,
                          transactions=transactions_list,
                          timestamp=time(),
                          previous_hash=last_block.hash)
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []
        return True

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def save_to_file(self):
        data = [{
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": [tx.to_dict() for tx in block.transactions],
            "previous_hash": block.previous_hash,
            "nonce": block.nonce,
            "hash": block.hash
        } for block in self.chain]
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self):
        if not os.path.exists(self.filename):
            self.create_genesis_block()
            return
        with open(self.filename, "r") as f:
            data = json.load(f)
        self.chain = []
        for b in data:
            transactions = [Transaction(**tx) for tx in b["transactions"]]
            block = Block(b["index"], transactions, b["timestamp"], b["previous_hash"], b["nonce"])
            block.hash = b["hash"]
            self.chain.append(block)

    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain) and self.validate_chain(new_chain):
            self.chain = new_chain
            return True
        return False

    def validate_chain(self, chain):
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            if current.hash != current.compute_hash() or current.previous_hash != previous.hash:
                return False
        return True

    def load_external_chain(self, filename):
        if not os.path.exists(filename):
            return None
        with open(filename, "r") as f:
            data = json.load(f)
        external_chain = []
        for b in data:
            transactions = [Transaction(**tx) for tx in b["transactions"]]
            block = Block(b["index"], transactions, b["timestamp"], b["previous_hash"], b["nonce"])
            block.hash = b["hash"]
            external_chain.append(block)
        return external_chain
