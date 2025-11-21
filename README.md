# Discord Blocker Bot

A Discord bot that allows users to block other users and prevent unwanted interactions. When a user is blocked, they cannot:
- Tag or mention the blocker
- Reply to the blocker's messages
- React to the blocker's messages
- Use specific keywords that the blocker has set

## Features

- **`/block` command**: Block a user and optionally set keywords they cannot use
- **`/unblock` command**: Remove a block on a user
- **Automatic message deletion**: Violations are automatically deleted
- **Ephemeral notifications**: Blocked users receive hidden notifications
- **Multi-user support**: Multiple users can block multiple people independently
- **Keyword filtering**: Each block can have custom keywords

## Manual Setup Instructions

### Step 1: Create a Discord Application and Bot

1. **Go to Discord Developer Portal**
   - Visit [https://discord.com/developers/applications](https://discord.com/developers/applications)
   - Log in with your Discord account

2. **Create a New Application**
   - Click the "New Application" button
   - Give it a name (e.g., "Blocker Bot")
   - Click "Create"

3. **Add a Bot to Your Application**
   - Go to the "Bot" section in the left sidebar
   - Click "Add Bot" and confirm
   - **IMPORTANT**: Under "Privileged Gateway Intents", enable:
     - ✅ **Message Content Intent** (REQUIRED - allows bot to read message content)
     - ✅ **Server Members Intent** (REQUIRED - allows bot to access member data)
   - Click "Save Changes"

4. **Get Your Bot Token**
   - Still in the "Bot" section, under "Token"
   - Click "Reset Token" and copy the token
   - **SAVE THIS TOKEN** - you'll need it later
   - ⚠️ **NEVER share this token publicly!**

5. **Invite Bot to Your Server**
   - Go to the "OAuth2" → "URL Generator" section
   - Under "Scopes", check:
     - ✅ `bot`
     - ✅ `applications.commands` (for slash commands)
   - Under "Bot Permissions", check:
     - ✅ `Read Messages/View Channels`
     - ✅ `Send Messages`
     - ✅ `Manage Messages` (to delete violating messages)
     - ✅ `Read Message History`
     - ✅ `Add Reactions` (to monitor reactions)
     - ✅ `Use External Emojis` (optional)
   - Copy the generated URL at the bottom
   - Open the URL in your browser and select your server
   - Click "Authorize"

### Step 2: Set Up Railway Account and Project

1. **Create Railway Account**
   - Go to [https://railway.app](https://railway.app)
   - Sign up with GitHub (recommended) or email
   - Verify your email if required

2. **Create a New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo" (recommended) or "Empty Project"
   - If using GitHub, authorize Railway and select your repository

3. **Add PostgreSQL Database**
   - In your Railway project, click "+ New"
   - Select "Database" → "Add PostgreSQL"
   - Wait for the database to provision
   - Click on the PostgreSQL service
   - Go to the "Variables" tab
   - **Copy these values** (you'll need them):
     - `PGHOST` (host)
     - `PGPORT` (port, usually 5432)
     - `PGDATABASE` (database name)
     - `PGUSER` (username)
     - `PGPASSWORD` (password)
   - You can also find these in the "Connect" tab

### Step 3: Deploy Bot to Railway

1. **Push Code to GitHub** (if not already done)
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Discord blocker bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Connect Railway to GitHub**
   - In Railway, click "+ New" → "GitHub Repo"
   - Select your repository
   - Railway will automatically detect it's a Python project

3. **Configure Environment Variables**
   - In your Railway service, go to the "Variables" tab
   - Add the following environment variables:
     ```
     DISCORD_TOKEN=your_bot_token_from_step_1
     DB_NAME=your_database_name_from_postgres
     DB_USER=your_database_user_from_postgres
     DB_PASSWORD=your_database_password_from_postgres
     DB_HOST=your_database_host_from_postgres
     DB_PORT=5432
     ```
   - Click "Add" for each variable
   - **Note**: Railway PostgreSQL provides these as `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`
   - You can either use the `PG*` variables directly or map them:
     ```
     DISCORD_TOKEN=your_bot_token
     DB_NAME=${{Postgres.PGDATABASE}}
     DB_USER=${{Postgres.PGUSER}}
     DB_PASSWORD=${{Postgres.PGPASSWORD}}
     DB_HOST=${{Postgres.PGHOST}}
     DB_PORT=${{Postgres.PGPORT}}
     ```

4. **Deploy**
   - Railway will automatically deploy when you push to GitHub
   - Or click "Deploy" in the Railway dashboard
   - Check the "Deployments" tab for build logs
   - Once deployed, check the "Logs" tab to see if the bot connected successfully

### Step 4: Verify Bot is Working

1. **Check Bot Status**
   - In Discord, go to your server
   - Check the member list - your bot should appear as "Online"
   - If offline, check Railway logs for errors

2. **Test the `/block` Command**
   - Type `/block` in any channel
   - Select a user to block
   - Optionally add keywords (e.g., "spam annoying")
   - The bot should respond with a confirmation

3. **Test Blocking Functionality**
   - Have the blocked user try to:
     - Mention/tag the blocker → Message should be deleted
     - Reply to blocker's message → Message should be deleted
     - React to blocker's message → Reaction should be removed
     - Use blocked keywords → Message should be deleted

## Local Development (Optional)

If you want to test the bot locally before deploying:

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**
   - Copy `.env.example` to `.env`
   - Fill in your Discord token and database credentials

3. **Run the Bot**
   ```bash
   python3 bot.py
   ```

## Troubleshooting

### Bot is Offline
- Check Railway logs for errors
- Verify `DISCORD_TOKEN` is set correctly
- Ensure bot has proper intents enabled in Discord Developer Portal

### Commands Not Appearing
- Wait a few minutes for slash commands to sync
- Try restarting the bot (redeploy on Railway)
- Ensure bot has `applications.commands` scope when invited

### Database Connection Errors
- Verify all database environment variables are set
- Check Railway PostgreSQL service is running
- Ensure database credentials are correct

### Messages Not Being Deleted
- Verify bot has "Manage Messages" permission in your server
- Check bot's role hierarchy (must be above users it's blocking)
- Ensure bot has "Message Content Intent" enabled

### Reactions Not Being Removed
- Verify bot has permission to manage reactions
- Check bot's role position in server settings

## Bot Permissions Summary

The bot needs these permissions:
- **Read Messages/View Channels**: To see messages
- **Send Messages**: To send notifications
- **Manage Messages**: To delete violating messages
- **Read Message History**: To check message content
- **Add Reactions**: To monitor reactions

## Database Schema

The bot uses a PostgreSQL table called `blocks`:
- `blocker_id`: User who created the block
- `blocked_id`: User who is blocked
- `guild_id`: Server where block applies
- `keywords`: Array of blocked keywords
- `created_at`: Timestamp of when block was created

## Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify all environment variables are set correctly
3. Ensure bot has proper permissions in your Discord server
4. Make sure all required intents are enabled in Discord Developer Portal

## License

This project is open source and available for personal use.

