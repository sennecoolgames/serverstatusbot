import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from mcstatus import JavaServer
import base64
import io

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID', 0))
STATUS_FILE = os.path.join(os.path.dirname(__file__), "server_status_config.json")

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # def get_status(self, server_ip):
    #     """Fetch server status from API"""
    #     try:
    #         resp = requests.get(f"https://api.mcsrvstat.us/3/{server_ip}", timeout=10)
    #         resp.raise_for_status()
    #         return resp.json()
    #     except Exception as e:
    #         print(f"Error fetching status for {server_ip}: {e}")
    #         return None
        
    def get_status(self, server_ip):
        """Fetch server status localy using mcstatus"""
        try:
            server = JavaServer.lookup(server_ip)
            status = server.status()
            return status
        except Exception as e:
            print(f"Error fetching status for {server_ip}: {e}")
            return None

    def create_embed(self, status, server_ip, display_name=None):
        """Create status embed"""
        is_online = status is not None
        title_name = display_name or "Minecraft Server"
        
        embed = nextcord.Embed(
            title=f"{title_name} — {'Online' if is_online else 'Offline'}",
            description="".join(status.motd.to_plain() or "No MOTD"),
            color=0x55FF55 if is_online else 0xFF5555,
            timestamp=datetime.now(timezone.utc)
        )

        # Add fields
        embed.add_field(name="Address", value=f"`{server_ip}`", inline=True)
        embed.add_field(
            name="Players", 
            value=f"{status.players.online}/{status.players.max if is_online else 0}", 
            inline=True
        )
        version = status.version.name if is_online else "Unknown"
        if any(x in version.lower() for x in ["velocity", "bungeecord"]):
            version = version.split(" ")[1]
        embed.add_field(name="Version", value=str(version), inline=True)

        # Set author and footer
        embed.set_author(name=self.bot.user.name, icon_url=getattr(self.bot.user.display_avatar, "url", None))
        # embed.set_footer(text="Last Updated")

        # Set thumbnail if valid
        try:
            favicon = None
            if hasattr(status, 'raw') and status.raw:
                favicon = status.raw.get('favicon')
            if not favicon and hasattr(status, 'icon'):
                favicon = status.icon
                
            if favicon and isinstance(favicon, str):
                if favicon.startswith("data:image"):
                    try:
                        header, b64data = favicon.split(',', 1)
                        image_data = base64.b64decode(b64data)
                        
                        fp = io.BytesIO(image_data)
                        file = nextcord.File(fp, filename="server_icon.png")
                        
                        embed.set_thumbnail(url="attachment://server_icon.png")
                        return embed, file
                    except Exception as e:
                        print(f"Failed to decode base64 favicon: {e}")
                elif len(favicon) <= 2048:
                    # Handle normal URL
                    embed.set_thumbnail(url=favicon)
                    
        except Exception as e:
            print(f"Failed to set favicon: {e}")

        return embed, None  # Return None as file if no favicon


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

        embed, file = self.create_embed(status, server_ip, name)
        if file:
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    cog = Status(bot)
    bot.add_cog(cog)