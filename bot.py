"""
Discord Blocker Bot
A bot that allows users to block other users and prevent them from:
- Tagging/mentioning the blocker
- Replying to the blocker's messages
- Reacting to the blocker's messages
- Using specific keywords in messages
"""
import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

# Initialize database
db = Database()

# Bot configuration
# Intents are required to read message content and monitor events
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.guilds = True  # Required for server operations
intents.guild_messages = True  # Required to monitor messages
intents.guild_reactions = True  # Required to monitor reactions
intents.members = True  # Required to access member information

# Initialize bot with slash commands
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


@bot.event
async def on_ready():
    """
    Called when the bot successfully connects to Discord.
    Syncs slash commands and prints confirmation.
    """
    print(f'Bot logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')


@bot.tree.command(name="block", description="Block a user and set keywords they cannot use")
@app_commands.describe(
    user="The user you want to block",
    keywords="Keywords that the blocked user cannot say (separate multiple keywords with spaces)"
)
async def block_command(interaction: discord.Interaction, user: discord.Member, keywords: str = ""):
    """
    Slash command to block a user.
    
    Args:
        interaction: Discord interaction object
        user: The member to block
        keywords: Space-separated list of keywords the blocked user cannot use
    """
    # Prevent users from blocking themselves
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "You cannot block yourself!",
            ephemeral=True  # Only visible to the command user
        )
        return
    
    # Prevent blocking the bot
    if user.id == bot.user.id:
        await interaction.response.send_message(
            "You cannot block the bot!",
            ephemeral=True
        )
        return
    
    # Parse keywords from the input string
    keyword_list = [kw.strip() for kw in keywords.split() if kw.strip()] if keywords else []
    
    # Store block relationship in database
    success = db.add_block(
        blocker_id=interaction.user.id,
        blocked_id=user.id,
        guild_id=interaction.guild_id,
        keywords=keyword_list
    )
    
    if success:
        # Create response message
        if keyword_list:
            keyword_text = ", ".join(f"`{kw}`" for kw in keyword_list)
            message = f"✅ You have blocked {user.mention}.\n\n**Blocked keywords:** {keyword_text}\n\nThey will not be able to:\n• Tag or mention you\n• Reply to your messages\n• React to your messages\n• Use the blocked keywords"
        else:
            message = f"✅ You have blocked {user.mention}.\n\nThey will not be able to:\n• Tag or mention you\n• Reply to your messages\n• React to your messages"
        
        await interaction.response.send_message(message, ephemeral=True)
    else:
        await interaction.response.send_message(
            "❌ Failed to create block. Please try again.",
            ephemeral=True
        )


@bot.tree.command(name="unblock", description="Unblock a user")
@app_commands.describe(
    user="The user you want to unblock"
)
async def unblock_command(interaction: discord.Interaction, user: discord.Member):
    """
    Slash command to unblock a user.
    
    Args:
        interaction: Discord interaction object
        user: The member to unblock
    """
    success = db.remove_block(
        blocker_id=interaction.user.id,
        blocked_id=user.id,
        guild_id=interaction.guild_id
    )
    
    if success:
        await interaction.response.send_message(
            f"✅ You have unblocked {user.mention}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Failed to remove block. The user may not be blocked.",
            ephemeral=True
        )


