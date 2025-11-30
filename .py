#                       _       __  __           _   _           _   
#                      ( )     |  \/  |         | | | |         | |  
#        _ __ _   _ ___|/ ___  | \  / | ___   __| | | |__   ___ | |_ 
#       | '__| | | |_  / / __| | |\/| |/ _ \ / _` | | '_ \ / _ \| __|
#       | |  | |_| |/ /  \__ \ | |  | | (_) | (_| | | |_) | (_) | |_ 
#       |_|   \__, /___| |___/ |_|  |_|\___/ \__,_| |_.__/ \___/ \__|
#              __/ |                                                 
#             |___/                                                  

import discord, json, os, re, asyncio, random, time, threading
from discord.ext import commands
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime
from collections import defaultdict
from discord.ui import Select, View
from discord import app_commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

CONFIG_FILE = "config.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = f.read().strip()
                if data:
                    return json.loads(data)
        except json.JSONDecodeError:
            print("Config file corrupted, resetting to empty config.")
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

bot = commands.Bot(command_prefix="r.", intents=intents, help_command=None)

config = load_config()
antispam_enabled = config.get("antispam_enabled", False)
autorole_enabled = config.get("autorole_enabled", False)
autorole_role_name = "Member"
user_messages = defaultdict(list)

def log_command_to_config(ctx):
    config = load_config()

    gid = str(ctx.guild.id) if ctx.guild else "DM"
    config.setdefault("guilds", {})
    config["guilds"].setdefault(gid, {})
    config["guilds"][gid].setdefault("command_history", [])

    config["guilds"][gid]["command_history"].append({
        "name": ctx.command.name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_config(config)

@bot.listen("on_command")
async def log_command(ctx):
    log_command_to_config(ctx)
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.send(f"Error: {error}")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="r.help | ryz"))
    synced = await bot.tree.sync()

    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Synced {len(synced)} command(s)")
    print(f"Servers: {len(bot.guilds)}")

class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General", description="Basic commands like help and tickets", emoji="📖"),
            discord.SelectOption(label="Moderation", description="Ban, kick, timeout, lock, etc.", emoji="🛡️"),
            discord.SelectOption(label="Utility", description="Purge, slowmode, antispam", emoji="🔧"),
            discord.SelectOption(label="Fun", description="Giveaways and more", emoji="🎉"),
            discord.SelectOption(label="Stats", description="Server stats setup and removal", emoji="📊"),
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        if category == "General":
            embed = discord.Embed(title="📖 General Commands", color=discord.Color.blue())
            embed.add_field(name="`r.help`", value="View all bot commands, organized by category with dropdown navigation", inline=False)
            embed.add_field(name="`r.ticketpanel`", value="Sends a panel with a button to create support tickets.", inline=False)

        elif category == "Moderation":
            embed = discord.Embed(title="🛡️ Moderation Commands", color=discord.Color.red())
            embed.add_field(name="`r.ban [@user]`", value="Bans a mentioned user.", inline=False)
            embed.add_field(name="`r.kick [@user]`", value="Kicks a mentioned user.", inline=False)
            embed.add_field(name="`r.timeout [@user] [duration]`", value="Timeout a mentioned user.", inline=False)
            embed.add_field(name="`r.utimeout [@user]`", value="Untimeout a mentioned user.", inline=False)
            embed.add_field(name="`r.lock`", value="Locks the channel.", inline=False)
            embed.add_field(name="`r.unlock`", value="Unlocks the channel.", inline=False)
            embed.add_field(name="`r.autorole [@role]`", value="Auto Assigns a role to a new user that joins.", inline=False)
            embed.add_field(name="`r.addrole [@user] [@role]`", value="Assigns a role to a user.", inline=False)
            embed.add_field(name="`r.removerole [@user] [@role]`", value="Removes a role from a user.", inline=False)

        elif category == "Utility":
            embed = discord.Embed(title="🔧 Utility Commands", color=discord.Color.green())
            embed.add_field(name="`r.purge [amount]`", value="Deletes a certain amount of messages.", inline=False)
            embed.add_field(name="`r.antispam [on/off]`", value="Prevents spamming.", inline=False)
            embed.add_field(name="`r.slowmode [duration]`", value="Sets a slowmode for a channel.", inline=False)

        elif category == "Fun":
            embed = discord.Embed(title="🎉 Fun Commands", color=discord.Color.purple())
            embed.add_field(name="`r.giveaway [duration] [prize]`", value="Starts a giveaway in the channel.", inline=False)
            embed.add_field(name="`r.coinflip`", value="Flips a coin (Heads/Tails).", inline=False)
            embed.add_field(name="`r.dice [sides]`", value="Rolls a dice with custom sides.", inline=False)
            embed.add_field(name="`r.rps [choice]`", value="Play Rock-Paper-Scissors against the bot.", inline=False)
            embed.add_field(name="`r.slot`", value="Spin a slot machine with emojis.", inline=False)
            embed.add_field(name="`r.eightball [question]`", value="Ask the magic 8-ball a question.", inline=False)
            embed.add_field(name="`r.quote`", value="Get a random inspirational or funny quote.", inline=False)
            embed.add_field(name="`r.ship [@user1] [@user2]`", value="Shows compatibility percentage between two users.", inline=False)
            embed.add_field(name="`r.rate [@user]`", value="Rates a user from 1–10.", inline=False)
            embed.add_field(name="`r.avatar [@user]`", value="Displays a user’s avatar.", inline=False)
            embed.add_field(name="`r.color`", value="Generates a random color with hex code.", inline=False)

        elif category == "Stats":
            embed = discord.Embed(title="📊 Stats Commands", color=discord.Color.gold())
            embed.add_field(name="`r.serverstats`", value="Shows server stats: members, channels, roles, etc.", inline=False)
            embed.add_field(name="`r.setupstats`", value="Creates voice channels that show online/offline members.", inline=False)
            embed.add_field(name="`r.removestats`", value="Removes the server stats voice channels.", inline=False)

        embed.set_footer(text="Bot by ryz")
        await interaction.response.edit_message(embed=embed)

