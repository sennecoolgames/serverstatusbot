import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import io
import base64

load_dotenv()
TEST_SERVER_ID = int(os.getenv('TEST_SERVER_ID'))


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="status")
    async def status_command(self, ctx, server_ip: str):
        status = get_status(server_ip)
        embed, file_to_send = format_status_message(server_ip, status, ctx, self.bot)
        print(status)

        if file_to_send:
            await ctx.send(embed=embed, file=file_to_send)
        else:
            await ctx.send(embed=embed)


    @nextcord.slash_command(name="status", description="Replies with the bot's status!", guild_ids=[TEST_SERVER_ID])
    async def status(
        self, 
        interaction: Interaction,
        server_ip: str = nextcord.SlashOption(
            description="The address of the Minecraft server",
            required=True
        )
    ):
        status = get_status(server_ip)
        embed, file_to_send = format_status_message(server_ip, status, interaction, self.bot)
        print(status)

        if file_to_send:
            await interaction.response.send_message(embed=embed, file=file_to_send, ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=False)



def get_status(server_ip):
    status = requests.get("https://api.mcsrvstat.us/3/" + server_ip).json()
    return status

def format_status_message(server_address, status, invoker, bot):
    is_online = status.get("online", False)
    server_ip = server_address
    motd = "\n".join(status.get("motd", {}).get("clean", [])) or "No MOTD"
    players_online = status.get("players", {}).get("online", 0)
    players_max = status.get("players", {}).get("max", 0)
    version = status.get("version", "Unknown")
    favicon_url = status.get("icon", None)

    color_online = 0x55FF55
    color_offline = 0xFF5555
    color = color_online if is_online else color_offline

    title_status = "Online" if is_online else "Offline"
    embed = nextcord.Embed(
        title=f"Minecraft Server — {title_status}",
        description=motd,
        color=color,
        timestamp=datetime.utcnow()
    )

    file_to_send = None
    if favicon_url:
        try:
            if favicon_url.startswith("data:") and "base64," in favicon_url:
                header, b64 = favicon_url.split("base64,", 1)
                data = base64.b64decode(b64)
                fp = io.BytesIO(data)
                fp.seek(0)
                file_to_send = nextcord.File(fp, filename="server_icon.png")
                embed.set_thumbnail(url="attachment://server_icon.png")
            else:
                # normal URL - only set if reasonable length
                if len(favicon_url) <= 2048:
                    embed.set_thumbnail(url=favicon_url)
        except Exception:
            # on any failure, skip thumbnail
            pass

    # Primary info fields
    embed.add_field(name="Address", value=f"`{server_ip}`", inline=True)
    embed.add_field(name="Players", value=f"{players_online}/{players_max}", inline=True)
    embed.add_field(name="Version", value=version, inline=True)

    # Determine user (works for Interaction or Context)
    user_obj = getattr(invoker, "user", None) or getattr(invoker, "author", None)
    user_mention = getattr(user_obj, "mention", str(user_obj) if user_obj else "Unknown")
    user_avatar_url = getattr(getattr(user_obj, "display_avatar", None), "url", None)

    # Visual footer and author
    embed.set_footer(text=f"Requested by {user_mention}", icon_url=user_avatar_url)
    embed.set_author(name=bot.user.name, icon_url=getattr(bot.user.display_avatar, "url", None))
    return embed, file_to_send


def setup(bot):
    bot.add_cog(Status(bot))