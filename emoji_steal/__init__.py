from .emoji_steal import EmojiSteal

def setup(bot):
    bot.add_cog(EmojiSteal(bot))