class HelpView(View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help Menu",
        description="Use the dropdown below to select a category.",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.set_footer(text="Bot by ryz")
    await ctx.send(embed=embed, ephemeral=True, view=HelpView())
    
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member):
    try:
        await member.ban()
        await ctx.send(f"{member.mention} has been banned.")
    except commands.MissingPermissions:
        await ctx.send("You dont have permission to use this command.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    try:
        await member.kick()
        await ctx.send(f"{member.mention} has been kicked.")
    except commands.MissingPermissions:
        await ctx.send("You dont have permission to use this command.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: str = "60s"):
    try:
        match = re.match(r"^(\d+)([smh])$", duration.lower())
        if not match:
            await ctx.send("Invalid duration format. Use formats like `30s`, `2m`, or `1h` or `1d` or `1w`.")
            return
        value, unit = int(match.group(1)), match.group(2)
        if unit == "s":
            delta = timedelta(seconds=value)
        elif unit == "m":
            delta = timedelta(minutes=value)
        elif unit == "h":
            delta = timedelta(hours=value)
        elif unit == "d":
            delta = timedelta(days=value)
        elif unit == "w":
            delta = timedelta(weeks=value)

        await member.timeout(delta)
        await ctx.send(f"{member.mention} has been timed out for {value}{unit}.")
    except discord.Forbidden:
        await ctx.send("I dont have permission to timeout this member.")
    except commands.MissingPermissions:
        await ctx.send("You dont have permission to use this command.")
    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"{member.mention} has been removed from timeout.")
    except discord.Forbidden:
        await ctx.send("I dont have permission to untimeout this member.")
    except commands.MissingPermissions:
        await ctx.send("You dont have permission to use this command.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    embed = discord.Embed(
        title="Support Ticket",
        description="Click the button below to create a support ticket.",
        color=discord.Color.from_rgb(173, 216, 230)
    )

    class TicketView(discord.ui.View):
        @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary)
        async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            guild = interaction.guild
            category_name = "TICKETS"
            category = discord.utils.get(guild.categories, name=category_name)

            if category is None:
                category = await guild.create_category(category_name)

            username = interaction.user.name.replace(" ", "-").replace("#", "").lower()
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{username}",
                category=category
            )

            await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
            await ticket_channel.set_permissions(guild.default_role, read_messages=False)

            ticket_embed = discord.Embed(
                title="Ticket Opened",
                description="A staff member will be with you shortly.\nClick the button below to close this ticket.",
                color=discord.Color.from_rgb(173, 216, 230)
            )

            class CloseView(discord.ui.View):
                @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
                async def close_ticket(self, close_interaction: discord.Interaction, close_button: discord.ui.Button):
                    if not close_interaction.user.guild_permissions.manage_channels:
                        await close_interaction.response.send_message(
                            "You don't have permission to close this ticket.",
                            ephemeral=True
                        )
                        return

                    await close_interaction.response.send_message("Closing ticket...", ephemeral=True)
                    await close_interaction.channel.delete()

            await ticket_channel.send(
                content=f"{interaction.user.mention} @here",
                embed=ticket_embed,
                view=CloseView()
            )
            await interaction.response.send_message(
                f"Your ticket has been created: {ticket_channel.mention}",
                ephemeral=True
            )

    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    try:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            msg = await ctx.send(f"{ctx.channel.mention} is already locked.")
            await asyncio.sleep(3)
            await msg.delete()
        else:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            msg = await ctx.send(f"{ctx.channel.mention} locked.")
            await asyncio.sleep(3)
            await msg.delete()
        await ctx.message.delete()
    except Exception as e:
        msg = await ctx.send(f"Error: {e}")
        await asyncio.sleep(3)
        await msg.delete()

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    try:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is True or overwrite.send_messages is None:
            msg = await ctx.send(f"{ctx.channel.mention} is already unlocked.")
            await asyncio.sleep(3)
            await msg.delete()
        else:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            msg = await ctx.send(f"{ctx.channel.mention} unlocked.")
            await asyncio.sleep(3)
            await msg.delete()
        await ctx.message.delete()
    except Exception as e:
        msg = await ctx.send(f"Error: {e}")
        await asyncio.sleep(3)
        await msg.delete()

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"Deleted {len(deleted)-1} messages.")
        await asyncio.sleep(3)
        await msg.delete()
    except Exception as e:
        msg = await ctx.send(f"Error: {e}")
        await asyncio.sleep(3)
        await msg.delete()

