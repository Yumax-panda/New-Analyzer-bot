from discord import app_commands
from discord.ext import commands
import discord

import API.api as API
import common

class Setting(commands.Cog):
    def __init__(self,bot)->None:
        self.bot = bot
        self.description = 'Manage settings'


    @commands.is_owner()
    @commands.command(hidden=True)
    async def sync_server(self,ctx:commands.Context)->None:
        await self.bot.tree.sync(guild=discord.Object(id=ctx.guild.id))
        await (await ctx.send('synced')).delete(delay=10)
        return



    @commands.is_owner()
    @commands.command(hidden=True)
    async def sync(self,ctx:commands.Context)->None:
        await self.bot.tree.sync()
        await (await ctx.send('synced')).delete(delay=10)
        return



    @commands.is_owner()
    @commands.command(aliases=['all'],hidden=True)
    async def sync_all(self,ctx):
        guild_list = self.bot.guilds
        ret = 0
        for guild in guild_list:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1
        await ctx.send(f'Synced the tree to {ret}/{len(guild_list)} servers.')



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases=['rname'],
        brief = 'Register team name',
        usage = '!rname <team name>'
    )
    async def register_name(
        self,
        ctx:commands.Context,
        name:str
    )->None:
        if len(name) == 0:
            await (await ctx.send('Empty name is invalid.')).delete(delay=10)
            return
        API.record_team_name(guild_id=ctx.guild.id, team_name=name)
        await ctx.send(f'Registered:  **{name}**')
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases=['dname','delname'],
        brief = 'Delete team name',
        usage = '!dname'
    )
    async def delete_name(
        self,
        ctx:commands.Context,
    )->None:
        API.delete_team_name(guild_id=ctx.guild.id)
        await ctx.send('Successfully deleted.')
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['connect'],
        brief = 'Link to your lounge account',
        usage = '!link <lounge name>'
    )
    @app_commands.describe(name = 'Lounge name')
    async def link(self,ctx:commands.Context,name:str)->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        player = await API.get_player(name=name,search_linked_id=False)
        if player is None:
            await ctx.send(f'Player named **{name}** is not Found.')
            return
        API.record_lounge_id(ctx.author.id,player['discordId'])
        await ctx.send(f'Successfully linked to **{player["name"]}**')
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        brief = 'Show team name',
        usage = '!teamname'
    )
    async def teamname(self,ctx:commands.Context)->None:
        await ctx.send(API.get_team_name(ctx.guild.id) or ctx.guild.name)
        return


async def setup(bot):
    await bot.add_cog(Setting(bot))