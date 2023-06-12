from innovarpc.authproxy import AuthServiceProxy
import sqlite3
from discord.ext import commands, tasks
import discord
import json
import os

rpc_user = 'RPC_USER' #change with your rpcuser
rpc_password = 'RPC_PASSWORD' #change with your rpcpassword
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:14531")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# initialize total burned coins
global_total_burned_coins = 0
# initialize last processed block
last_processed_block = -1 # set to desired start block

def get_last_processed_block_from_db():
    conn = sqlite3.connect('burnbot.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS burnbot (last_processed_block INT, total_burned_coins REAL)")
    c.execute("SELECT last_processed_block FROM burnbot")
    result = c.fetchone()
    conn.close()
    if result is None:
        return -1
    return result[0]

def get_total_burned_coins_from_db():
    conn = sqlite3.connect('burnbot.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS burnbot (last_processed_block INT, total_burned_coins REAL)")
    c.execute("SELECT total_burned_coins FROM burnbot")
    result = c.fetchone()
    conn.close()
    if result is None:
        return 0.0
    return result[0]

def update_last_processed_block_in_db(block_num):
    conn = sqlite3.connect('burnbot.db')
    c = conn.cursor()
    c.execute("UPDATE burnbot SET last_processed_block = ?", (block_num,))
    conn.commit()
    conn.close()

def update_total_burned_coins_in_db(total_burned):
    conn = sqlite3.connect('burnbot.db')
    c = conn.cursor()
    c.execute("UPDATE burnbot SET total_burned_coins = ?", (total_burned,))
    conn.commit()
    conn.close()

# read last processed block and total burned coins from DB
last_processed_block = get_last_processed_block_from_db()
global_total_burned_coins = get_total_burned_coins_from_db()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord Server!') # Debug line
    await calculate_total_burned_coins()
    burn_check.start()

@tasks.loop(seconds=15)  # desired interval
async def burn_check():
    global global_total_burned_coins, last_processed_block

    # fetch the latest block
    latest_block = rpc_connection.getblockcount()

    # check if the latest block is the same as the last processed block
    if latest_block == last_processed_block:
        # if it is, no need to process it again
        return

    print(f'Checking block {latest_block}')  # Debug line

    # get the block hash
    block_hash = rpc_connection.getblockhash(latest_block)
    print(f'Block hash: {block_hash}')  # Debug line

    # Burned coins in the current block
    total_burned_coins_this_block = 0
    burn_txid_this_block = None

    # get the block
    block = rpc_connection.getblock(block_hash)

    # prepare a list of commands to get transaction details for each transaction in the block
    commands = [['getrawtransaction', txid, 1] for txid in block['tx']]

    # send batch command to get all transaction details
    transactions = rpc_connection.batch_(commands)

    # iterate through each transaction in the block
    for tx in transactions:
        if tx is None:
            print(f'Failed to get raw transaction {txid}.')  # Debug line
            continue  # Skip this transaction and move to the next one

        # check each output script for the OP_RETURN opcode
        for vout in tx['vout']:
            if vout['scriptPubKey']['asm'].startswith('OP_RETURN'):
                # add the value of this output to the total burned coins
                total_burned_coins_this_block += vout['value']
                burn_txid_this_block = txid

    if total_burned_coins_this_block > 0:
        global_total_burned_coins += total_burned_coins_this_block
        update_total_burned_coins_in_db(global_total_burned_coins)
        print(f'Detected burn transaction {burn_txid_this_block} in block {latest_block} with {total_burned_coins_this_block} burned coins')  # Debug line
        # send a message if there were any burned coins in this transaction
        channel = bot.get_channel(CHANNEL_ID)  # change with desired CHANNEL_ID
        if channel is None:
            print('No channel found with specified ID')  # Debug line
        else:
            print(f'Sending message to channel {channel.id}')  # Debug line
            await channel.send(f'Burn transaction detected!\n'
                               f'Block number: {latest_block}\n'
                               f'Block hash: {block_hash}\n'
                               f'Transaction ID: {burn_txid_this_block}\n'
                               f'Burned coins in this block: {total_burned_coins_this_block}\n'
                               f'Total burned coins: {global_total_burned_coins}')

    # update last processed block
    last_processed_block = latest_block
    update_last_processed_block_in_db(last_processed_block)

async def calculate_total_burned_coins():
    global global_total_burned_coins, last_processed_block

    # fetch the latest block
    latest_block = rpc_connection.getblockcount()

    # we will start from the last processed block + 1 and iterate up to the latest block
    # prepare a list of commands to get block hash for each block
    commands = [['getblockhash', height] for height in range(last_processed_block + 1, latest_block + 1)]

    # send batch command to get all block hashes
    block_hashes = rpc_connection.batch_(commands)

    # prepare a list of commands to get block details for each block
    commands = [['getblock', block_hash] for block_hash in block_hashes]

    # send batch command to get all block details
    blocks = rpc_connection.batch_(commands)

    # iterate through each block
    for i, block in enumerate(blocks):
        # iterate through each transaction in the block
        for txid in block['tx']:
            # get transaction details
            tx = rpc_connection.getrawtransaction(txid, 1)

            # check each output script for the OP_RETURN opcode
            for vout in tx['vout']:
                if vout['scriptPubKey']['asm'].startswith('OP_RETURN'):
                    # add the value of this output to the total burned coins
                    global_total_burned_coins += vout['value']
                    update_total_burned_coins_in_db(global_total_burned_coins)

                    # print out the sync progress and total burned coins so far
                    print(f'Sync progress: Block {i+last_processed_block+1}/{latest_block} checked. Total burned coins so far: {global_total_burned_coins}') # Debug line

        # update last processed block
        last_processed_block = i+last_processed_block+1
        update_last_processed_block_in_db(last_processed_block)

# replace with your actual bot token
bot.run('your-bot-token')
