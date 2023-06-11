import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('burnbot.db')

# Create a cursor object
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS burnbot
             (last_processed_block INTEGER)''')

# Insert a row of data with the block number -1 (indicating that no blocks have been processed yet) and 0.0 coins (indicating that no coins have been burned yet)
c.execute("INSERT INTO burnbot (last_processed_block, total_burned_coins) VALUES (?, ?)", (-1, 0.0))

# Save (commit) the changes
conn.commit()

# Close the connection
conn.close()
