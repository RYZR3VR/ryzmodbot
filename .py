import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import timedelta
import random
import json

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
    embed.set_footer(text="Bot by ryz")
    await ctx.send(embed=embed)@bot.command()

@bot.command()
async def economy(ctx):
    embed = discord.Embed(
        title="Economy Commands",
        description="Available commands:",
        color=discord.Color.from_rgb(173, 216, 230)
    )
    embed.add_field(name="r.balance", value="Displays your money.", inline=False)
    embed.add_field(name="r.coinflip [heads or tails] [amount]", value="Displays this message.", inline=False)
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
        await ctx.send("You don't have enough coins. Run `r.freemoney` for +10 coins.")
        return

    flip = random.choice(["heads", "tails"])
    if flip == choice:
        user_balances[user_id] += amount
        await ctx.send(f"It was **{flip}**! You won {amount} coins!")
    else:
        user_balances[user_id] -= amount
        await ctx.send(f"It was **{flip}**. You lost {amount} coins.")

    save_balances()

bot.run(TOKEN)