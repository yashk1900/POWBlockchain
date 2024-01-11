"""
In this assignment you will extend and implement a class framework to create a simple but functional blockchain that combines the ideas of proof-of-work, transactions, blocks, and blockchains.
You may create new member functions, but DO NOT MODIFY any existing APIs.  These are the interface into your blockchain.


This blockchain has the following consensus rules (it is a little different from Bitcoin to make testing easier):

Blockchain

1. There are no consensus rules pertaining to the minimum proof-of-work of any blocks.  That is it has no "difficulty adjustment algorithm".
Instead, your code will be expected to properly place blocks of different difficulty into the correct place in the blockchain and discover the most-work tip.

2. A block with no transactions (no coinbase) is valid (this will help us isolate tests).

3. If a block as > 0 transactions, the first transaction MUST be the coinbase transaction.

Block Merkle Tree

1. You must use sha256 hash 
2. You must use 0 if additional items are needed to pad odd merkle levels
(more specific information is included below)

Transactions

1. A transaction with inputs==None is a valid mint (coinbase) transaction.  The coins created must not exceed the per-block "minting" maximum.

2. If the transaction is not a coinbase transaction, coins cannot be created.  In other words, coins spent (inputs) must be >= coins sent (outputs).

3. Constraint scripts (permission to spend) are implemented via python lambda expressions (anonymous functions).  These constraint scripts must accept a list of parameters, and return True if
   permission to spend is granted.  If execution of the constraint script throws an exception or returns anything except True do not allow spending!

461: You may assume that every submitted transaction is correct.
     This means that you should just make the Transaction validate() function return True
     You do not need to worry about tracking the UTXO (unspent transaction outputs) set.

661: You need to verify transactions, their constraint and satisfier scripts, and track the UTXO set.


Some useful library functions:

Read about hashlib.sha256() to do sha256 hashing in python.
Convert the sha256 array of bytes to a big endian integer via: int.from_bytes(bunchOfBytes,"big")

Read about the "dill" library to serialize objects automatically (dill.dumps()).  "Dill" is like "pickle", but it can serialize python lambda functions, which you need to install via "pip3 install dill".  The autograder has this library pre-installed.
You'll probably need this when calculating a transaction id.

"""
import sys
assert sys.version_info >= (3, 6)
import hashlib
import pdb
import copy
import json
# import np
# pip3 install dill
import dill as serializer

class Output:
    """ This models a transaction output """
    # A PRIVATE VARIABLE TO STORE THE VALUES
    _value = None
    # PRIVATE FUNCTION TO STORE AND CHECK THE PASSED CONSTRAINT FUNCTION
    _constraints = None
    def __init__(self, constraint = None, amount = 0):
        """ constraint is a function that takes 1 argument which is a list of 
            objects and returns True if the output can be spent.  For example:
            Allow spending without any constraints (the "satisfier" in the Input object can be anything)
            lambda x: True

            Allow spending if the spender can add to 100 (example: satisfier = [40,60]):
            lambda x: x[0] + x[1] == 100

            If the constraint function throws an exception, do not allow spending.
            For example, if the satisfier = ["a","b"] was passed to the previous constraint script

            If the constraint is None, then allow spending without constraint
            amount is the quantity of tokens associated with this output """
        self._value = amount
        self._constraints = constraint
    
    def getValue(self):
        return self._value
        # pass

class Input:
    """ This models an input (what is being spent) to a blockchain transaction """
    # VARIABLE TO IDENTIFY PREVIOUS OUTPUT TO REFERENCE
    _prev_txn_hash = None
    _prev_txn_index = None
    # LIST OF OBJECTS TO PASS TO RELEVANT OUTPUT
    _satisfier = None
    def __init__(self, txHash, txIdx, satisfier):
        """ This input references a prior output by txHash and txIdx.
            txHash is therefore the prior transaction hash
            txIdx identifies which output in that prior transaction is being spent.  It is a 0-based index.
            satisfier is a list of objects that is be passed to the Output constraint script to prove that the output is spendable.
        """
        self._prev_txn_hash = txHash
        self._prev_txn_index = txIdx
        self._satisfier = satisfier

    def getPrevTxnHash(self):
        return self._prev_txn_hash
    
    def getPrevTxnIndex(self):
        return self._prev_txn_index

        # pass

