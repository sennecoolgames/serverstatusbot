# https://discord.com/oauth2/authorize?client_id=1433438226609344522&permissions=2269403341638720&integration_type=0&scope=bot
# https://discord.com/oauth2/authorize?client_id=1433438226609344522&permissions=8&integration_type=0&scope=bot
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TEST_SERVER_ID = os.getenv('TEST_SERVER_ID')

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    print('Guilds connected to:')
    for guild in bot.guilds:
        print(f'- {guild.id} (name: {guild.name})')

# @bot.slash_command(name="ping", description="Replies with pong!", guild_ids=[testServerID])
# async def ping(interaction: nextcord.Interaction):
#     await interaction.send("Pong!", ephemeral=False)


initial_extensions = []

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        initial_extensions.append(f'cogs.{filename[:-3]}')
print(f'Loaded cogs: {initial_extensions}')

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

bot.run(DISCORD_TOKEN)