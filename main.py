import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from API_JBChangeLogs import github_sync as api_github_sync
from stockage_system import setup_stockage_system
from github_sync import GitHubSync
from trading_ticket_system import setup_trading_ticket_system

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('TOKEN_DISCORD')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} connected to Discord!')
    
    # Configurer le système de stockage
    stockage_system = setup_stockage_system(bot)
    print("Stockage System loaded!")
    
    # Configurer le système de tickets de trading
    trading_ticket_system = setup_trading_ticket_system(bot)
    print("Trading Ticket System loaded!")
    
    # Démarrer la synchronisation GitHub
    asyncio.create_task(api_github_sync.start_monitoring())

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    file_sync = GitHubSync()
    await file_sync.sync_all_files_to_github()
    
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: TOKEN_DISCORD not found in environment variables")