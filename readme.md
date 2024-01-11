# Blockchain Construction

Implemented a class framework to create a simple but functional blockchain that combines the ideas of proof-of-work, transactions, blocks, and blockchains.

This blockchain has the following consensus rules (it is a little different from Bitcoin to make testing easier)

## Blockchain

1. There are no consensus rules pertaining to the minimum proof-of-work of any blocks.  That is it has no "difficulty adjustment algorithm".
Instead, the code is expected to properly place blocks of different difficulty into the correct place in the blockchain and discover the most-work tip.

2. A block with no transactions (no coinbase) is valid.

3. If a block as > 0 transactions, the first transaction MUST be the coinbase transaction.

##  Merkle Tree of Transactions

1. Use of sha256 hash.
2. Used 0 if additional items are needed to pad odd merkle levels
(more specific information is included below)

## Transactions

1. A transaction with inputs==None is a valid mint (coinbase) transaction.  For these transactions, the coins created does not exceed the per-block "minting" maximum.

2. If the transaction is not a coinbase transaction, coins cannot be created.  In other words, coins spent (inputs) must be >= coins sent (outputs).

3. Constraint scripts (permission to spend) are implemented via python lambda expressions (anonymous functions).  These constraint scripts accept a list of parameters, and return True if
   permission to spend is granted.  If execution of the constraint script throws an exception or returns anything except True, spending is not allowed!

## More Information

Verified transactions, their constraint and satisfier scripts, and tracked the UTXO set.

### Hashlib
Used hashlib.sha256() to do sha256 hashing in python.

### Byte to integer conversion
Converted the sha256 array of bytes to a big endian integer via: int.from_bytes(bunchOfBytes,"big")

