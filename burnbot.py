from discord.ext import commands, tasks
import discord

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    burn_check.start()

@tasks.loop(seconds=15)  # desired interval
async def burn_check():
    try:
        # fetch the latest block
        latest_block = request('http://localhost:14531', 'getinfo')['blocks']
        block_hash = request('http://localhost:14531', 'getblockhash', latest_block)
        block = request('http://localhost:14531', 'getblock', block_hash)

        # iterate through each transaction in the block
        for txid in block['tx']:
            tx = request('http://localhost:14531', 'getrawtransaction', txid, 1)
            # initialize total burned coins for this transaction
            total_burned_coins = 0
            # check each output script for the OP_RETURN opcode
            for vout in tx['vout']:
                if vout['scriptPubKey']['asm'].startswith('OP_RETURN'):
                    # add the value of this output to the total burned coins
                    total_burned_coins += vout['value']
            if total_burned_coins > 0:
                # send a message if there were any burned coins in this transaction
                channel = discord.utils.get(bot.get_all_channels(), name='burn-transactions')
                await channel.send(f'Burn transaction detected!\n'
                                   f'Block number: {latest_block}\n'
                                   f'Block hash: {block_hash}\n'
                                   f'Transaction ID: {txid}\n'
                                   f'Total burned coins: {total_burned_coins}')

    except Exception as e:
        print(f'Error: {e}')

# replace with your actual bot token
bot.run('your-bot-token')
