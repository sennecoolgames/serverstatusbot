import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import requests
import json
import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID', 0))
STATUS_FILE = os.path.join(os.path.dirname(__file__), "server_status_config.json")

class AutoStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_config = self.load_config()

    def load_config(self):
        """Load status config from file"""
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load config: {e}")
        return {}

    def save_config(self):
        """Save current config to file"""
        try:
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.status_config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    async def update_message(self, channel, message_id, embed):
        """Update or send status message"""
        try:
            if message_id:
                try:
                    msg = await channel.fetch_message(message_id)
                    await msg.edit(embed=embed)
                    return message_id
                except nextcord.NotFound:
                    pass
            
            new_msg = await channel.send(embed=embed)
            return new_msg.id
        except Exception as e:
            print(f"Failed to update/send message: {e}")
            return None

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

    async def update_status(self):
        """Background task to update all status messages"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild_id, cfg in list(self.status_config.items()):
                channel = self.bot.get_channel(cfg.get("channel_id"))
                if not channel:
                    continue

                status = self.get_status(cfg.get("server_ip"))
                if status:
                    embed = self.create_embed(status, cfg.get("server_ip"), cfg.get("name"))
                    new_id = await self.update_message(channel, cfg.get("message_id"), embed)
                    
                    if new_id and new_id != cfg.get("message_id"):
                        cfg["message_id"] = new_id
                        self.save_config()

            await asyncio.sleep(300)  # 5 minutes

    @nextcord.slash_command(
        name="autostatus",
        description="Set up auto-updating server status in this channel",
        default_member_permissions=nextcord.Permissions(manage_channels=True)
    )
    async def set_autostatus(
        self,
        interaction: Interaction,
        name: str = nextcord.SlashOption(description="Display name for the server", required=True),
        server_ip: str = nextcord.SlashOption(description="Server IP address (and port)", required=True)
    ):
        if not interaction.guild or not interaction.channel:
            await interaction.response.send_message("This command must be used in a server channel", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        # Update config
        guild_key = str(interaction.guild.id)
        self.status_config[guild_key] = {
            "channel_id": interaction.channel.id,
            "server_ip": server_ip,
            "name": name.replace("_", " ")
        }
        self.save_config()

        # Create initial status message
        status = self.get_status(server_ip)
        if not status:
            await interaction.followup.send("Could not fetch server status. Will retry later.", ephemeral=True)
            return

        embed = self.create_embed(status, server_ip, name)
        msg_id = await self.update_message(interaction.channel, None, embed)
        
        if msg_id:
            self.status_config[guild_key]["message_id"] = msg_id
            self.save_config()
            await interaction.followup.send("Auto-status message created successfully!", ephemeral=True)
        else:
            await interaction.followup.send("Failed to create status message", ephemeral=True)

def setup(bot):
    cog = AutoStatus(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog.update_status())