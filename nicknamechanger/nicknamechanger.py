from discord.ext import commands
import re
import discord
import asyncio
from datetime import datetime
import unicodedata
import aiohttp



class NameChanger:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="check")
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nickname_checker(self, ctx, output="channel"):
        """This will check if someone has special characters in their nickname and will either give you a list of all
        users who have special characters in their name or will directly change them.
        Example: っ, !, ◔
        """
        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '👍'

        server = ctx.message.guild
        membercount = server.member_count
        check_change = False
        # checks if the bot has the ability to change nicknames, if yes asks the user if he/she wants to get the list
        # or wants the nicknames directly changed
        if ctx.message.guild.me.guild_permissions.manage_nicknames:
            msg = await ctx.send("Would you like me to change all nicknames which contain special characters? If yes"
                                 " please add the `👍` emote as reaction.\nIf you don't want me to do it you don't have"
                                 " to do anything")
            await msg.add_reaction("👍")
            try:
                await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                check_change = True
            except asyncio.TimeoutError:
                pass
        else:
            check_change = False
        if check_change:
            text = f"""Okay. I will now check {membercount} members if their nicknames don't 
contain special characters."""
            if membercount > 100:
                text = text + f" This might take a while."
            await ctx.send(text)
            counter = 0
            changed_users = ""
            time_before = datetime.utcnow()
            for member in server.members:
                m_nick = member.display_name
                changed_nick = self.nickname_maker(m_nick)
                if m_nick != changed_nick:
                    # checks if a user can change his nickname if he is able to his nick will not be changed
                    if not member.guild_permissions.change_nickname:
                        try:
                            await member.edit(reason=f"Old name ({m_nick}) contained special characters.",
                                              nick=changed_nick)
                            changed_users = changed_users + f"{member.name}: {m_nick} was changed to {changed_nick}\n"
                        except commands.MissingPermissions:
                            pass
                        counter += 1
            if changed_users == "":
                link = await self.mystbin(stringx="No users with special characters in their nicknames could be found.")
            else:
                link = await self.mystbin(stringx=f"Found {counter} members:\n{changed_users}")
            time_after = datetime.utcnow()
            difference = time_after - time_before
            difference = round(difference.total_seconds() / 60.0, 1)
            embed = discord.Embed(
                color=discord.Color.green(),
                title="Successfully finished!",
                description=f"Changed {counter} nicknames in {difference} minutes. Here is a list with all changes: "
                            f"{link}",
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=f"{ctx.message.author}", icon_url=f"{ctx.message.author.avatar_url}")
            if output == "channel":
                await ctx.send(embed=embed)
            else:
                if output == "channel":
                    await ctx.send(embed=embed)
                else:
                    await ctx.message.author(embed=embed)
        else:
            # only returns the list
            await ctx.send("Okay. I will create a file now with all users who have special characters in their name.")
            changed_users = ""
            counter_ = 0
            time_before = datetime.utcnow()
            for member in server.members:
                m_nick = member.display_name
                changed_nick = self.nickname_maker(m_nick)
                if m_nick != changed_nick:
                    counter_ += 1
                    changed_users = changed_users + f"\n{member}({member.id})'s nickname/name ({m_nick}) could be " \
                                                    f"changed to {changed_nick}"
            time_after = datetime.utcnow()
            difference = time_after - time_before
            difference = round(difference.total_seconds() / 60.0, 1)
            if changed_users == "":
                link = await self.mystbin(stringx="No users with special characters in their nicknames could be found.")
            else:
                link = await self.mystbin(stringx=f"Found {counter_} members:\n{changed_users}")
            embed = discord.Embed(
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
                title="Successfully finished!",
                description=f"Found {counter_} members with special characters in their nickname in "
                            f"{difference} minutes.\nHere is the link to the list: {link}",
            )
            embed.set_author(name=f"{ctx.message.author}", icon_url=f"{ctx.message.author.avatar_url}")
            await ctx.send(embed=embed)

    @staticmethod
    def strip_accents(text):
        try:
            text = unicodedata.normalize('NFD', text)
            text = text.encode('ascii', 'ignore')
            text = text.decode("utf-8")
        except Exception as e:
            print(e)
            pass
        return str(text)

    def nickname_maker(self, old_nick):
        old_nick = self.strip_accents(old_nick)
        changed_nick = re.sub('[^a-zA-Z0-9 \n.]', '', old_nick)
        if len(changed_nick.replace(" ", "")) <= 1:
            changed_nick = "Request a new nickname"
        return changed_nick

    @nickname_checker.error
    async def nickname_error(self, ctx, error):
    # error handler
        if isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.CommandError):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="Something didn't go quite right...",
                description="I will report this error."
            )
            embed.set_author(name=f"{ctx.message.author}", icon_url=f"{ctx.message.author.avatar_url}")
            await ctx.send(embed=embed)
            print(error)

    @commands.command(name="setnick")
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def setnick_cmd(self, ctx, user: discord.Member=None, *, nickname: str=None):
        if nickname is None or user is None and len(nickname) >= 2:
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred.",
                description=f"Please follow the format: `{ctx.prefix}setnick {'user'} {'new nickname'}`.\n"
                            f"If you followed the format please make sure that the new nickname is at least two chara"
                            f"cters long."
            )
            return await ctx.send(embed=embed)
        await user.edit(nick=nickname, reason=f"Nickname edit by {ctx.message.author.name} ({ctx.message.author.id})")
        embed = discord.Embed(
            color=discord.Color.green(),
            title=f"Successfully changed {user}'s nickname.",
            description=f"New nickname: {nickname}\nOld nickname: {user.display_name}"
        )
        await ctx.send(embed=embed)

    @setnick_cmd.error
    async def setnick_error(self, ctx, error):
    # error handler
        if isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="I am missing a necessary permission.",
                description="Please make sure I have the manage nicknames permission."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandError):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="Something didn't go quite right...",
                description="I will report this error."
            )
            embed.set_author(name=f"{ctx.message.author}", icon_url=f"{ctx.message.author.avatar_url}")
            await ctx.send(embed=embed)
            print(error)

    @staticmethod
    async def mystbin(stringx):
        async with aiohttp.ClientSession() as session:
            async with session.post("http://mystb.in/documents", data=stringx.encode('utf-8')) as post:
                post = await post.json()      
        return f"http://mystb.in/{post['key']}.txt"
