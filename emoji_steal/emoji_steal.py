import re
import aiohttp
from redbot.core import commands
import discord

class EmojiSteal:
    def __init__(self, bot):
        self.bot = bot
     
    @commands.command(name="emotesteal", aliases=["esteal", "emoteupload", "eupload"])
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    async def create_emote(self, ctx, emoji: EmojiConverter=None, name=None):
        """Uploads a custom emoji to your server."""
        if emoji is None:
            return await ctx.send("Make sure that you specified a valid emoji. This can either be a link or any other"
                                  " custom emoji.\n**Note:** Make sure that the emoji is static because otherwise"
                                  " I will not be able to upload it.")
        if name is None:
            return await ctx.send("Make sure that you specified a valid name. This name will be used for the the emoji."
                                  )
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji,
                                                        reason=f"Custom emoji uploaded by {ctx.author.id}")
            return await ctx.send(f"Successfully uploaded the emoji! {emoji}")
        except Exception as e:
            print(e)
            return await ctx.send("Something didn't go quite right. Please make sure that you haven't already uploaded"
                                  " 50 custom emotes!")
                                  
    async def __error(self, ctx, error):
        # error handler
        if isinstance(error, commands.BadArgument):
            print(error)
            await ctx.send(f"Please make sure you supplied the right arguments. For more information please use the "
                           f"command {ctx.prefix}help {ctx.command}")
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return
        elif isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return
        elif isinstance(error, ValueError):
            await ctx.send(f"Please make sure you supplied the right arguments. For more information please use the "
                           f"command {ctx.prefix}help {ctx.command}")
            return
        elif isinstance(error, commands.CommandError):
            self.error_handler(error)
            await ctx.send("Something didn't go quite right.")
            
    @staticmethod
    def error_handler(error):
        print("An error occurred:")
        traceback.print_exception(type(error), error, error.__traceback__)
        return False
        
class EmojiConverter(commands.Converter):
    async def convert(self, ctx, emoji):
        is_link_ = self.is_link(emoji)
        if not is_link_:
            base_link = "https://cdn.discordapp.com/emojis"
            emoji_id = self.get_emoji_id(emoji)
            if not emoji_id: return None
            link = f"{base_link}/{emoji_id}.png"
        else:
            link = emoji
        byte_emoji = await self.get_emoji(link)
        return byte_emoji

    @staticmethod
    def get_emoji_id(emoji):
        emoji_parts = emoji.split(":")
        if emoji_parts[0] == "<a": return False
        emoji_id = emoji_parts[1]
        return emoji_id

    @staticmethod
    def is_link(emoji):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, emoji)

    @staticmethod
    async def get_emoji(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as result:
                return await result.read()