@bot.event
async def on_message(message: discord.Message):
    """
    Monitor all messages for:
    1. Mentions/tags of blocked users
    2. Replies to blocked users' messages
    3. Keyword violations
    """
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Ignore DMs (only works in servers)
    if not message.guild:
        return
    
    guild_id = message.guild.id
    author_id = message.author.id
    
    # Get all users who have blocked this message author
    blockers = db.get_all_blockers(blocked_id=author_id, guild_id=guild_id)
    
    if not blockers:
        # No one has blocked this user, check for keyword violations anyway
        has_violation, violating_blockers = db.check_keywords(
            message_content=message.content,
            blocked_id=author_id,
            guild_id=guild_id
        )
        if has_violation:
            # Delete message and notify user
            try:
                await message.delete()
                await message.author.send(
                    "🚫 Your message was deleted because it contained keywords that a user has blocked you from using.",
                    delete_after=10  # Auto-delete after 10 seconds
                )
            except discord.errors.Forbidden:
                # Can't DM user, that's okay
                pass
        return
    
    # Check if message mentions any blocker
    mentioned_users = [user.id for user in message.mentions]
    mentions_blocker = any(blocker_id in mentioned_users for blocker_id in blockers)
    
    # Check if message is a reply to a blocker's message
    is_reply_to_blocker = False
    if message.reference and message.reference.resolved:
        referenced_message = message.reference.resolved
        if isinstance(referenced_message, discord.Message):
            is_reply_to_blocker = referenced_message.author.id in blockers
    
    # Check for keyword violations
    has_keyword_violation, violating_blockers = db.check_keywords(
        message_content=message.content,
        blocked_id=author_id,
        guild_id=guild_id
    )
    
    # If any violation detected, delete message and notify
    if mentions_blocker or is_reply_to_blocker or has_keyword_violation:
        try:
            await message.delete()
            
            # Create notification message
            violations = []
            if mentions_blocker:
                violations.append("tagging/mentioning a user who has blocked you")
            if is_reply_to_blocker:
                violations.append("replying to a user who has blocked you")
            if has_keyword_violation:
                violations.append("using blocked keywords")
            
            violation_text = ", ".join(violations)
            notification = f"🚫 Your message was deleted because you tried {violation_text}. The user has blocked you from interacting with them."
            
            # Try to send ephemeral notification (only works in interactions)
            # Since this is a message event, we'll try to DM the user
            try:
                await message.author.send(notification, delete_after=10)
            except discord.errors.Forbidden:
                # Can't DM user, that's okay - they'll just see their message disappear
                pass
        except discord.errors.Forbidden:
            # Bot doesn't have permission to delete messages
            print(f"Missing permission to delete message in {message.guild.name}")
        except discord.errors.NotFound:
            # Message was already deleted
            pass


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.Member):
    """
    Monitor reactions to prevent blocked users from reacting to blocker's messages.
    
    Args:
        reaction: The reaction that was added
        user: The user who added the reaction
    """
    # Ignore bot reactions
    if user.bot:
        return
    
    # Ignore DMs
    if not reaction.message.guild:
        return
    
    # Get the author of the message being reacted to
    message_author_id = reaction.message.author.id
    
    # Check if the reactor is blocked by the message author
    is_blocked = db.is_blocked(
        blocker_id=message_author_id,
        blocked_id=user.id,
        guild_id=reaction.message.guild.id
    )
    
    if is_blocked:
        # Remove the reaction
        try:
            await reaction.remove(user)
            
            # Try to notify the user
            try:
                await user.send(
                    "🚫 You cannot react to messages from users who have blocked you.",
                    delete_after=10
                )
            except discord.errors.Forbidden:
                # Can't DM user
                pass
        except discord.errors.Forbidden:
            # Bot doesn't have permission to remove reactions
            print(f"Missing permission to remove reaction in {reaction.message.guild.name}")
        except discord.errors.NotFound:
            # Reaction was already removed
            pass


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """
    Monitor edited messages for violations.
    Reuses the same logic as on_message.
    """
    # Process edited message as if it's a new message
    await on_message(after)


# Error handling for commands
@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    Handle errors from slash commands.
    """
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"❌ This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(error)}",
            ephemeral=True
        )
        print(f"Command error: {error}")


# Run the bot
if __name__ == "__main__":
    # Get bot token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("ERROR: DISCORD_TOKEN environment variable not set!")
        print("Please set DISCORD_TOKEN in your .env file or environment variables.")
        exit(1)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("ERROR: Invalid bot token!")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        # Close database connection on shutdown
        db.close()

