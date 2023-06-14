from discord.ext import commands, tasks
from aiohttp import BasicAuth
import sqlite3
import logging
import discord
import aiohttp
import json
import os

rpc_user = 'RPC_USER' #change with your rpcuser
rpc_password = 'RPC_PASSWORD' #change with your rpcpassword
auth = BasicAuth(rpc_user, rpc_password)

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# initialize total burned coins
global_total_burned_coins = 0 # do not change from 0, allow sync from block 0 (or burn start block) to track all burned coins
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
    #logger.info('%s has connected to Discord Server!', bot.user) # Logger
    await calculate_total_burned_coins()
    burn_check.start()

@tasks.loop(seconds=15)  # desired interval
async def burn_check():
    global global_total_burned_coins, last_processed_block

    # Initialize current_block
    current_block = last_processed_block

    async with aiohttp.ClientSession(auth=auth) as session:
        try:
            # fetch the latest block
            async with session.post('http://localhost:14531', json={'method': 'getinfo'}) as response:
                response_json = await response.json()
                latest_block = response_json['result']['blocks']

            # iterate through each unprocessed block
            for current_block in range(last_processed_block + 1, latest_block + 1):
                print(f'Checking block {current_block}')  # Debug line

                async with session.post('http://localhost:14531', json={'method': 'getblockhash', 'params': [current_block]}) as response:
                    response_json = await response.json()
                    block_hash = response_json['result']
                    print(f'Block hash: {block_hash}')  # Debug line

                # Burned coins in the current block
                total_burned_coins_this_block = 0
                burn_txid_this_block = None

                async with session.post('http://localhost:14531', json={'method': 'getblock', 'params': [block_hash]}) as response:
                    response_json = await response.json()
                    block = response_json['result']

                # iterate through each transaction in the block
                for txid in block['tx']:
                    async with session.post('http://localhost:14531', json={'method': 'getrawtransaction', 'params': [txid, 1]}) as response:
                        response_json = await response.json()
                        print(f'Response JSON for raw transaction: {response_json}')  # Debug line
                        tx = response_json['result']
                    if tx is None:
                        print(f'Failed to get raw transaction {txid}.') # Debug line
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
                    channel_1 = bot.get_channel(CHANNEL_ID_1) # replace with your first CHANNEL_ID
                    channel_2 = bot.get_channel(CHANNEL_ID_2) # replace with your second CHANNEL_ID (For telegram-bridge) Comment this line out if you want only one channel

                    if channel_1 is None:
                        print('No channel found with specified ID for channel 1')  # Debug line
                    else:
                        print(f'Sending message to channel {channel_1.id}')  # Debug line

                        # Step 1: Catch exceptions during message preparation and sending
                        try:
                            # Step 2: Validate the embed format. Convert the values to string before passing to the add_field method.
                            embed=discord.Embed(title="Burn transaction detected!", color=0x01619c)
                            embed.add_field(name="Block number", value=str(latest_block), inline=False)
                            embed.add_field(name="Block hash", value=str(block_hash), inline=False)
                            embed.add_field(name="Transaction ID", value=str(burn_txid_this_block), inline=False)
                            embed.add_field(name="Burned coins in this block", value=str(total_burned_coins_this_block), inline=False)
                            embed.add_field(name="Total burned coins", value=str(global_total_burned_coins), inline=False)
                            await channel_1.send(embed=embed)
                        except Exception as e:
                            print(f'Exception occurred while creating/sending the embed: {e}') # Debug line
        
                    if channel_2 is None: # Comment out starting here if you want only one channel
                        print('No channel found with specified ID for channel 2')  # Debug line
                    else:
                        print(f'Sending message to channel {channel_2.id}')  # Debug line
                        await channel_2.send(f'Burn transaction detected!\n'
                                        f'Block number: {latest_block}\n'
                                        f'Block hash: {block_hash}\n'
                                        f'Transaction ID: {burn_txid_this_block}\n'
                                        f'Burned coins in this block: {total_burned_coins_this_block}\n'
                                        f'Total burned coins: {global_total_burned_coins}') # Comment out ending here if you want only one channel

            # update last processed block
            last_processed_block = current_block
            update_last_processed_block_in_db(last_processed_block)

        # Debug 
        except Exception as e:
            print(f'Response status: {response.status}')
            print(f'Response text: {await response.text()}')
            print(f'Exception occurred while processing blocks: {e}')  # Debug line

async def calculate_total_burned_coins():
    global global_total_burned_coins, last_processed_block

    # Initialize current_block
    current_block = last_processed_block

    async with aiohttp.ClientSession(auth=auth) as session:
        # fetch the latest block
        async with session.post('http://localhost:14531', json={'method': 'getinfo'}) as response:
            response_json = await response.json()
            latest_block = response_json['result']['blocks']

        # we will start from the last processed block + 1 and iterate up to the latest block
        for current_block in range(last_processed_block + 1, latest_block + 1):
            print(f'Checking block {current_block}')  # Debug line

            async with session.post('http://localhost:14531', json={'method': 'getblockhash', 'params': [current_block]}) as response:
                response_json = await response.json()
                block_hash = response_json['result']
                print(f'Block hash: {block_hash}')  # Debug line

            async with session.post('http://localhost:14531', json={'method': 'getblock', 'params': [block_hash]}) as response:
                response_json = await response.json()
                block = response_json['result']

            # iterate through each transaction in the block
            for txid in block['tx']:
                async with session.post('http://localhost:14531', json={'method': 'getrawtransaction', 'params': [txid, 1]}) as response:
                    response_json = await response.json()
                    #print(f'Response JSON for raw transaction: {response_json}')  # Debug line
                    #logger.info('Response JSON for raw transaction: %s', response_json) # Logger
                    tx = response_json['result']
                    if tx is None:
                        #print(f'Failed to get raw transaction {txid}') # Debug line
                        #logger.info('Failed to get raw transaction %s.', txid) # Logger
                        continue  # skip this transaction and move to the next one

                # check each output script for the OP_RETURN opcode
                for vout in tx['vout']:
                    if vout['scriptPubKey']['asm'].startswith('OP_RETURN'):
                        # add the value of this output to the total burned coins
                        global_total_burned_coins += vout['value']
                        update_total_burned_coins_in_db(global_total_burned_coins)

                        # print out the sync progress and total burned coins so far
                        print(f'Sync progress: Block {current_block}/{latest_block} checked. Total burned coins so far: {global_total_burned_coins}') # Debug line

            # update last processed block
            last_processed_block = current_block
            update_last_processed_block_in_db(last_processed_block)

# replace with your actual bot token
bot.run('your-bot-token')
