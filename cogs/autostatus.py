import nextcord
import requests
import json
import os
import asyncio
from nextcord.ext import commands
from nextcord import Interaction
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID', 0))

# Save config next to this file so restarts still find it
STATUS_FILE = os.path.join(os.path.dirname(__file__), "server_status_config.json")


class AutoStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_config = {}  # keyed by guild id (string)
        self.load_config()

    def load_config(self):
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    self.status_config = json.load(f)
            except Exception as e:
                print("Failed to load autostatus config:", e)
                self.status_config = {}

    def save_config(self):
        try:
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.status_config, f, indent=2)
        except Exception as e:
            print("Failed to save autostatus config:", e)

    async def update_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild_id, cfg in list(self.status_config.items()):
                channel_id = cfg.get("channel_id")
                server_ip = cfg.get("server_ip")
                message_id = cfg.get("message_id")  # optional stored message id
                display_name = cfg.get("name")  # optional display name

                if not channel_id or not server_ip:
                    continue

                # get or fetch channel
                channel = self.bot.get_channel(channel_id)
                if channel is None:
                    try:
                        channel = await self.bot.fetch_channel(channel_id)
                    except Exception:
                        print(f"Could not fetch channel {channel_id} for autostatus (guild {guild_id})")
                        continue

                status = self.get_status(server_ip)
                if not status:
                    continue

                embed = self.create_embed(status, server_ip, display_name)

                # update existing message or send new one and store id
                if message_id:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.edit(embed=embed)
                    except nextcord.NotFound:
                        try:
                            new_msg = await channel.send(embed=embed)
                            cfg["message_id"] = new_msg.id
                            self.save_config()
                        except Exception as e:
                            print("Failed to send autostatus message:", e)
                    except Exception as e:
                        print("Error updating autostatus message:", e)
                else:
                    try:
                        new_msg = await channel.send(embed=embed)
                        cfg["message_id"] = new_msg.id
                        self.save_config()
                    except Exception as e:
                        print("Failed to send autostatus message:", e)

            await asyncio.sleep(300)  # 5 minutes

    def get_status(self, server_ip):
        try:
            resp = requests.get(f"https://api.mcsrvstat.us/3/{server_ip}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Error fetching status for {server_ip}: {e}")
            return None

    def create_embed(self, status, server_ip, display_name=None):
        is_online = status.get("online", False)
        motd = "\n".join(status.get("motd", {}).get("clean", [])) or "No MOTD"
        players_online = status.get("players", {}).get("online", 0)
        players_max = status.get("players", {}).get("max", 0)
        version = status.get("version", "Unknown")
        favicon = status.get("icon", None)

        color_online = 0x55FF55
        color_offline = 0xFF5555
        color = color_online if is_online else color_offline

        title_status = "Online" if is_online else "Offline"
        title_name = display_name if display_name else "Minecraft Server"
        embed = nextcord.Embed(
            title=f"{title_name} — {title_status}",
            description=motd,
            color=color,
        )

        embed.add_field(name="Address", value=f"`{server_ip}`", inline=True)
        embed.add_field(name="Players", value=f"{players_online}/{players_max}", inline=True)
        embed.add_field(name="Version", value=version, inline=True)

        # footer + author using bot info
        embed.set_author(name=self.bot.user.name, icon_url=getattr(self.bot.user.display_avatar, "url", None))
        current_time = int(datetime.utcnow().timestamp())
        embed.set_footer(text=f"Updated <t:{current_time}:R>", icon_url=None)

        # favicon handling: if data URI, skip ; if url and <=2048 set it
        try:
            if favicon and isinstance(favicon, str) and not favicon.startswith("data:") and len(favicon) <= 2048:
                embed.set_thumbnail(url=favicon)
        except Exception:
            pass

        return embed

    @nextcord.slash_command(
        name="autostatus",
        description="Set up auto-updating server status in this channel.",
        guild_ids=None,
        default_member_permissions=nextcord.Permissions(manage_channels=True)
    )
    async def set_autostatus_command(
        self,
        interaction: Interaction,
        name: str = nextcord.SlashOption(
            description="Optional display name for the server (use underscores for spaces)",
            required=True,
            default=None
        ),
        server_ip: str = nextcord.SlashOption(
            description="The address of the Minecraft server (ip[:port])",
            required=True
        )
    ):
        # Add an additional permission check just to be safe
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You need Manage Channels permission to use this command.", ephemeral=True)
            return
            
        """Set the server IP (and optional display name) to auto-update in this channel and create/update the embed immediately."""
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if guild is None:
            await interaction.followup.send("This command must be used in a guild.", ephemeral=True)
            return

        guild_key = str(guild.id)
        channel = interaction.channel
        if channel is None:
            await interaction.followup.send("Could not determine channel.", ephemeral=True)
            return
        channel_id = channel.id

        # normalize name (allow users to pass underscores for spaces)
        display_name = name.replace("_", " ") if isinstance(name, str) and name else None

        # update config and save
        entry = self.status_config.get(guild_key, {})
        entry.update({
            "channel_id": channel_id,
            "server_ip": server_ip,
            "name": display_name
        })
        self.status_config[guild_key] = entry
        self.save_config()

        # attempt to fetch status now and create/update embed/message
        status = self.get_status(server_ip)
        if not status:
            await interaction.followup.send(f"Could not fetch status for `{server_ip}`. Saved config; will retry in background.", ephemeral=True)
            return

        embed = self.create_embed(status, server_ip, display_name)
        message_id = entry.get("message_id")

        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embed=embed)
                await interaction.followup.send(f"Updated existing auto-status for `{server_ip}` in this channel.", ephemeral=True)
                entry["message_id"] = msg.id
                self.save_config()
                return
            except nextcord.NotFound:
                pass
            except Exception as e:
                print("Error editing stored autostatus message:", e)

        # send a new message and store id
        try:
            new_msg = await channel.send(embed=embed)
            entry["message_id"] = new_msg.id
            self.status_config[guild_key] = entry
            self.save_config()
            await interaction.followup.send(f"Auto status set for server `{server_ip}` in this channel.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to create autostatus message: {e}", ephemeral=True)


def setup(bot):
    instance = AutoStatus(bot)
    bot.add_cog(instance)
    # schedule the update loop for the same instance
    bot.loop.create_task(instance.update_status())