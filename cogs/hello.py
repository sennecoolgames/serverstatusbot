import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from dotenv import load_dotenv
import os

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID'))


class Hello(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello")
    async def hello_command(self, ctx):
        await ctx.send(f"Hello, {ctx.author.mention}!")

    @nextcord.slash_command(name="hello", description="Replies with a greeting!", guild_ids=None)
    async def hello(self, interaction: Interaction):
        await interaction.response.send_message(f"Hello, {interaction.user.mention}!", ephemeral=False)


def setup(bot):
    bot.add_cog(Hello(bot))