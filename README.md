# track-burn-bot

This bot is designed to detect burn transactions in a blockchain and post information about those transactions to a Discord channel.

## Prerequisites

You need Python 3.6 or later to run this bot. You can verify your Python version by running python --version in your command prompt.

You also need the following Python packages which can be installed via pip:

    discord.py
    aiohttp

Install them using this command:

```pip install -r requirements.txt```

## Configuration

Replace RPC_USER and RPC_PASSWORD with your rpcuser and rpcpassword from your local daemon conf file.

Replace `'your-bot-token'` in `bot.run('your-bot-token')` with the token of your Discord bot. The token can be obtained from the Discord Developer Portal.

Ensure you replace the 15 second interval to your desired interval on line 11.

This bot uses getinfo to retrieve blockchain info, if your blockchain uses a newer BTC Core and require the `getblockchaininfo` command be sure to simply replace `getinfo` with `getblockchaininfo` (Or which ever command grabs the blockchain info with the `blocks` data).

Dont forget to replace the Innova RPC port of 14531 with the RPC port of the blockchain you are trying to monitor.

Also, ensure that you change the channel name from "burn-transactins" to the channel you want the bot to post to.

## Running the Bot

To start the bot, navigate to the directory containing bot.py in your command prompt and run:

```python burnbot.py```

The bot will start and attempt to connect to Discord. Once connected, it will print a message in the command prompt containing its username.

## Usage

Once the blockchain is synced you may start the bot, it will automatically start checking for burn transactions in the blockchain every 15 seconds (Or whatever you changed it to). When it detects a burn transaction, it will send a message to the discord channel in your Discord server that you designated, with information about the block number, block hash, transaction ID, burned coins in current transaction ID, and the total burned coins.