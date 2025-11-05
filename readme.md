# ServerStatusBot

Simple Discord bot that posts and auto-updates Minecraft Java server (in the future maybe other games) status embeds. Uses `mcstatus` to query servers and stores autostatus configuration (channel, server IP, display name, message id) in a JSON file so updates survive restarts.

## Public Bot
This bot was made for [GreatNet Hosting](https://greatnethosting.com/) and they are hosting a public instance of this bot.
You can invite it to your server with [this link](https://discord.com/oauth2/authorize?client_id=1433438226609344522&permissions=2269403341638720&integration_type=0&scope=bot).
### Support
GreatNet Hosting was kind enough to provide this bot publically. Consider supporting the project by using their services and code **SSB25** for **30%** off your first month of bot hosting or a game server!
[![Gratnet Hosting](https://greatnethosting.com/assets/img/logo.png)](https://greatnethosting.com/)



## Features
- `/status <ip> [name]` — show a one-time server status embed (supports base64 favicons).
- `/autostatus <name> <ip>` — create an auto-updating status message in the current channel (requires Manage Channels).
- Periodic updates every 5 minutes. Config persisted to `server_status_config.json`.


# Self Hosting

## Requirements
- Python 3.10+
- See `requirements.txt`:
    - nextcord 3.1.1
    - python-dotenv 1.1.1
    - mcstatus 12.0.6
    - PyYAML 6.0.3


## Setup
1. **Clone the repository:**

    ```bash
    git clone https://github.com/sennecoolgames/serverstatusbot.git
    cd serverstatusbot
    ```
2. **Install the requirements**
    ```bash
    pip install -r requirements.txt
    ``` 
3. **Copy `.env.example` to `.env` and set:**
    ```bash
    cp .env.example .env
    ```
    - `DISCORD_TOKEN` — your bot token (create one [here](https://discord.com/developers/applications))
    - `TEST_SERVER_ID` — (optional) a guild ID used during development to register slash commands to a single server. Only needed for local testing; remove or leave empty for global commands.
4. **Run the bot:**
    ```powershell
    # Windows
    & C:/Python312/python.exe main.py
    ```
    ```bash
    # Linux
    & python3 main.py
    ```

## Usage
- Invite the bot to your server with appropriate permissions (Send Messages, Embed Links, Manage Messages if you want to allow message deletion).
- Use `/status <server_ip> [name]` to check status immediately.
- Use `/autostatus <name> <server_ip>` in a channel where you want the auto-updating embed. You must have Manage Channels permission to use the command.
- The bot will create a message and update it every 5 minutes.

## Notes & Troubleshooting

- If you see errors about editing messages authored by another user, ensure the saved `message_id` in `server_status_config.json` belongs to a message the bot created. Delete that entry to recreate the message.
- `TEST_SERVER_ID` is only for development (registers new slash commands to a single guild). Leave blank or remove for production/global commands.

## Files of interest
- `main.py` — bot entrypoint (loads cogs).
- `server_status_config.json` — stored autostatus configs (channel, ip, name, message_id).
- `config.yml` — additional configs like keywords to filter from version strings.
- `cogs/status.py` — manual status command, embed formatting.
- `cogs/autostatus.py` — auto-updating cog, persistence and background task.

If you want adjustments to embed styling, update `create_embed` in `cogs/status.py` and `cogs/autostatus.py`.