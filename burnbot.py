from discord.ext import commands, tasks
import discord
import aiohttp
import json

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# initialize total burned coins
global_total_burned_coins = 0

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    burn_check.start()

@tasks.loop(seconds=15)  # desired interval
async def burn_check():
    global global_total_burned_coins

    async with aiohttp.ClientSession() as session:
        try:
            # fetch the latest block
            async with session.post('http://localhost:14531', json={'method': 'getinfo'}) as response:
                response_json = await response.json()
                latest_block = response_json['result']['blocks']
            
            async with session.post('http://localhost:14531', json={'method': 'getblockhash', 'params': [latest_block]}) as response:
                response_json = await response.json()
                block_hash = response_json['result']
            
            async with session.post('http://localhost:14531', json={'method': 'getblock', 'params': [block_hash]}) as response:
                response_json = await response.json()
                block = response_json['result']

            # iterate through each transaction in the block
            for txid in block['tx']:
                async with session.post('http://localhost:14531', json={'method': 'getrawtransaction', 'params': [txid, 1]}) as response:
                    response_json = await response.json()
                    tx = response_json['result']
                # initialize total burned coins for this transaction
                total_burned_coins_this_tx = 0
                # check each output script for the OP_RETURN opcode
                for vout in tx['vout']:
                    if vout['scriptPubKey']['asm'].startswith('OP_RETURN'):
                        # add the value of this output to the total burned coins
                        total_burned_coins_this_tx += vout['value']
                if total_burned_coins_this_tx > 0:
                    global_total_burned_coins += total_burned_coins_this_tx
                    # send a message if there were any burned coins in this transaction
                    channel = discord.utils.get(bot.get_all_channels(), name='burn-transactions')
                    await channel.send(f'Burn transaction detected!\n'
                                        f'Block number: {latest_block}\n'
                                        f'Block hash: {block_hash}\n'
                                        f'Transaction ID: {txid}\n'
                                        f'Burned coins in this TX: {total_burned_coins_this_tx}\n'
                                        f'Total burned coins: {global_total_burned_coins}')
        # temp
        except Exception as e:
            print(f'Response status: {response.status}')
            print(f'Response text: {await response.text()}')
            print(f'Error: {e}')

# replace with your actual bot token
bot.run('your-bot-token')
