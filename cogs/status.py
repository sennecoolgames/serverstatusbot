import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID', 0))
STATUS_FILE = os.path.join(os.path.dirname(__file__), "server_status_config.json")

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_status(self, server_ip):
        """Fetch server status from API"""
        try:
            resp = requests.get(f"https://api.mcsrvstat.us/3/{server_ip}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error fetching status for {server_ip}: {e}")
            return None

    def create_embed(self, status, server_ip, display_name=None):
        """Create status embed"""
        is_online = status.get("online", False)
        title_name = display_name or "Minecraft Server"
        
        embed = nextcord.Embed(
            title=f"{title_name} — {'Online' if is_online else 'Offline'}",
            description="\n".join(status.get("motd", {}).get("clean", [])) or "No MOTD",
            color=0x55FF55 if is_online else 0xFF5555,
            timestamp=datetime.now(timezone.utc)
        )

        # Add fields
        embed.add_field(name="Address", value=f"`{server_ip}`", inline=True)
        embed.add_field(
            name="Players", 
            value=f"{status.get('players', {}).get('online', 0)}/{status.get('players', {}).get('max', 0)}", 
            inline=True
        )
        embed.add_field(name="Version", value=status.get("version", "Unknown"), inline=True)

        # Set author and footer
        embed.set_author(name=self.bot.user.name, icon_url=getattr(self.bot.user.display_avatar, "url", None))
        embed.set_footer(text="Last Updated")

        # Set thumbnail if valid
        favicon = status.get("icon")
        if favicon and isinstance(favicon, str) and not favicon.startswith("data:") and len(favicon) <= 2048:
            embed.set_thumbnail(url=favicon)

        return embed


    @nextcord.slash_command(
        name="status",
        description="Check the status of a minecraft server",
        # default_member_permissions=nextcord.Permissions(manage_channels=True)
    )
    async def status(
        self,
        interaction: Interaction,
        server_ip: str = nextcord.SlashOption(description="Server IP address (and port)", required=True),
        name: str = nextcord.SlashOption(description="Display name for the server", required=False)
    ):
        # if not interaction.guild or not interaction.channel:
        #     await interaction.response.send_message("This command must be used in a server channel", ephemeral=True)
        #     return

        await interaction.response.defer(ephemeral=True)

        # Create initial status message
        status = self.get_status(server_ip)
        if not status:
            await interaction.followup.send("Could not fetch server status. Will retry later.", ephemeral=True)
            return

        embed = self.create_embed(status, server_ip, name)
        await interaction.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    cog = Status(bot)
    bot.add_cog(cog)