@bot.command()
@commands.has_permissions(manage_channels=True)
async def antispam(ctx, toggle: str = None):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    gid = str(ctx.guild.id)
    config.setdefault("guilds", {})
    config["guilds"].setdefault(gid, {})

    if toggle not in ["on", "off"]:
        await ctx.send("Usage: r.antispam [on/off]")
        return

    current = config["guilds"][gid].get("antispam_enabled", False)
    new_state = toggle == "on"

    if current == new_state:
        await ctx.send(f"Anti-spam is already {'enabled' if new_state else 'disabled'}.")
    else:
        config["guilds"][gid]["antispam_enabled"] = new_state
        await ctx.send(f"Anti-spam {'enabled' if new_state else 'disabled'}.")

    config["guilds"][gid]["last_command"] = {
        "name": ctx.command.name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@bot.event
async def on_message(message):
    global antispam_enabled
    if message.author.bot:
        return
    
    if not antispam_enabled:
        return await bot.process_commands(message)

    if antispam_enabled:
        now = time.time()
        timestamps = user_messages[message.author.id]

        timestamps = [t for t in timestamps if now - t < 10]
        timestamps.append(now)
        user_messages[message.author.id] = timestamps

        if len(timestamps) > 3:
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} is spamming! Messages deleted.",
                    delete_after=3
                )
                await message.author.timeout(
                    discord.utils.utcnow() + timedelta(seconds=60),
                    reason="Spamming"
                )
            except Exception as e:
                await message.channel.send(f"Error: {e}")

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, duration: str):
    try:
        match = re.match(r"^(\d+)([smhdw])$", duration.lower())
        if not match:
            await ctx.send("Invalid format. Use `30s`, `2m`, `1h`, `1d`, or `1w`.")
            return

        value, unit = int(match.group(1)), match.group(2)
        delay = 0
        if unit == "s":
            delay = value
        elif unit == "m":
            delay = value * 60
        elif unit == "h":
            delay = value * 3600
        elif unit == "d":
            delay = value * 86400
        elif unit == "w":
            delay = value * 604800

        await ctx.channel.edit(slowmode_delay=delay)
        await ctx.send(f"Set slowmode delay to {value}{unit}.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def getserver(ctx, guild_id: int):
    guild = bot.get_guild(guild_id)
    if not guild:
        await ctx.send("Bot is not in that server or ID is invalid.")
        return

    channel = None
    for ch in guild.text_channels:
        if ch.permissions_for(guild.me).create_instant_invite:
            channel = ch
            break

    if not channel:
        await ctx.send("No channel found where I can create an invite.")
        return

    invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
    await ctx.send(f"Invite for **{guild.name}**: {invite.url}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, duration: str, *, prize: str):
    match = re.match(r"^(\d+)([smhdw])$", duration.lower())
    if not match:
        await ctx.send("Invalid format. Use `30s`, `2m`, `1h`, `1d`, or `1w`.")
        return

    value, unit = int(match.group(1)), match.group(2)
    delay = 0
    if unit == "s":
        delay = value
    elif unit == "m":
        delay = value * 60
    elif unit == "h":
        delay = value * 3600
    elif unit == "d":
        delay = value * 86400
    elif unit == "w":
        delay = value * 604800

    embed = discord.Embed(
        title="Giveaway",
        description=f"Prize: **{prize}**\nReact with 🎉 to enter!\nEnds in {duration}.",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.set_footer(text=f"Hosted by {ctx.author}")

    giveaway_msg = await ctx.send(embed=embed)
    await giveaway_msg.add_reaction("🎉")

    await asyncio.sleep(delay)

    new_msg = await ctx.channel.fetch_message(giveaway_msg.id)
    users = [user async for user in new_msg.reactions[0].users() if not user.bot]

    if not users:
        await ctx.send("No valid entries, no winner.")
        return

    winner = random.choice(users)
    await ctx.send(f"Congratulations {winner.mention}! You won **{prize}**")

@bot.command()
async def serverstats(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"Server Stats for {guild.name}",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setupstats(ctx):
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False)
    }

    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline and not m.bot)
    bots = sum(1 for m in guild.members if m.bot)

    total_channel = await guild.create_voice_channel(f"Members: {total}", overwrites=overwrites)
    online_channel = await guild.create_voice_channel(f"Online Members: {online}", overwrites=overwrites)
    offline_channel = await guild.create_voice_channel(f"Offline Members: {offline}", overwrites=overwrites)
    bots_channel = await guild.create_voice_channel(f"Bots: {bots}", overwrites=overwrites)

    gid = str(guild.id)
    config.setdefault("stats_channels", {})
    config["stats_channels"][gid] = {
        "total": total_channel.id,
        "online": online_channel.id,
        "offline": offline_channel.id,
        "bots": bots_channel.id
    }
    save_config(config)

    await ctx.send("Server stats channels created.")

async def update_stats_channels(guild):
    gid = str(guild.id)
    stats = config.get("stats_channels", {}).get(gid)
    if not stats:
        return

    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline and not m.bot)
    bots = sum(1 for m in guild.members if m.bot)

    try:
        total_channel = guild.get_channel(stats["total"])
        online_channel = guild.get_channel(stats["online"])
        offline_channel = guild.get_channel(stats["offline"])
        bots_channel = guild.get_channel(stats["bots"])

        if total_channel:
            await total_channel.edit(name=f"Members: {total}")
        if online_channel:
            await online_channel.edit(name=f"Online Members: {online}")
        if offline_channel:
            await offline_channel.edit(name=f"Offline Members: {offline}")
        if bots_channel:
            await bots_channel.edit(name=f"Bots: {bots}")
    except Exception as e:
        print(f"Error updating stats for guild {gid}: {e}")

