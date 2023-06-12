# track-burn-bot

The `track-burn-bot` is a Python-based Discord bot designed to monitor and report burn transactions in a given blockchain. It provides the block number, block hash, transaction ID, the number of burned coins in the transaction, and the total number of burned coins in a given blockchain using a message to a specified Discord channel.

## Prerequisites

1. Python 3.6 or later: You can verify your Python version by running `python --version` in your command prompt.
2. SQLite3: This is included in the Python standard library for Python versions 2.5 and later.
3. Python packages:
   * discord.py
   * aiohttp

These can be installed via pip using the requirements file:

```bash
pip install -r requirements.txt
```

## Configuration

### SQLite Database

The bot requires a SQLite database to persist the state of the last processed block and the total burned coins. The database file is called `burnbot.db` and it is created automatically when the bot starts if it does not already exist. It contains a single table, `burnbot`, with the fields `last_processed_block` (integer) and `total_burned_coins` (real).

### RPC Configuration

The bot requires connection to a local daemon running the target blockchain. Specify the `rpcuser` and `rpcpassword` from your local daemon's configuration file in `burnbot.py`:

```python
rpc_user = 'RPC_USER'  # Replace with your rpcuser
rpc_password = 'RPC_PASSWORD'  # Replace with your rpcpassword
```

### Discord Bot Token

Obtain the token of your Discord bot from the [Discord Developer Portal](https://discord.com/developers/applications) and specify it in `burnbot.py`:

```python
bot.run('your-bot-token')  # Replace with your Discord bot token
```

### Update Interval

The bot checks for burn transactions at a set interval. This can be adjusted on line 61 of `burnbot.py`:

```python
@tasks.loop(seconds=15)  # Adjust the interval as desired
```

### Blockchain Information Method

Depending on the version of Bitcoin Core used by the target blockchain, the method to retrieve blockchain information may vary. For newer versions, replace `'getinfo'` with `'getblockchaininfo'` or the appropriate command for your blockchain:

```python
async with session.post('http://localhost:14531', json={'method': 'getinfo'}) as response:  # Change 'getinfo' as necessary
```

### RPC Port

Ensure that the RPC port matches the one used by your target blockchain. The default port is 14531 for Innova:

```python
async with session.post('http://localhost:14531', json={'method': 'getinfo'}) as response:  # Change port number as necessary
```

### Discord Channel ID

Specify the ID of the Discord channel where the bot will post updates:

```python
channel = bot.get_channel(CHANNEL_ID)  # Replace CHANNEL_ID with your actual Discord channel ID
```

## Running the Bot

To start the bot, navigate to the directory containing `burnbot.py` in your terminal and run:

```bash
python burnbot.py
```

The bot will attempt to connect to Discord. Upon successful connection, it will print a message in the terminal with its username.

## Usage

Once your blockchain is synced, start the bot. It will automatically begin checking for burn transactions from the last processed block, if it's the first run, it will start from block 0. Once it reaches the most recent block it will start an automated check based on the interval you specified. When it detects a burn transaction, it will send a message to the designated Discord channel with the block number, block hash, transaction ID, number of burned coins in the transaction, and the total number of burned coins in the chain so far.

If you encounter any issues, check the terminal for any error messages or debugging information.
