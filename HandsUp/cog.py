from typing import Optional

from discord import app_commands
from discord.ext import commands
import discord

import re

from HandsUp.tool import Host
import HandsUp.tool as tool
import API.api as API
import common



class HandsUp(commands.Cog):
    def __init__(self,bot)->None:
        self.bot = bot
        self.description = 'Support for team activities'


    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['c','join'],
        brief = 'Join a mogi.',
        usage = '!c [@mention1 @mention2..] <hour1 hour2...>'
    )
    @app_commands.describe(members = '@mention1 @mention2...')
    @app_commands.describe(hours = 'hour1 hour2...')
    async def can(
        self,
        ctx:commands.Context,
        members:commands.Greedy[discord.Member] = [],
        *,
        hours:Optional[str] = None,
        )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        if hours is None:
            await ctx.send('You need to choose the time.')
            return
        hours:list[str] = re.findall(r'[0-9]+',hours)
        if len(hours) == 0:
            await ctx.send('You need to choose the time.')
            return
        msg,call,embed = tool.participate(
            ctx,hours,(list(set(members)) or [ctx.author]),action='c'
        )
        old_msg = await tool.fetch_war_msg(ctx.channel)
        await tool.set_hours(ctx,hours,list(set(members)) or [ctx.author])
        await ctx.send(msg,embed=embed)
        if old_msg is not None:
            await old_msg.delete()
        if call is not None:
            await ctx.send(call)
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['t','maybe','rc','sub'],
        brief = 'Tentatively join a mogi.',
        usage = '!t [@mention1 @mention2..] <hour1 hour2...>'
    )
    @app_commands.describe(members = '@mention1 @mention2...')
    @app_commands.describe(hours = 'hour1 hour2...')
    async def tentative(
        self,
        ctx:commands.Context,
        members:commands.Greedy[discord.Member] = [],
        *,
        hours:Optional[str] = None,
        )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        if hours is None:
            await ctx.send('You need to choose the time.')
            return
        hours:list[str] = re.findall(r'[0-9]+',hours)
        if len(hours) == 0:
            await ctx.send('You need to choose the time.')
            return
        msg,_,embed = tool.participate(
            ctx,hours,(list(set(members)) or [ctx.author]),action='t'
        )
        old_msg = await tool.fetch_war_msg(ctx.channel)
        await tool.set_hours(ctx,hours,list(set(members)) or [ctx.author])
        await ctx.send(msg,embed=embed)
        if old_msg is not None:
            await old_msg.delete()
        return




    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['d','dr'],
        brief = 'Drop from a mogi',
        usage = '!d [@mention1 @mention2..] <hour1 hour2...>'
    )
    async def drop(
        self,
        ctx:commands.Context,
        members:commands.Greedy[discord.Member] = [],
        *,
        hours:Optional[str] = None,
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        if hours is None:
            await ctx.send('You need to choose the time.')
            return
        hours:list[str] = re.findall(r'[0-9]+',hours)
        if len(hours) == 0:
            await ctx.send('You need to choose the time.')
            return
        msg,embed = tool.drop_mogi(ctx,hours,list(set(members))or[ctx.author])
        old_msg = await tool.fetch_war_msg(ctx.channel)
        await tool.drop_hours(ctx,hours,list(set(members))or[ctx.author])
        await ctx.send(msg,embed=embed)
        if old_msg is not None:
            await old_msg.delete()
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases=['cle','refresh'],
        brief = 'Clear war list',
        usage = '!clear'
    )
    async def clear(self,ctx:commands.Context)->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        details = API.get_details(ctx.guild.id)
        hours = details['recruit'].keys()
        await tool.clear_hours(ctx, hours)
        details['recruit'] = {}
        API.post_details(ctx.guild.id, details)
        old_msg = await tool.fetch_war_msg(ctx.channel)
        if old_msg is not None:
            embed = old_msg.embeds[0]
            embed.title = '**6v6 War List**  (cleared)'
            await old_msg.edit(embed=embed)
        await ctx.send('Successfully cleared.')
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['clist','participants','now'],
        brief = 'Show war list',
        usage = '!now'
    )
    async def warlist(self, ctx:commands.Context)->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        details = API.get_details(ctx.guild.id)
        if details is None:
            await ctx.send('No one joins a mogi.')
            return
        old_msg = await tool.fetch_war_msg(ctx.channel)
        embed = tool.create_war_embed(details['recruit'])
        msg = None
        if embed is None:
            msg = 'No one joins a mogi.'
        await ctx.send(msg,embed=embed)
        if old_msg is not None and msg is None:
            await old_msg.delete()
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['m','mk'],
        brief = 'Make #mkmg template for twitter',
        usage = "!mkmg [hour] ['h' (host)]"
    )
    @app_commands.choices(host =[
        app_commands.Choice(name='Yes',value='h'),
        app_commands.Choice(name='No',value='_')])
    async def mkmg(
        self,
        ctx:commands.Context,
        hour:Optional[str] = None,
        host:Host = False,
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        msg,embed = await tool.mkmg_template(ctx, hour, host)
        await ctx.send(msg,embed=embed)
        return




async def setup(bot)->None:
    await bot.add_cog(HandsUp(bot))