@bot.event
async def on_member_remove(member):
    await update_stats_channels(member.guild)

@bot.event
async def on_presence_update(before, after):
    if before.guild:
        await update_stats_channels(before.guild)

@bot.command()
@commands.has_permissions(administrator=True)
async def removestats(ctx):
    guild = ctx.guild
    gid = str(guild.id)

    stats = config.get("stats_channels", {}).get(gid)
    if not stats:
        await ctx.send("No stats channels are set up for this server.")
        return

    try:
        total_channel = guild.get_channel(stats.get("total"))
        online_channel = guild.get_channel(stats.get("online"))
        offline_channel = guild.get_channel(stats.get("offline"))
        bots_channel = guild.get_channel(stats.get("bots"))

        for channel in [total_channel, online_channel, offline_channel, bots_channel]:
            if channel:
                await channel.delete()

        del config["stats_channels"][gid]
        save_config(config)

        await ctx.send("Server stats channels removed.")
    except Exception as e:
        await ctx.send(f"Error removing stats channels: {e}")

@bot.command()
async def coinflip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"🪙 The coin landed on **{result}**!")

@bot.command()
async def dice(ctx, sides: int = 6):
    roll = random.randint(1, sides)
    await ctx.send(f"🎲 You rolled a **{roll}** on a {sides}-sided dice!")

@bot.command()
async def rps(ctx, choice: str):
    options = ["rock", "paper", "scissors"]
    bot_choice = random.choice(options)
    choice = choice.lower()

    if choice not in options:
        await ctx.send("⚠️ Please choose rock, paper, or scissors.")
        return

    if choice == bot_choice:
        result = "It's a tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "You lose!"

    await ctx.send(f"✂️ You chose **{choice}**, I chose **{bot_choice}**. {result}")

@bot.command()
async def slot(ctx):
    emojis = ["🍒", "🍋", "🍉", "⭐", "7️⃣"]
    result = [random.choice(emojis) for _ in range(3)]
    await ctx.send("🎰 " + " | ".join(result))

    if len(set(result)) == 1:
        await ctx.send("💰 Jackpot! All three match!")
    elif len(set(result)) == 2:
        await ctx.send("✨ Nice! Two match!")
    else:
        await ctx.send("😢 Better luck next time!")