class Transaction:
    """ This is a blockchain transaction """
    # MAKE THEM PRIVATE LATER
    inputs = None
    outputs = None
    fee =0
    data=None 
    def __init__(self, inputs=None, outputs=None, data = None):
        """ Initialize a transaction from the provided parameters.
            inputs is a list of Input objects that refer to unspent outputs.
            outputs is a list of Output objects.
            data is a byte array to let the transaction creator put some 
              arbitrary info in their transaction.
        """
        # LIST OF INPUTS
        self.inputs = inputs
        # LIST OF OUTPUTS
        self.outputs = outputs
        # INPUT SUM - OUTPUT SUM
        self.fee = 0
        self.data = data
        # pass

    def getHash(self):
        """Return this transaction's probabilistically unique identifier as a big-endian integer"""
        tx_serialized = serializer.dumps(self)
        tx_hash = hashlib.sha256(tx_serialized).hexdigest()
        return int(tx_hash,16)

    def getInputs(self):
        """ return a list of all inputs that are being spent """
        return self.inputs

    def getOutput(self, n):
        """ Return the output at a particular index """
        return self.outputs[n]

    def validateMint(self, maxCoinsToCreate):
        """ Validate a mint (coin creation) transaction.
            A coin creation transaction should have no inputs,
            and the sum of the coins it creates must be less than maxCoinsToCreate.
        """
        if self.inputs == None:
            # if self._outputs == None:
            #     return False        
            output_sum = 0
            if self.outputs != None:
                for o in self.outputs:
                    output_sum = output_sum + o.getValue()
            if(output_sum<=maxCoinsToCreate):
                return True
            else: return False
        return False
        # mint = Transaction(None, [Output(lambda x: True, maxCoinsToCreate)])
        # return mint
        # pass

    def validate(self, unspentOutputDict):
        """ Validate this transaction given a dictionary of unspent transaction outputs.
            unspentOutputDict is a dictionary of items of the following format: { (txHash, offset) : Output }
        """
        # first go throught the inputs array
        print("In transaction validation")
        input_sum=0
        if self.inputs != None:
            for input in self.inputs:
                txn_hash = input._prev_txn_hash
                txn_id = input._prev_txn_index
                #  THERE WILL BE 1 OUPUT FOR 1 SPECIFIC TXN ID
                if (txn_hash,txn_id) in unspentOutputDict:
                    output = unspentOutputDict[(txn_hash,txn_id)]
                    print("output value: ",output.getValue())
                    print("output constraint: ",output._constraints)
                    # check if output is accessible
                    try:
                        if(output._constraints(input._satisfier)):
                            input_sum = input_sum+output.getValue()
                        else:
                            print("Constraints failed")
                            return False
                    except:
                        return False
                else: 
                    print("couldn't find the given tx hash:",txn_hash," txid: ",txn_id)
                    return False
        # now  check the output
        output_sum =0
        if self.outputs != None:
            for o in self.outputs:
                output_sum = output_sum + o.getValue()

        #  The excess coins are lost
        print("input sum: ",input_sum," output sum:",output_sum)
        if input_sum >= output_sum:
            return True
        else:
            return False 

class GivesHash:
    def __init__(self, hash):
        self.hash = hash

    def getHash(self):
        return self.hash
    
