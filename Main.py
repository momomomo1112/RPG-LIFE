import discord
from discord.ext import commands, tasks
import os, json, asyncio
from datetime import datetime, timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

TOKEN = "YOUR_BOT_TOKEN_HERE"

LOG_CATEGORY_NAME = "zeus-logs"
QUARANTINE_ROLE_NAME = "Zeus Quarantine"
LOG_CHANNELS = {
    "moderation": "moderation-logs",
    "roles": "role-logs",
    "channels": "channel-logs",
    "vc": "vc-logs",
    "messages": "message-logs",
    "server": "server-logs",
    "webhooks": "webhook-logs",
    "joins": "join-leave-logs",
    "security": "security-alerts"
}

BAD_WORDS = ["fuck", "shit", "bitch", "asshole", "nigga", "retard", "chutiya", "madarchod", "bhenchod", "gandu", "mc", "bc", "لعنة", "حرام", "كلب"]

if not os.path.exists("data.json"):
    with open("data.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("user_logs.json"):
    with open("user_logs.json", "w") as f:
        json.dump({}, f)

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def load_user_logs():
    with open("user_logs.json", "r") as f:
        return json.load(f)

def save_user_logs(logs):
    with open("user_logs.json", "w") as f:
        json.dump(logs, f, indent=4)

@bot.event
async def on_ready():
    print(f"⚡ Zeus is online as {bot.user}")

async def animated_startup(ctx):
    msg = await ctx.send("☁️ Opening the heavens...")
    await asyncio.sleep(1)
    await msg.edit(content="⚡ Summoning the power of Zeus...")
    await asyncio.sleep(1)
    await msg.edit(content="🏛️ Establishing divine order...")
    await asyncio.sleep(1)
    await msg.edit(content=f"**⚡ Zeus has awakened! Divine protection active.**\nHello {ctx.author.mention}, moderation is live.")

def is_admin(member: discord.Member):
    return member.guild_permissions.administrator

async def setup_logs(guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
    if not category:
        category = await guild.create_category(LOG_CATEGORY_NAME, overwrites=overwrites)
    channels = {}
    for key, name in LOG_CHANNELS.items():
        chan = discord.utils.get(guild.text_channels, name=name)
        if not chan:
            chan = await guild.create_text_channel(name=name, category=category)
        channels[key] = chan
    return channels

async def ensure_quarantine(guild):
    role = discord.utils.get(guild.roles, name=QUARANTINE_ROLE_NAME)
    if not role:
        role = await guild.create_role(name=QUARANTINE_ROLE_NAME)
        for channel in guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False, connect=False)
    return role

@bot.command()
async def zeus(ctx, arg=None):
    if arg == "start" and is_admin(ctx.author):
        await animated_startup(ctx)
        await setup_logs(ctx.guild)
        await ensure_quarantine(ctx.guild)
        await ctx.send("Zeus logging system initialized.")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="⚡ Zeus Command List", color=discord.Color.gold())
    embed.add_field(name=".zeus start", value="Activate Zeus and initialize the system.", inline=False)
    embed.add_field(name=".updates", value="Show server updates in the last 24 hours.", inline=False)
    embed.add_field(name=".help", value="Display this help message.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def updates(ctx):
    if not is_admin(ctx.author):
        return await ctx.send("Admins only.")
    logs = load_user_logs()
    now = datetime.utcnow()
    report = ""
    for uid, events in logs.items():
        for e in events:
            t = datetime.strptime(e["time"], "%Y-%m-%d %H:%M:%S")
            if now - t < timedelta(hours=24):
                report += f"{e['time']} — {e['type']} — {e['desc']}\n"
    embed = discord.Embed(title="⚡ Zeus Server Update (24h)", description=report or "No logs found.", color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Insult Zeus
    if "zeus" in message.content.lower() and any(x in message.content.lower() for x in ["suck", "stupid", "idiot", "useless"]):
        await message.channel.send(f"{message.author.mention}, **YOU suck. I’m Zeus. Respect the gods.**")
        return

    # Bad words
    if any(word in message.content.lower() for word in BAD_WORDS):
        await message.delete()
        await message.channel.send(f"{message.author.mention} ⚠️ No bad words allowed.")
        logs = load_user_logs()
        uid = str(message.author.id)
        logs.setdefault(uid, []).append({
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "Bad Language",
            "desc": message.content[:100]
        })
        save_user_logs(logs)
        return

    await bot.process_commands(message)

@bot.event
async def on_member_update(before, after):
    logs = load_user_logs()
    uid = str(after.id)
    changes = []
    if before.nick != after.nick:
        changes.append(f"Nickname changed: {before.nick} -> {after.nick}")
    if before.avatar != after.avatar:
        changes.append(f"Avatar changed.")
    for change in changes:
        logs.setdefault(uid, []).append({
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "Profile Update",
            "desc": change
        })
    save_user_logs(logs)

@bot.event
async def on_guild_channel_create(channel):
    logs = load_user_logs()
    logs.setdefault("server", []).append({
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "Channel Created",
        "desc": f"{channel.name} ({channel.id})"
    })
    save_user_logs(logs)

bot.run(TOKEN)
