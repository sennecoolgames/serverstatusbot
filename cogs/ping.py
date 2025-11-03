import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from dotenv import load_dotenv
import os

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID'))


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_command(self, ctx):
        await ctx.send(f"Pong! {ctx.author.mention}")

    @nextcord.slash_command(name="ping", description="Replies with a ping!", guild_ids=None)
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message(f"Pong! {interaction.user.mention}", ephemeral=True)


def setup(bot):
    bot.add_cog(Ping(bot))