class HashableMerkleTree:
    """ A merkle tree of hashable objects.

        If no transaction or leaf exists, use 32 bytes of 0.
        The list of objects that are passed must have a member function named
        .getHash() that returns the object's sha256 hash as an big endian integer.

        Your merkle tree must use sha256 as your hash algorithm and big endian
        conversion to integers so that the tree root is the same for everybody.
        This will make it easy to test.

        If a level has an odd number of elements, append a 0 value element.
        if the merkle tree has no elements, return 0.

    """
    _merkle_root = None
    _tx_list = None

    def __init__(self, hashableList = None):
        self._tx_list = hashableList
        # add 0 elements to make it a power of n
        pass
    def getTxList(self):
        return self._tx_list
    
    def calcMerkleRoot(self):
        """ Calculate the merkle root of this tree."""
        # take the hash of all the elements and consider them as leaf
        if not self._tx_list:
            return 0
        if len(self._tx_list) == 0:
            return 0
        while len(self._tx_list) > 1:
            print("Length: ",len(self._tx_list))
            if len(self._tx_list) % 2 != 0:
                self._tx_list.append(GivesHash(0))  # Pad with 0 for odd levels
            new_level = []
            for i in range(0, len(self._tx_list), 2):
                combined_hash = hashlib.sha256(
                    (self._tx_list[i].getHash().to_bytes(32, "big") + self._tx_list[i + 1].getHash().to_bytes(32, "big"))
                ).hexdigest()
                new_level.append(GivesHash(int(combined_hash, 16)))
            self._tx_list = new_level

        return self._tx_list[0].getHash()


class BlockContents:
    """ The contents of the block (merkle tree of transactions)
        This class isn't really needed.  I added it so the project could be cut into
        just the blockchain logic, and the blockchain + transaction logic.
    """
    data=None
    def __init__(self):
        # WHAT IS THE HASHABLE LIST?
        self.data = HashableMerkleTree()

    def setData(self, d):
        self.data = d

    def getData(self):
        return self.data

    def calcMerkleRoot(self):
        return self.data.calcMerkleRoot()

class Block:
    """ This class should represent a blockchain block.
        It should have the normal fields needed in a block and also an instance of "BlockContents"
        where we will store a merkle tree of transactions.
    """

    _nonce = None
    _timestamp = None
    _version = None
    _merkle_root = None
    _prev_hash = None
    _target = None
    _block_contents = None
    # THIS STORES THE UTXO AT THE TIME IT WAS MINED

    def __init__(self):
        # Hint, beyond the normal block header fields what extra data can you keep track of per block to make implementing other APIs easier?
        pass

    def getContents(self):
        """ Return the Block content (a BlockContents object)"""
        return self._block_contents
        # pass

    def setContents(self, data):
        """ set the contents of this block's merkle tree to the list of objects in the data parameter """
        b = BlockContents()
        b.setData(data)
        self._block_contents = b
        # pass

    def setTarget(self, target):
        """ Set the difficulty target of this block """
        self._target = target
        pass

    def getTarget(self):
        """ Return the difficulty target of this block """
        return self._target
        pass

    def getHash(self):
        """ Calculate the hash of this block. Return as an integer """
        # Just serialize the block?
        tx_serialized = serializer.dumps(self)
        tx_hash = hashlib.sha256(tx_serialized).hexdigest()
        return int(tx_hash, 16)

    def setPriorBlockHash(self, priorHash):
        """ Assign the parent block hash """
        self._prev_hash = priorHash

    def getPriorBlockHash(self):
        """ Return the parent block hash """
        return self._prev_hash
    
    def mine(self,tgt):
        """Update the block header to the passed target (tgt) and then search for a nonce which produces a block who's hash is less than the passed target, "solving" the block"""
        self.setTarget(tgt)
        self._nonce=0
        while self.getHash() >= self.getTarget():
            self._nonce += 1
        # return True   

    def validate(self, unspentOutputs, maxMint):
        """ Given a dictionary of unspent outputs, and the maximum amount of
            coins that this block can create, determine whether this block is valid.
            Valid blocks satisfy the POW puzzle, have a valid coinbase tx, and have valid transactions (if any exist).

            Return None if the block is invalid.

            Return something else if the block is valid

            661 hint: you may want to return a new unspent output object (UTXO set) with the transactions in this
            block applied, for your own use when implementing other APIs.

            461: you can ignore the unspentOutputs field (just pass {} when calling this function)
        """
        print(" ")
        print("Txn being validated: ",self.getContents())
        # # MINE THE BLOCK
        # self.mine(self._target)

        # POW CHECK
        candidate_hash = self.getHash()
        if(candidate_hash>=self._target):
            print("pow failed")
            return None

        # CHECK CONTENT AND TXNs
        block_content = self.getContents()
        # IF EMPTY BLOCK RETURN TRUE
        if block_content == None:
            # ADDING UTXO FOR THE NEW BLOCK
            print("Empty block")
            return unspentOutputs
            
        
        txn_list = block_content.getData()

        # TRANSACTION CHECKS
        if len(txn_list)>0:
            # CHECK FOR COINBASE TXN
            if not txn_list[0].validateMint(maxMint):
                print("No coinbase present")
                return None
            for txn in txn_list[1:]:
                if not txn.validate(unspentOutputs):
                    print("txn invalid")
                    return None
                
        # UPDATE UTXO
        consumed_utxos = []
        new_utxos = []
        for txn in txn_list:
            inputs = txn.getInputs()
            outputs = txn.outputs
            if inputs:
                consumed_utxos += [(input.getPrevTxnHash(), input.getPrevTxnIndex()) for input in inputs]
            if outputs:
                new_utxos += [(txn.getHash(), idx, output) for idx, output in enumerate(outputs)]

        if len(set(consumed_utxos)) != len(consumed_utxos):
            return None

        # Update utxo set
        new_utxo_set = {}
        for entry in new_utxos:
            new_utxo_set[(entry[0], entry[1])] = entry[2]
        for key in unspentOutputs.keys():
            if key not in consumed_utxos:
                new_utxo_set[key] = unspentOutputs[key]

        
        return new_utxo_set  


        

        
        # pass


