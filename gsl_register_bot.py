import discord
from discord.ext import commands
import re
import os

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

register_channel_name = "𐎸・register-here"
confirm_channel_name = "𐎸・confirm-teams"
submit_ss_channel_name = "𐎸・submut-fb-yt-ss"


def get_confirm_number():
    if not os.path.exists("confirm_count.txt"):
        with open("confirm_count.txt", "w") as f:
            f.write("1")
        return 1
    with open("confirm_count.txt", "r") as f:
        return int(f.read().strip())


def update_confirm_number(new_number):
    with open("confirm_count.txt", "w") as f:
        f.write(str(new_number))


def load_registered_teams():
    if not os.path.exists("registered_teams.txt"):
        with open("registered_teams.txt", "w") as f:
            pass
        return []
    with open("registered_teams.txt", "r") as f:
        return [line.strip().lower() for line in f.readlines()]


def save_registered_team(team_name):
    with open("registered_teams.txt", "a") as f:
        f.write(team_name + "\n")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1️⃣ Auto Give Role if 6+ screenshots
    if message.channel.name == submit_ss_channel_name:
        if len(message.attachments) >= 6:
            role = discord.utils.get(message.guild.roles, name="register")
            if role:
                await message.author.add_roles(role)

    # 2️⃣ Registration Channel Handling
    if message.channel.name == register_channel_name:
        register_role = discord.utils.get(message.guild.roles, name="register")
        if register_role not in message.author.roles:
            warning = await message.channel.send(
                f"❌ {message.author.mention} You must first submit the all screenshots in submut-fb-yt-ss channel to get the 'register' role before submitting your roster.Otherwise your roster will automatically deleted."
            )
            await message.delete()
            return

        content = message.content

        # Extract TEAM NAME
        team_name_match = re.search(
            r"(team name|team)\s*[:\-]\s*(.+)", content, re.IGNORECASE
        )
        if not team_name_match:
            await message.channel.send(
                "❌ **Registration failed!** `TEAM NAME :` or `TEAM -` is missing."
            )
            return

        team_name = team_name_match.group(2).strip()
        team_name_lower = team_name.lower()

        # Extract Manager
        manager_match = re.search(
            r"(discord leader\s*/\s*manager|leader|manager)\s*[:\-]\s*(<@!?\d+>)",
            content,
            re.IGNORECASE,
        )
        if manager_match:
            manager_mention = manager_match.group(2).strip()
            manager_id = int(re.search(r"\d+", manager_mention).group())
            manager_member = message.guild.get_member(manager_id)
        else:
            manager_member = message.author
            manager_mention = message.author.mention

        # All Mentions (Minimum 3 required)
        all_mentions = re.findall(r"<@!?\d+>", content)
        if not manager_match:
            all_mentions.append(manager_member.mention)

        unique_mentions = list(set(all_mentions))

        if len(unique_mentions) < 4:
            await message.channel.send(
                f"❌ {message.author.mention} **Registration failed! Minimum 4 Discord mentions (including Manager) required.Again submit your roster.**"
            )
            return

        registered_teams = load_registered_teams()

        if team_name_lower in registered_teams:
            await message.channel.send(
                f"❌ **Team `{team_name}` already registered!**"
            )
            return

        confirm_no = get_confirm_number()

        confirm_channel = discord.utils.get(
            message.guild.text_channels, name=confirm_channel_name
        )
        if confirm_channel:
            confirm_message = (
                f"✅ **Registration Confirmed!**\n"
                f"**Team Name :** {team_name}\n"
                f"**Team Manager :** {manager_mention}\n"
                f"**Confirm Team No :** {confirm_no}"
            )
            await confirm_channel.send(confirm_message)

            # DM Manager
            if manager_member:
                try:
                    await manager_member.send(
                        f"✅ **Your Team Registration is Confirmed in GSL Tier 2!**\n"
                        f"**Team Name :** {team_name}\n"
                        f"**Confirm Team No :** {confirm_no}"
                    )
                except discord.Forbidden:
                    print(f"Couldn't DM {manager_member} (DMs closed).")

            save_registered_team(team_name_lower)
            update_confirm_number(confirm_no + 1)

    await bot.process_commands(message)


# 🔑 Put your real bot token here
bot.run('')
