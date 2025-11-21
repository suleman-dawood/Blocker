# Quick Setup Guide

## Discord Bot Setup (5 minutes)

1. **Create Bot Application**
   - Go to https://discord.com/developers/applications
   - Click "New Application" → Name it → Create
   - Go to "Bot" section → "Add Bot"
   - **CRITICAL**: Enable these intents:
     - ✅ Message Content Intent
     - ✅ Server Members Intent
   - Copy the bot token (save it!)

2. **Invite Bot to Server**
   - Go to "OAuth2" → "URL Generator"
   - Scopes: `bot` + `applications.commands`
   - Permissions: `Read Messages`, `Send Messages`, `Manage Messages`, `Read Message History`, `Add Reactions`
   - Copy URL → Open in browser → Select server → Authorize

## Railway Deployment (10 minutes)

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create Project**
   - Click "New Project"
   - "Deploy from GitHub repo" → Select your repo

3. **Add PostgreSQL**
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Wait for provisioning
   - Go to PostgreSQL service → "Variables" tab
   - Note the connection details

4. **Set Environment Variables**
   - In your bot service, go to "Variables" tab
   - Add these variables:
     ```
     DISCORD_TOKEN=your_bot_token_here
     DB_NAME=${{Postgres.PGDATABASE}}
     DB_USER=${{Postgres.PGUSER}}
     DB_PASSWORD=${{Postgres.PGPASSWORD}}
     DB_HOST=${{Postgres.PGHOST}}
     DB_PORT=${{Postgres.PGPORT}}
     ```

5. **Deploy**
   - Railway auto-deploys on git push
   - Check "Logs" tab to verify bot is online

## Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

## Test Commands

- `/block @user keyword1 keyword2` - Block a user with keywords
- `/block @user` - Block a user without keywords
- `/unblock @user` - Unblock a user

## Troubleshooting

- **Bot offline?** Check Railway logs, verify DISCORD_TOKEN
- **Commands not showing?** Wait 5 minutes, ensure `applications.commands` scope
- **Messages not deleting?** Check bot permissions, role hierarchy
- **Database errors?** Verify all DB environment variables are set

See README.md for detailed instructions.