class Blockchain(object):
    g_utxo_set = {}
    blockchain_dict={}
    blockchain_height={}
    blockchain_work={}
    maxCoinPerBlock = None
    genTarget = None
    genBlock = Block()
    def __init__(self, genesisTarget, maxMintCoinsPerTx):
        """ Initialize a new blockchain and create a genesis block.
            genesisTarget is the difficulty target of the genesis block (that you should create as part of this initialization).
            maxMintCoinsPerTx is a consensus parameter -- don't let any block into the chain that creates more coins than this!
        """
        self.maxCoinPerBlock = maxMintCoinsPerTx
        self.genTarget = genesisTarget

        # setting a 0 txn block
        gen_block = Block()
        gen_block.setContents([])
        # gen_block.setTarget(genesisTarget)
        gen_block.mine(genesisTarget)
        self.genBlock = gen_block
        self.blockchain_dict[self.genBlock.getHash()] = self.genBlock
        self.g_utxo_set[gen_block.getHash()]={}
        self.blockchain_height[gen_block.getHash()] = 0.0
        self.blockchain_work[gen_block.getHash()] = 1.0
        # pass

    def getTip(self):
        """ Return the block at the tip (end) of the blockchain fork that has the largest amount of work"""
        tip_block = None
        tip_block_work = 0
        for key in self.blockchain_dict:
            temp_block = self.blockchain_dict[key]
            if self.blockchain_work[key] > tip_block_work:
                tip_block=temp_block
                tip_block_work=self.blockchain_work[key]
        return tip_block
        # pass

    def getWork(self, target):
        """Get the "work" needed for this target.  Work is the ratio of the genesis target to the passed target"""
        return self.genTarget/target

    def getCumulativeWork(self, blkHash):
        """Return the cumulative work for the block identified by the passed hash.  Return None if the block is not in the blockchain"""
        if blkHash in self.blockchain_work:
            return self.blockchain_work[blkHash]
        else:
            # print("blockhash not found")
            return None

    def getBlocksAtHeight(self, height):
        """Return an array of all blocks in the blockchain at the passed height (including all forks)"""
        height_block=[]
        required_hashes=[]
        for hash in self.blockchain_height:
            if self.blockchain_height[hash] ==height:
                required_hashes.append(hash)
        for blk in self.blockchain_dict:
            if self.blockchain_dict[blk].getHash() in required_hashes:
                height_block.append(self.blockchain_dict[blk])
        return height_block
    
    def extend(self, block):
        """Adds this block into the blockchain in the proper location, if it is valid.  The "proper location" may not be the tip!

           Hint: Note that this means that you must validate transactions for a block that forks off of any position in the blockchain.
           The easiest way to do this is to remember the UTXO set state for every block, not just the tip.
           For space efficiency "real" blockchains only retain a single UTXO state (the tip).  This means that during a blockchain reorganization
           they must travel backwards up the fork to the common block, "undoing" all transaction state changes to the UTXO, and then back down
           the new fork.  For this assignment, don't implement this detail, just retain the UTXO state for every block
           so you can easily "hop" between tips.

           Return false if the block is invalid (breaks any miner constraints), and do not add it to the blockchain."""
        
        # print("view the utxo set")
        cnt=0

        # GET THE PREVIOUS BLOCK
        prev_block_hash = block.getPriorBlockHash()
        # print("previous hash:",prev_block_hash)
        # print("current hash:",block.getHash())
        if not prev_block_hash in self.blockchain_dict:
            # print("prior hash invalid")
            return False 
        
        if prev_block_hash in self.g_utxo_set:
            utxo_prev_block = self.g_utxo_set[prev_block_hash]

            # CHECK IF BLOCK IS VALID
            
            x = block.validate(utxo_prev_block,self.maxCoinPerBlock)
            if x!=None:
                self.g_utxo_set[block.getHash()]=x
                # block.setHeight(prev_block._height +1)
                # block.setWork(prev_block._work + self.getWork(block.getTarget()))
                self.blockchain_dict[block.getHash()] = block
                self.blockchain_height[block.getHash()] = self.blockchain_height[prev_block_hash]+1.0
                self.blockchain_work[block.getHash()] = self.blockchain_work[prev_block_hash]+self.getWork(block.getTarget())
                # print("block added: ",block.getWork(),block.getHeight())
                return True
            return False
        else:
            # print("No such earlier hash exists!")
            return False

        pass

