from .nicknamechanger import NicknameChanger

def setup(bot):
  bot.add_cog(NicknameChanger(bot))
