from discord import app_commands
from discord.ext import commands
import discord

import Vote.tool as tool
import common



class Vote(commands.Cog):
    def __init__(self,bot)->None:
        self.bot = bot


    @common.is_allowed_guild()
    @app_commands.command()
    @app_commands.describe(
        target = 'Role',
        date = 'ex: 2023/1/1',
    )
    async def start_voting(
        self,
        interaction:discord.Interaction,
        target:discord.Role,
        enemy:str,
        time:int,
        date:str = '',
        )->None:
        await tool.vote_message(interaction, target, enemy, time, date)
        return



async def setup(bot)->None:
    await bot.add_cog(Vote(bot))