# --------------------------------------------

# Block hash to UTXO dictionary
# but what is UTXO ? What form will it be stored in?
# txhash : txnOutput?



# --------------------------------------------
# You should make a bunch of your own tests before wasting time submitting stuff to gradescope.
# Its a LOT faster to test locally.  Try to write a test for every API and think about weird cases.

# Let me get you started:
def Test():
    # test creating blocks, mining them, and verify that mining with a lower target results in a lower hash
    b1 = Block()
    b1.mine(int("F"*64,16))
    # b1.mine(int("F"*6,16))
    h1 = b1.getHash()
    b2 = Block()
    b2.mine(int("F"*63,16))
    h2 = b2.getHash()
    assert h2 < h1

    t0 = Transaction(None, [Output(lambda x: True, 100)])
    # Negative test: minted too many coins
    assert t0.validateMint(50) == False, "1 output: tx minted too many coins"
    # Positive test: minted the right number of coins
    assert t0.validateMint(50) == False, "1 output: tx minted too many coins"

    class GivesHash:
        def __init__(self, hash):
            self.hash = hash
        def getHash(self):
            return self.hash

    assert HashableMerkleTree([GivesHash(x) for x in [106874969902263813231722716312951672277654786095989753245644957127312510061509]]).calcMerkleRoot().to_bytes(32,"big").hex() == "ec4916dd28fc4c10d78e287ca5d9cc51ee1ae73cbfde08c6b37324cbfaac8bc5"

    assert HashableMerkleTree([
        # this is supposed to be txn list
        GivesHash(x) for x in [
            106874969902263813231722716312951672277654786095989753245644957127312510061509, 
            66221123338548294768926909213040317907064779196821799240800307624498097778386, 
            98188062817386391176748233602659695679763360599522475501622752979264247167302]
            ]
            ).calcMerkleRoot().to_bytes(32,"big").hex() == "ea670d796aa1f950025c4d9e7caf6b92a5c56ebeb37b95b072ca92bc99011c20"

    t0 = Transaction(None, [Output(lambda x: True, 1)])
    
    blkchn = Blockchain(genesisTarget=int("F"*64,16), maxMintCoinsPerTx=2)
    genesisBlock = blkchn.getTip()
    assert blkchn.getCumulativeWork(genesisBlock.getHash()) == 1.0, "basic case work calc failed!"
    assert blkchn.getCumulativeWork(1) == None, "invalid hash finding failed!"
    assert blkchn.getCumulativeWork(0) == None, "invalid hash finding failed!"

    b1 = Block()
    b1.setPriorBlockHash(genesisBlock.getHash())
    b1.mine(int("F"*64,16))
    blkchn.extend(b1)
    b2 = Block()
    b2.setPriorBlockHash(b1.getHash())
    b2.mine(int("F"*63,16))
    blkchn.extend(b2)


    assert blkchn.getCumulativeWork(genesisBlock.getHash()) == 1.0, "Extended block case work calc failed!"
    assert blkchn.getCumulativeWork(b1.getHash()) == 2.0, "intermediate block work calc finding failed! - 1"
    assert blkchn.getCumulativeWork(b2.getHash()) == 18.0, "intermediate block work calc finding failed! - 2"
    assert blkchn.getCumulativeWork(blkchn.getTip().getHash()) == 18, "Basic tip update failed!"



    b_orphan = Block()
    b_orphan.mine(int("F"*64,16))
    blkchn.extend(b_orphan)
    assert b_orphan.getHash() not in blkchn.blockchain_dict, "Adding orphan blocks is possible!"
    assert blkchn.getCumulativeWork(b_orphan.getHash()) == None, "Adding orphan blocks is possible!"

    b3 = Block()
    b3.setPriorBlockHash(genesisBlock.getHash())
    b3.mine(int("F"*63,16))
    blkchn.extend(b3)
    assert blkchn.getTip().getHash() == b2.getHash(), "Alt chain tip update failed! - 1"
    b4 = Block()
    b4.setPriorBlockHash(b3.getHash())
    b4.mine(int("F"*63,16))
    blkchn.extend(b4)
    assert blkchn.getTip().getHash() == b4.getHash(), "Alt chain tip update failed! - 2"
    assert blkchn.getBlocksAtHeight(1) == [b1, b3], "Get Blocks at Height Failed!"

    # print(" ")
    # print("Transaction level tests started")
    # print(" ")

    t0 = Transaction(inputs=None,outputs=[Output(lambda x: x==10,1) ])
    
    t1 = Transaction(inputs=None,outputs=None)
    bt1 = Block()
    bt1.setPriorBlockHash(b4.getHash())
    bt1.setContents([t1])
    # bt1.setContents([t0])
    bt1.mine(int("F"*63,16))
    blkchn.extend(bt1)

    # print("t0 hash: ",t0.getHash())
    # print("t0 ouputs: ",t0.getOutput(0).getValue())
    t3 = Transaction(inputs=[Input(t0.getHash(),0,[10])],outputs=[Output(lambda x: x==15,0.5),Output(lambda x: x==20,0.5)] )
    t2 = Transaction(inputs=None,outputs=[Output(lambda x: x==20,1) ])
    bt2 = Block()
    bt2.setPriorBlockHash(b4.getHash())
    bt2.setContents([t3])
    bt2.mine(int("F"*63,16))
    assert bt1.getHash() == bt2.getHash(),"Can't spend output of other fork"

    emptyblock = Block()
    emptyblock.setPriorBlockHash(bt1.getHash())
    emptyblock.mine(int("F"*63,16))
    assert emptyblock.validate({},1000) != None, "mined but no coinbase txn"



    


    print ("yay local tests passed")
Test()