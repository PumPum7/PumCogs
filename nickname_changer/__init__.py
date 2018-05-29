
from .nickname_changer import NameChanger


def setup(bot):
  bot.add_cog(NameChanger(bot))
