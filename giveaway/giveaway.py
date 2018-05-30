from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
import discord
import datetime
from random import choice

DATE_STRING = "{days}d{hours}h{minutes}m"
GIVEAWAY_EMOTE = "🎉"


class Giveaway:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="giveaway")
    @commands.guild_only()
    @commands.has_role("Giveaways")
    @commands.bot_has_permissions(add_reactions=True)
    async def cmd_giveaway(self, ctx, time: str=None, *, prize: str=None):
        # check the inputs
        end_time = self.end_time(time)
        if end_time is None:
            return await ctx.send("Please follow the format: `{days}d{hours}h{minutes}m`. You can also only use "
                                  "one/two of the three possible time units.")
        if prize is None:
            return await ctx.send(f"Please follow the format: `{ctx.prefix}{ctx.command} {DATE_STRING} {'{prize}'}`")
        # send the giveaway embed
        giveaway_embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{GIVEAWAY_EMOTE} GIVEAWAY! {GIVEAWAY_EMOTE}",
            description=f"Prize: {prize}"
        )
        giveaway_embed.add_field(
            name="End date:",
            value=f"{str(end_time).split('.')[0]}"
        )
        giveaway_embed.set_footer(text=f"Click on the {GIVEAWAY_EMOTE} to enter!")
        msg = await ctx.send(embed=giveaway_embed)
        await msg.add_reaction(f"{GIVEAWAY_EMOTE}")
        # set up the scheduler
        scheduler = AsyncIOScheduler()
        scheduler.configure(timezone=end_time.tzname())
        scheduler.add_job(func=self.giveaway_embed, trigger="date", run_date=end_time, args=(prize, ctx.channel, msg.id)
                          )
        scheduler.start()

    def end_time(self, time):
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
        if unit in time:
            new_tm = time.split(unit)
            return new_tm
        else:
            return None

    @staticmethod
    async def giveaway_embed(prize, channel: discord.TextChannel, msg_id: int):
        message = await channel.get_message(msg_id)
        if message is None:
            return await channel.send(content="I couldn't determine a winner.")
        reactions = message.reactions
        winner = None
        await message.remove_reaction(member=message.author, emoji=f"{GIVEAWAY_EMOTE}")
        for reaction in reactions:
            if reaction.emoji == f"{GIVEAWAY_EMOTE}":
                winner = choice(await reaction.users().flatten())
        if winner is None:
            return await message.edit(content="I couldn't determine a winner.")
        embed = discord.Embed(
            color=discord.Color.green(),
            title=f"{GIVEAWAY_EMOTE} Giveaway! {GIVEAWAY_EMOTE}",
            description=f"{winner.mention} has won the giveaway! Congratulations!\n**Prize:** {prize}"
        )
        await message.edit(embed=embed)

    @cmd_giveaway.error
    async def error_handler_giveaway(self, ctx, error):
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

    @commands.command(name="reroll")
    @commands.guild_only()
    @commands.has_role("Giveaways")
    @commands.bot_has_permissions(embed_links=True)
    async def reroll_giveaways(self, ctx, message_id=None):
        channel = ctx.channel
        message = None
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
        for reaction in reactions:
            if reaction.emoji == GIVEAWAY_EMOTE:
                winner = choice(await reaction.users().flatten())
        if winner is None:
            return await ctx.send(content="I couldn't determine a winner.", delete_after=10)
        else:
            return await ctx.send(content=f"{GIVEAWAY_EMOTE} {winner.mention} is the new winner! Congratulations!")

    @reroll_giveaways.error
    async def reroll_error(self, ctx, error):
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