@bot.command(name="8ball")
async def eightball(ctx, *, question: str):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Ask again later",
        "Without a doubt", "Not looking good", "Absolutely", "I don’t think so"
    ]
    await ctx.send(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@bot.command()
async def quote(ctx):
    quotes = [
        "“The best way to predict the future is to invent it.” – Alan Kay",
        "“Do or do not. There is no try.” – Yoda",
        "“Stay hungry, stay foolish.” – Steve Jobs",
        "“In the middle of difficulty lies opportunity.” – Albert Einstein"
    ]
    await ctx.send(random.choice(quotes))

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(0, 100)
    await ctx.send(f"{user1.display_name} and {user2.display_name} = {percentage}% compatibility!")

@bot.command()
async def rate(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    rating = random.randint(1, 10)
    await ctx.send(f"⭐ I rate {user.display_name} a {rating}/10!")

@bot.command()
async def avatar(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    embed = discord.Embed(title=f"{user.display_name}'s Avatar")
    embed.set_image(url=user.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def color(ctx):
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    hex_code = f"#{r:02x}{g:02x}{b:02x}"
    embed = discord.Embed(title="🎨 Random Color", description=hex_code, color=discord.Color.from_rgb(r, g, b))
    await ctx.send(embed=embed)

@bot.command()
async def servers(ctx):
    server_list = "\n".join(f"{guild.name} (ID: {guild.id})" for guild in bot.guilds)
    total = len(bot.guilds)
    message = f"Connected servers:\n{server_list}\n\nTotal servers: {total}"
    await ctx.send(message)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def autorole(ctx, role: discord.Role = None):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    gid = str(ctx.guild.id)
    config.setdefault("guilds", {})
    config["guilds"].setdefault(gid, {})

    if role is None:
        await ctx.send("Usage: r.autorole [@role_name]")
        return

    config["guilds"][gid]["autorole_enabled"] = True
    config["guilds"][gid]["autorole_role_id"] = role.id
    config["guilds"][gid]["last_command"] = {
        "name": ctx.command.name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    await ctx.send(f"Autorole set to '{role.name}'.")

@bot.event
async def on_member_join(member):
    await update_stats_channels(member.guild)
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        return

    gid = str(member.guild.id)
    guild_config = config.get("guilds", {}).get(gid, {})
    if not guild_config.get("autorole_enabled"):
        return

    role_id = guild_config.get("autorole_role_id")
    if not role_id:
        return

    role = member.guild.get_role(role_id)
    if role:
        await asyncio.sleep(3)
        await member.add_roles(role)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, target: str, role: discord.Role):
    if target.lower() == "@everyone":
        count = 0
        for member in ctx.guild.members:
            if not member.bot and role not in member.roles:
                try:
                    await member.add_roles(role)
                    count += 1
                except Exception:
                    continue
        await ctx.send(f" Assigned '{role.name}' to {count} members.")
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            await member.add_roles(role)
            await ctx.send(f"{member.mention} has been given the '{role.name}' role.")
        except Exception as e:
            await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, target: str, role: discord.Role):
    if target.lower() == "@everyone":
        count = 0
        for member in ctx.guild.members:
            if not member.bot and role in member.roles:
                try:
                    await member.remove_roles(role)
                    count += 1
                except Exception:
                    continue
        await ctx.send(f"Removed '{role.name}' from {count} members.")
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            await member.remove_roles(role)
            await ctx.send(f"Removed '{role.name}' from {member.mention}.")
        except Exception as e:
            await ctx.send(f"Error: {e}")
#            __                                           _     
#           / /                                          | |    
#          / /__ ___  _ __ ___  _ __ ___   __ _ _ __   __| |___ 
#         / / __/ _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` / __|
#        / / (_| (_) | | | | | | | | | | | (_| | | | | (_| \__ \
#       /_/ \___\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|___/

# /help
@bot.tree.command(
    name="help",
    description="View all bot commands, organized by category with dropdown navigation."
)
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Help Menu",
        description="Use the dropdown below to select a category.",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.set_footer(text="Bot by ryz")
    await interaction.response.send_message(embed=embed, ephemeral=True, view=HelpView())

# /ban
@bot.tree.command(name="ban", description="Ban a member from the server.")
async def ban_command(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.ban(reason=f"Banned by {interaction.user}")
        await interaction.response.send_message(f"{member.mention} has been banned.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don’t have permission to ban this member.", ephemeral=True)

# /kick
@bot.tree.command(name="kick", description="Kick a member from the server.")
async def kick_command(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.kick(reason=f"Kicked by {interaction.user}")
        await interaction.response.send_message(f"{member.mention} has been kicked.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don’t have permission to kick this member.", ephemeral=True)

# /timeout
@bot.tree.command(name="timeout", description="Timeout a member for a duration.")
async def timeout_command(interaction: discord.Interaction, member: discord.Member, duration: str = "60s"):
    match = re.match(r"^(\d+)([smhdw])$", duration.lower())
    if not match:
        await interaction.response.send_message("Invalid format. Use `30s`, `2m`, `1h`, `1d`, or `1w`.", ephemeral=True)
        return

    value, unit = int(match.group(1)), match.group(2)
    delta = {
        "s": timedelta(seconds=value),
        "m": timedelta(minutes=value),
        "h": timedelta(hours=value),
        "d": timedelta(days=value),
        "w": timedelta(weeks=value)
    }[unit]

    try:
        await member.timeout(delta, reason=f"Timed out by {interaction.user}")
        await interaction.response.send_message(f"{member.mention} has been timed out for {value}{unit}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don’t have permission to timeout this member.", ephemeral=True)

# /untimeout
@bot.tree.command(name="untimeout", description="Remove timeout from a member.")
async def untimeout_command(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.timeout(None, reason=f"Untimed out by {interaction.user}")
        await interaction.response.send_message(f"{member.mention} has been removed from timeout.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don’t have permission to untimeout this member.", ephemeral=True)

# /ticketpanel
@bot.tree.command(name="ticketpanel", description="Open the ticket panel.")
async def ticketpanel_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support Ticket",
        description="Click the button below to create a support ticket.",
        color=discord.Color.from_rgb(173, 216, 230)
    )

    class TicketView(discord.ui.View):
        @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary)
        async def create_ticket(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            guild = button_interaction.guild
            category = discord.utils.get(guild.categories, name="TICKETS") or await guild.create_category("TICKETS")
            username = button_interaction.user.name.replace(" ", "-").lower()
            ticket_channel = await guild.create_text_channel(f"ticket-{username}", category=category)

            await ticket_channel.set_permissions(button_interaction.user, read_messages=True, send_messages=True)
            await ticket_channel.set_permissions(guild.default_role, read_messages=False)

            ticket_embed = discord.Embed(
                title="Ticket Opened",
                description="A staff member will be with you shortly.\nClick below to close this ticket.",
                color=discord.Color.from_rgb(173, 216, 230)
            )

            class CloseView(discord.ui.View):
                @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
                async def close_ticket(self, close_interaction: discord.Interaction, button: discord.ui.Button):
                    if not close_interaction.user.guild_permissions.manage_channels:
                        await close_interaction.response.send_message("You can't close this ticket.", ephemeral=True)
                        return
                    await close_interaction.response.send_message("Closing ticket...", ephemeral=True)
                    await close_interaction.channel.delete()

            await ticket_channel.send(content=f"{button_interaction.user.mention} @here", embed=ticket_embed, view=CloseView())
            await button_interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)

    await interaction.response.send_message(embed=embed, ephemeral=True, view=TicketView())

# /lock
@bot.tree.command(name="lock", description="Lock the current channel.")
async def lock_command(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"{interaction.channel.mention} locked.", ephemeral=True)

# /unlock
@bot.tree.command(name="unlock", description="Unlock the current channel.")
async def unlock_command(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"{interaction.channel.mention} unlocked.", ephemeral=True)

# /purge
@bot.tree.command(name="purge", description="Delete a number of messages from the channel.")
async def purge_command(interaction: discord.Interaction, amount: int):
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)

# /antispam
@bot.tree.command(name="antispam", description="Toggle anti-spam system on or off.")
async def antispam_command(interaction: discord.Interaction, toggle: str):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    gid = str(interaction.guild.id)
    config.setdefault("guilds", {}).setdefault(gid, {})

    if toggle not in ["on", "off"]:
        await interaction.response.send_message("Usage: /antispam [on/off]", ephemeral=True)
        return

    new_state = toggle == "on"
    config["guilds"][gid]["antispam_enabled"] = new_state
    config["guilds"][gid]["last_command"] = {
        "name": "antispam",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    await interaction.response.send_message(f"Anti-spam {'enabled' if new_state else 'disabled'}.", ephemeral=True)

# /slowmode
@bot.tree.command(name="slowmode", description="Set slowmode delay for the channel.")
async def slowmode_command(interaction: discord.Interaction, duration: str):
    match = re.match(r"^(\d+)([smhdw])$", duration.lower())
    if not match:
        await interaction.response.send_message("Invalid format. Use `30s`, `2m`, `1h`, `1d`, or `1w`.", ephemeral=True)
        return

    value, unit = int(match.group(1)), match.group(2)
    delay = {
        "s": value,
        "m": value * 60,
        "h": value * 3600,
        "d": value * 86400,
        "w": value * 604800
    }[unit]

    await interaction.channel.edit(slowmode_delay=delay)
    await interaction.response.send_message(f"Set slowmode delay to {value}{unit}.", ephemeral=True)

# /getserver
@bot.tree.command(name="getserver", description="Get an invite link to a server by ID.")
async def getserver_command(interaction: discord.Interaction, guild_id: int):
    guild = interaction.client.get_guild(guild_id)
    if not guild:
        await interaction.response.send_message("Bot is not in that server or ID is invalid.", ephemeral=True)
        return

    channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite), None)
    if not channel:
        await interaction.response.send_message("No channel found where I can create an invite.", ephemeral=True)
        return

    invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
    await interaction.response.send_message(f"Invite for **{guild.name}**: {invite.url}", ephemeral=True)

# /giveaway
@bot.tree.command(name="giveaway", description="Start a giveaway with a duration and prize.")
async def giveaway_command(interaction: discord.Interaction, duration: str, prize: str):
    match = re.match(r"^(\d+)([smhdw])$", duration.lower())
    if not match:
        await interaction.response.send_message("Invalid format. Use `30s`, `2m`, `1h`, `1d`, or `1w`.", ephemeral=True)
        return

    value, unit = int(match.group(1)), match.group(2)
    delay = {
        "s": value,
        "m": value * 60,
        "h": value * 3600,
        "d": value * 86400,
        "w": value * 604800
    }[unit]

    embed = discord.Embed(
        title="Giveaway 🎉",
        description=f"Prize: **{prize}**\nReact with 🎉 to enter!\nEnds in {duration}.",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.set_footer(text=f"Hosted by {interaction.user}")

    giveaway_msg = await interaction.channel.send(embed=embed)
    await giveaway_msg.add_reaction("🎉")
    await interaction.response.send_message("Giveaway started!", ephemeral=True)

    await asyncio.sleep(delay)
    new_msg = await interaction.channel.fetch_message(giveaway_msg.id)
    users = [user async for user in new_msg.reactions[0].users() if not user.bot]

    if not users:
        await interaction.channel.send("No valid entries, no winner.")
        return

    winner = random.choice(users)
    await interaction.channel.send(f"Congratulations {winner.mention}! You won **{prize}** 🎉")

# /serverstats
@bot.tree.command(name="serverstats", description="Show statistics about the server.")
async def serverstats_command(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"Server Stats for {guild.name}",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /removestats
@bot.tree.command(name="removestats", description="Remove server stats channels.")
async def removestats_command(interaction: discord.Interaction):
    guild = interaction.guild
    gid = str(guild.id)
    stats = config.get("stats_channels", {}).get(gid)
    if not stats:
        await interaction.response.send_message("No stats channels are set up for this server.", ephemeral=True)
        return

    try:
        for channel_id in stats.values():
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.delete()
        del config["stats_channels"][gid]
        save_config(config)
        await interaction.response.send_message("Server stats channels removed.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error removing stats channels: {e}", ephemeral=True)

# /coinflip
@bot.tree.command(name="coinflip", description="Flip a coin.")
async def coinflip_command(interaction: discord.Interaction):
    result = random.choice(["Heads", "Tails"])
    await interaction.response.send_message(f"🪙 The coin landed on **{result}**!", ephemeral=True)

# /dice
@bot.tree.command(name="dice", description="Roll a dice with a given number of sides.")
async def dice_command(interaction: discord.Interaction, sides: int = 6):
    roll = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a **{roll}** on a {sides}-sided dice!", ephemeral=True)

# /rps
@bot.tree.command(name="rps", description="Play rock-paper-scissors against the bot.")
async def rps_command(interaction: discord.Interaction, choice: str):
    options = ["rock", "paper", "scissors"]
    bot_choice = random.choice(options)
    choice = choice.lower()
    if choice not in options:
        await interaction.response.send_message("⚠️ Please choose rock, paper, or scissors.", ephemeral=True)
        return
    if choice == bot_choice:
        result = "It's a tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "You lose!"
    await interaction.response.send_message(
        f"✂️ You chose **{choice}**, I chose **{bot_choice}**. {result}", ephemeral=True
    )

# /slot
@bot.tree.command(name="slot", description="Spin the slot machine.")
async def slot_command(interaction: discord.Interaction):
    emojis = ["🍒", "🍋", "🍉", "⭐", "7️⃣"]
    result = [random.choice(emojis) for _ in range(3)]
    message = "🎰 " + " | ".join(result)
    if len(set(result)) == 1:
        message += "\n💰 Jackpot! All three match!"
    elif len(set(result)) == 2:
        message += "\n✨ Nice! Two match!"
    else:
        message += "\n😢 Better luck next time!"
    await interaction.response.send_message(message, ephemeral=True)

# /8ball
@bot.tree.command(name="8ball", description="Ask the magic 8-ball a question.")
async def eightball_command(interaction: discord.Interaction, question: str):
    responses = [
        "Yes", "No", "Maybe", "Definitely", "Ask again later",
        "Without a doubt", "Not looking good", "Absolutely", "I don’t think so"
    ]
    await interaction.response.send_message(
        f"🎱 Question: {question}\nAnswer: {random.choice(responses)}", ephemeral=True
    )

# /quote
@bot.tree.command(name="quote", description="Get a random inspirational quote.")
async def quote_command(interaction: discord.Interaction):
    quotes = [
        "“The best way to predict the future is to invent it.” – Alan Kay",
        "“Do or do not. There is no try.” – Yoda",
        "“Stay hungry, stay foolish.” – Steve Jobs",
        "“In the middle of difficulty lies opportunity.” – Albert Einstein"
    ]
    await interaction.response.send_message(random.choice(quotes), ephemeral=True)

# /ship
@bot.tree.command(name="ship", description="Check compatibility between two users.")
async def ship_command(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(0, 100)
    await interaction.response.send_message(
        f"{user1.display_name} ❤️ {user2.display_name} = {percentage}% compatibility!", ephemeral=True
    )

# /rate
@bot.tree.command(name="rate", description="Rate a user out of 10.")
async def rate_command(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user
    rating = random.randint(1, 10)
    await interaction.response.send_message(f"⭐ I rate {user.display_name} a {rating}/10!", ephemeral=True)

# /avatar
@bot.tree.command(name="avatar", description="Show a user's avatar.")
async def avatar_command(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user
    embed = discord.Embed(title=f"{user.display_name}'s Avatar")
    embed.set_image(url=user.avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /color
@bot.tree.command(name="color", description="Generate a random color.")
async def color_command(interaction: discord.Interaction):
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    hex_code = f"#{r:02x}{g:02x}{b:02x}"
    embed = discord.Embed(title="🎨 Random Color", description=hex_code, color=discord.Color.from_rgb(r, g, b))
    await interaction.response.send_message(embed=embed, ephemeral=True)

# /autorole
@bot.tree.command(name="autorole", description="Set an autorole for new members.")
async def autorole_command(interaction: discord.Interaction, role: discord.Role):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    gid = str(interaction.guild.id)
    config.setdefault("guilds", {}).setdefault(gid, {})

    config["guilds"][gid]["autorole_enabled"] = True
    config["guilds"][gid]["autorole_role_id"] = role.id
    config["guilds"][gid]["last_command"] = {
        "name": "autorole",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    await interaction.response.send_message(f"Autorole set to '{role.name}'.", ephemeral=True)

# /addrole
@bot.tree.command(name="addrole", description="Add a role to a member or everyone.")
async def addrole_command(interaction: discord.Interaction, target: str, role: discord.Role):
    if target.lower() == "@everyone":
        count = 0
        for member in interaction.guild.members:
            if not member.bot and role not in member.roles:
                try:
                    await member.add_roles(role)
                    count += 1
                except Exception:
                    continue
        await interaction.response.send_message(f"Assigned '{role.name}' to {count} members.", ephemeral=True)
    else:
        try:
            member = await commands.MemberConverter().convert(interaction, target)
            await member.add_roles(role)
            await interaction.response.send_message(
                f"{member.mention} has been given the '{role.name}' role.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

# /removerole
@bot.tree.command(name="removerole", description="Remove a role from a member or everyone.")
async def removerole_command(interaction: discord.Interaction, target: str, role: discord.Role):
    if target.lower() == "@everyone":
        count = 0
        for member in interaction.guild.members:
            if not member.bot and role in member.roles:
                try:
                    await member.remove_roles(role)
                    count += 1
                except Exception:
                    continue
        await interaction.response.send_message(f"Removed '{role.name}' from {count} members.", ephemeral=True)
    else:
        try:
            member = await commands.MemberConverter().convert(interaction, target)
            await member.remove_roles(role)
            await interaction.response.send_message(
                f"Removed '{role.name}' from {member.mention}.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

bot.run(TOKEN)
