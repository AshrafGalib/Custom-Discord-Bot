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
submit_ss_channel_name = "𐎸・submit-fb-yt-ss"


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


def load_registered_players():
    if not os.path.exists("registered_players.txt"):
        with open("registered_players.txt", "w") as f:
            pass
        return set()
    with open("registered_players.txt", "r") as f:
        return set(line.strip() for line in f.readlines())


def save_registered_players(player_ids):
    with open("registered_players.txt", "a") as f:
        for pid in player_ids:
            f.write(pid + "\n")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Auto give role if 6+ screenshots
    if message.channel.name == submit_ss_channel_name:
        if len(message.attachments) >= 6:
            role = discord.utils.get(message.guild.roles, name="register")
            if role:
                await message.author.add_roles(role)

    # Registration Handling
    if message.channel.name == register_channel_name:
        register_role = discord.utils.get(message.guild.roles, name="register")
        if register_role not in message.author.roles:
            await message.delete()
            await message.channel.send(
                f"❌ {message.author.mention} You must first submit screenshots in {submit_ss_channel_name} to get 'register' role.Otherwise your registration will be deleted automatically."
            )
            return

        content = message.content

        # TEAM NAME
        team_name_match = re.search(
            r"(team name|team)\s*[:\-]\s*(.+)", content, re.IGNORECASE
        )
        if not team_name_match:
            await message.channel.send(
                "❌ Registration failed! `TEAM NAME :` or `TEAM -` Use these formats when typing your team name.Again submit your roster."
            )
            return

        team_name = team_name_match.group(2).strip()
        team_name_lower = team_name.lower()

        # MANAGER
        manager_match = re.search(
            r"(discord leader\s*/\s*manager|leader|manager)\s*[:\-]\s*(<@!?\d+>)",
            content,
            re.IGNORECASE,
        )
        if manager_match:
            manager_mention = manager_match.group(2).strip()
            manager_id = re.search(r"\d+", manager_mention).group()
            manager_member = message.guild.get_member(int(manager_id))
        else:
            manager_member = message.author
            manager_mention = message.author.mention
            manager_id = str(message.author.id)

        # Mentions Check
        all_mentions = re.findall(r"<@!?\d+>", content)
        if not manager_match:
            all_mentions.append(manager_member.mention)

        mention_ids = [re.search(r"\d+", m).group() for m in all_mentions]

        # Prevent mentioning bot
        if str(bot.user.id) in mention_ids:
            await message.channel.send(
                f"❌ {message.author.mention} Registration failed! Do not mention me.Again submit your roster."
            )
            return

        # Inside roster: prevent non-manager duplicates
        player_counts = {}
        for pid in mention_ids:
            player_counts[pid] = player_counts.get(pid, 0) + 1

        for pid, count in player_counts.items():
            if pid != manager_id and count > 1:
                await message.channel.send(
                    f"❌ {message.author.mention} Registration failed! Same player mentioned twice.Again submit your roster."
                )
                return

        # Total minimum mentions
        unique_ids = set(mention_ids)
        if len(unique_ids) < 4:
            await message.channel.send(
                f"❌ {message.author.mention} Registration failed! Minimum 4 Discord mentions (including Manager) required.Again submit your roster."
            )
            return

        registered_teams = load_registered_teams()
        if team_name_lower in registered_teams:
            await message.channel.send(
                f"❌ Team `{team_name}` already registered!"
            )
            return

        # Across rosters: prevent player already used
        registered_players = load_registered_players()
        used_conflicts = [pid for pid in unique_ids if pid in registered_players and pid != manager_id]
        if used_conflicts:
            await message.channel.send(
                f"❌ {message.author.mention} Registration failed! Player's mention is already in another registered team.Again submit your roster"
            )
            return

        # ✅ Success
        confirm_no = get_confirm_number()
        confirm_channel = discord.utils.get(message.guild.text_channels, name=confirm_channel_name)

        if confirm_channel:
            confirm_message = (
                f"Team '**{team_name}**' registered successfully.\n"
                f"Manager: {manager_mention}\n"
                f"Confirmation No: **{confirm_no}**\n"
                f"────────────────────────────"
            )
            await confirm_channel.send(confirm_message)

        # DM Confirmation
        if manager_member:
            try:
                await manager_member.send(
                    f"Your Team Registration is Confirmed in GSL Tier 2!\n"
                    f"Team Name : **{team_name}**\n"
                    f"Confirmation No : **{confirm_no}**"
                )
            except discord.Forbidden:
                print(f"Couldn't DM {manager_member} (DMs closed).")

        save_registered_team(team_name_lower)
        # Save all mentions except manager (manager is allowed multiple)
        registered_players.update([pid for pid in unique_ids if pid != manager_id])
        save_registered_players([pid for pid in unique_ids if pid != manager_id])
        update_confirm_number(confirm_no + 1)

    await bot.process_commands(message)


bot.run('')
