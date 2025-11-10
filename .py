import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import timedelta
import random
import json
import re

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

BALANCE_FILE = "balances.json"

def load_balances():
    try:
        with open(BALANCE_FILE, "r") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except FileNotFoundError:
        return {}

def save_balances():
    with open(BALANCE_FILE, "w") as f:
        json.dump(user_balances, f)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="r.", intents=intents, help_command=None)

user_balances = load_balances()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help",
        description="Available commands:",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.add_field(name="r.help", value="Displays this message.", inline=False)
    embed.add_field(name="r.economy", value="Displays a list of economy commands.", inline=False)
    embed.add_field(name="r.mod", value="Displays a list of moderation commands.", inline=False)
    embed.set_footer(text="Bot by ryz")
    await ctx.send(embed=embed)

@bot.command()
async def economy(ctx):
    embed = discord.Embed(
        title="Economy Commands",
        description="Available commands:",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.add_field(name="r.balance", value="Displays your money.", inline=False)
    embed.add_field(name="r.coinflip [heads or tails] [amount]", value="Pick Heads or Tails and win money.", inline=False)
    embed.add_field(name="r.coolrole", value="Purchase the cool role for 10,000 coins.", inline=False)
    embed.set_footer(text="Bot by ryz")
    await ctx.send(embed=embed)

@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    balance = user_balances[user_id]

    if balance == 0:
        description = f"{ctx.author.name}, your balance is 0 coins. Run `r.freemoney` for +10 coins."
    else:
        description = f"{ctx.author.name}, your current balance is {balance} coins."

    save_balances()

    await ctx.send(description)

@bot.command()
@commands.cooldown(1, 300, commands.BucketType.user)
async def freemoney(ctx):
    user_id = str(ctx.author.id)
    user_balances[user_id] += 10
    save_balances()
    await ctx.send(f"{ctx.author.name}, you received 10 coins. New balance: {user_balances[user_id]}")

@bot.command()
async def coinflip(ctx, choice: str, amount: int):
    user_id = str(ctx.author.id)
    choice = choice.lower()

    if choice not in ["heads", "tails"]:
        await ctx.send("Choose either `heads` or `tails`.")
        return
    if amount <= 0:
        await ctx.send("Bet must be positive.")
        return

    if user_id not in user_balances:
        user_balances[user_id] = 10

    if user_balances[user_id] < amount:
        await ctx.send("You dont have enough coins. Run `r.freemoney` for +10 coins.")
        return

    flip = random.choice(["heads", "tails"])
    if flip == choice:
        user_balances[user_id] += amount
        await ctx.send(f"It was **{flip}**! You won {amount} coins!")
    else:
        user_balances[user_id] -= amount
        await ctx.send(f"It was **{flip}**. You lost {amount} coins.")
    save_balances()

@bot.command()
async def coolrole(ctx):
    role_id = 1437541280266715219
    cost = 10000
    user_id = str(ctx.author.id)

    if user_balances[user_id] < cost:
        await ctx.send(f"You need {cost} coins to get this role. Your balance: {user_balances[user_id]}")
        return

    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Role not found.")
        return

    try:
        await ctx.author.add_roles(role)
        user_balances[user_id] -= cost
        save_balances()
        await ctx.send(f"{ctx.author.mention} has gotten the role: {role.name}. You spent {cost} coins.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
async def mod(ctx):
    embed = discord.Embed(
        title="Moderation Commands",
        description="Available commands:",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.add_field(name="r.ban [@user]", value="Bans a mentioned user.", inline=False)
    embed.add_field(name="r.kick [@user]", value="Kicks a mentioned user.", inline=False)
    embed.add_field(name="r.timeout [@user] [time]", value="Timeout a mentioned user.", inline=False)
    embed.add_field(name="r.untimeout [@user]", value="Untimeout a mentioned user.", inline=False)
    embed.set_footer(text="Bot by ryz")
    await ctx.send(embed=embed)

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

bot.run(TOKEN)

