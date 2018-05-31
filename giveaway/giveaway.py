from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
import discord
import datetime
from random import choice, randint
import re

DATE_STRING = "{days}d{hours}h{minutes}m"
GIVEAWAY_EMOTE = "🎉"


class Giveaway:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="giveaway", invoke_without_command=True)
    async def giveaway(self, ctx):
        """A basic guide for the giveaway cog"""
        embed = discord.Embed(
            color=discord.Color.blue(),
            title="Giveaway guide",
            description=f"Basic format: `{ctx.prefix}giveaway start {DATE_STRING + ' - duration'} {'prize'}`"
                        f"\nBoth the prize and the duration are required arguments."
        )
        if ctx.guild is not None:
            channel = choice(ctx.guild.channels)
            cnt = 0
            while type(channel) != discord.TextChannel:
                cnt += 1
                channel = choice(ctx.guild.channels)
                if cnt > 20:
                    channel_mention = "{channel mention}"
            if not cnt > 20:
                channel_mention = channel.mention
        embed.add_field(
            name="More information:",
            value="If you want to host the giveaway in a specified channel add `{channel mention}c` to the command."
                  f" Example: {ctx.prefix}giveaway start 7d10h discord nitro {channel_mention}c. You **have to**"
                  f" use a channel mention and don't forget the `c` after it.\nIf you want to host a giveaway"
                  " with a specified amount of winners add `{number from 1 to 9}w` to the command. "
                  f"Example: {ctx.prefix}giveaway start 2h discord nitro {randint(1, 9)}w.\nBoth of these extra "
                  " features are not needed arguments."
        )
        await ctx.send(embed=embed)

    @giveaway.command(name="start")
    @commands.guild_only()
    @commands.has_role("Giveaways")
    @commands.bot_has_permissions(add_reactions=True)
    async def cmd_giveaway(self, ctx, time: str=None, *, prize: str=None):
        f"""Start giveaways, use {ctx.prefix}giveaway for more information"""
        # check the inputs
        winners = re.search("[\d]w", prize)
        if winners is not None:
            prize = prize.replace(winners.group(0), "")
            winners = int(winners.group(0).replace("w", ""))
            if winners == 0:
                winners = 1
        else:
            winners = 1
        channel = re.search(r"<#(?P<channel_id>\d+)>c", prize)
        if channel is not None:
            prize = prize.replace(channel.group(0), "")
            channel = ctx.guild.get_channel(int(channel.groupdict()["channel_id"]))
        else:
            channel = ctx.channel
        perms = ctx.me.permissions_in(channel)
        if not perms.add_reactions and perms.embed_links and perms.send_messages:
            return await ctx.send(content="Please make sure that I have the `send messages`, `embed_links` and"
                                          " `add_reactions` permission in this channel.", delete_after=15)
        end_time = self.end_time(time)
        if end_time is None:
            return await ctx.send(f"Please follow the format: `{DATE_STRING}`. You can also only use "
                                  "one/two of the three possible time units.")
        if prize is None:
            return await ctx.send(f"Please follow the format: `{ctx.prefix}{ctx.command} {DATE_STRING} {'{prize}'}`")
        # send the giveaway embed
        giveaway_embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{GIVEAWAY_EMOTE} GIVEAWAY! {GIVEAWAY_EMOTE}",
            description=f"**Prize:** {prize}\n**Possible winners:** {winners} {'member' if winners == 1 else 'members'}"
        )
        giveaway_embed.add_field(
            name="End date:",
            value=f"{str(end_time).split('.')[0]}"
        )
        giveaway_embed.set_footer(text=f"Click on the {GIVEAWAY_EMOTE} to enter!")
        msg = await channel.send(embed=giveaway_embed)
        await msg.add_reaction(f"{GIVEAWAY_EMOTE}")
        # set up the scheduler
        scheduler = AsyncIOScheduler()
        scheduler.configure(timezone=end_time.tzname())
        scheduler.add_job(func=self.giveaway_embed, trigger="date", run_date=end_time, args=(prize, channel,
                                                                                             msg.id, winners)
                          )
        scheduler.start()
        await ctx.send("Giveaway started!", delete_after=10)

    def end_time(self, time):
        # makes the end time of the giveaway
        if time is None: return None
        try:
            days = 0; hours = 0; minutes = 0
            new_tm = self.get_time(time, "d")
            if new_tm is not None:
                time = new_tm[1]
                days = new_tm[0]
            new_tm = self.get_time(time, "h")
            if new_tm is not None:
                time = new_tm[1]
                hours = new_tm[0]
            new_tm = self.get_time(time, "m")
            if new_tm is not None:
                minutes = new_tm[0]
            return datetime.datetime.now() + datetime.timedelta(days=float(days), hours=float(hours),
                                                                minutes=float(minutes))
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

    @staticmethod
    def get_time(time, unit: str):
        # time maker
        if unit in time:
            new_tm = time.split(unit)
            return new_tm
        else:
            return None

    async def giveaway_embed(self, prize, channel: discord.TextChannel, msg_id: int, winner_num: int):
        # creates the embed for the commands
        message = await channel.get_message(msg_id)
        if message is None:
            return await channel.send(content="I couldn't determine a winner.")
        reactions = message.reactions
        winners = []
        await message.remove_reaction(member=message.author, emoji=f"{GIVEAWAY_EMOTE}")
        for reaction in reactions:
            if reaction.emoji == f"{GIVEAWAY_EMOTE}":
                for i in range(winner_num):
                    winners.append(choice(await reaction.users().flatten()))
        if len(winners) < 1:
            return await message.edit(content="I couldn't determine a winner.")
        text = await self.text_builder(winners)
        embed = discord.Embed(
            color=discord.Color.green(),
            title=f"{GIVEAWAY_EMOTE} Giveaway! {GIVEAWAY_EMOTE}",
            description=f"{text}! Congratulations!\n"
        )
        embed.add_field(
            name="Prize:",
            value=prize
        )
        await message.edit(embed=embed)

    @staticmethod
    async def text_builder(winners: [list, tuple]):
        if len(winners) < 2:
            return f"{winners[0].mention} has won the giveaway!"
        else:
            text = ""
            if winners.count(winners[0]) == len(winners):
                return f"{winners[0].mention} has won every prize in the giveaway"
            for member in winners:
                text += member.mention + ", "
            text = text[:2] + " have won the giveaway"
            return text

    @cmd_giveaway.error
    async def error_handler_giveaway(self, ctx, error):
        # error handler
        if isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send("Please make sure that I can add reactions to my messages and embed links.")
        elif isinstance(error, commands.CheckFailure):
            role = discord.utils.get(ctx.guild.roles, name="Giveaways")
            if role is not None:
                return
            if ctx.author.permissions_in(ctx.channel).manage_roles or \
                    ctx.author.permissions_in(ctx.channel).manage_server:
                await ctx.send("Please create a role called `Giveaways` and give it to everyone who should be able"
                               " to host giveaways.")
            else:
                return

    @giveaway.command(name="reroll")
    @commands.guild_only()
    @commands.has_role("Giveaways")
    @commands.bot_has_permissions(embed_links=True)
    async def reroll_giveaways(self, ctx, message_id=None):
        """"Rerolls the giveaway"""
        channel = ctx.channel
        message = None
        # gets the right message
        if message_id is None:
            async for message in channel.history(limit=50):
                if message.author == ctx.me:
                    if len(message.embeds) > 0:
                        message = message
                        break
        else:
            message = await channel.get_message(message_id)
        if message is None:
            return await ctx.send(content="Please specify a valid message id.", delete_after=10)
        reactions = message.reactions
        winner = None
        # goes trough all reactions to find the right one and then randomly chooses a winner
        for reaction in reactions:
            if reaction.emoji == GIVEAWAY_EMOTE:
                winner = choice(await reaction.users().flatten())
        if winner is None:
            return await ctx.send(content="I couldn't determine a winner.", delete_after=10)
        else:
            return await ctx.send(content=f"{GIVEAWAY_EMOTE} {winner.mention} is the new winner! Congratulations!")

    @reroll_giveaways.error
    async def reroll_error(self, ctx, error):
        # error handler
        if isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send("Please make sure that I have the `embed links` permission.")
        elif isinstance(error, commands.CheckFailure):
            role = discord.utils.get(ctx.guild.roles, name="Giveaways")
            if role is not None:
                return
            if ctx.author.permissions_in(ctx.channel).manage_roles or \
                    ctx.author.permissions_in(ctx.channel).manage_server:
                await ctx.send("Please create a role called `Giveaways` and give it to everyone who should be able"
                               " to host and reroll giveaways.")
            else:
                return
