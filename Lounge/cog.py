from typing import Optional

from discord import app_commands
from discord.ext import commands
import discord

import os
import re
import json
import asyncio
import API.lounge_api as lapi
import pandas as pd

import common
import Lounge.tool as tool
import API.api as API

config = json.loads(os.environ['CONFIG'])

DETAIL_URL = 'https://www.mk8dx-lounge.com/PlayerDetails/'
MKC_URL = 'https://www.mariokartcentral.com/mkc/registry/players/'
_RE = re.compile(r'[0-9]{4}\-[0-9]{4}\-[0-9]{4}')


class Lounge(commands.Cog):
    def __init__(self,bot)->None:
        self.bot = bot



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['show'],
        brief = 'Show Lounge Stats',
        usage = '!show [season] [name]'
    )
    async def stats(
        self,
        ctx:commands.Context,
        season:Optional[commands.Range[int,1,config['season']]] = config['season'],
        *,
        name:Optional[str] = None,
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        err_msg = None
        img_file = None
        if name is None:
            player = await API.get_player(
                discord_id=ctx.author.id,
                search_linked_id=True,
                season=season
            )
        else:
            name,d_id,fc = tool.maybe_param(name,ctx.guild)
            player = await API.get_player(name=name,discord_id=d_id,fc=fc)
        if player is None and season >=5:
            await (await ctx.send('Not Found')).delete(delay=10)
            return
        elif player is None:
            player = {'name':name}
        if season >= 5:
            err_msg,embed,img_file = await tool.current_stats(player['name'],season)
        elif season == 4:
            flag:bool = False
            err_msg,current_embed,img_file = await tool.current_stats(player['name'],4)
            err_msg,prev_embed = await tool.prev_stats(player['name'],4)
            if prev_embed is not None:
                flag = True
                prev_embed.title = 'Season 4 Stats (Previous)'
                await ctx.send(embed=prev_embed)
            if current_embed is not None:
                flag = True
                await ctx.send(embed=current_embed,file=img_file)
            if not flag:
                await(await ctx.send('Not Found')).delete(delay=10)
            return
        else:
            err_msg,embed = await tool.prev_stats(player['name'],season)

        if err_msg is not None:
            await (await ctx.send(err_msg)).delete(delay=10)
            return
        await ctx.send(embed= embed,file = img_file)
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        name = 'team',
        aliases=['group'],
        brief = 'Show team MMR',
        usage = '!team <@role1 @role2...>'
    )
    @app_commands.describe(roles='@Role1 @Role2...')
    async def team_mmr(
        self,
        ctx:commands.Context,
        roles:commands.Greedy[discord.Role],
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        if len(roles) == 0:
            await(await ctx.send('No roles specified')).delete(delay=10)
            return
        member_id = []
        for role in roles:
            member_id = list(set(member_id) | {member.id for member in role.members})
        txt = await tool.calc_team_mmr(roles, member_id,season=config['season'])
        await ctx.send(txt)
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['friend'],
        brief = 'Show Friend Code',
        usage = '!fc [name or id]'
    )
    async def fc(
        self,
        ctx:commands.Context,
        name:Optional[str]=None
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        if name is None:
            player = await API.get_player(
                discord_id=ctx.author.id,
                search_linked_id=True,
            )
        else:
            name,d_id,fc = tool.maybe_param(name,ctx.guild)
            player = await API.get_player(name=name,discord_id=d_id,fc=fc)
        if player is None:
            await (await ctx.send('Not Found')).delete(delay=10)
            return
        fc = player.get('switchFc')
        if fc is None:
            await (await ctx.send('This player\'s fc is not registered.')).delete(delay=10)
            return
        else:
            await ctx.send(fc)
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        brief = 'Show MMR',
        usage = '!mmr [season] [name]'
    )
    async def mmr(
        self,
        ctx:commands.Context,
        name:Optional[str] = None,
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        err_msg,embed = await tool.get_mmr(ctx,season=config['season'],name=name)
        if err_msg is not None:
            await (await ctx.send(err_msg)).delete(delay=10)
            return
        await ctx.send(embed=embed)
        return



    @common.is_allowed_guild()
    @app_commands.command(description= 'Show player name')
    @app_commands.describe(name='name or ID')
    async def who(
        self,
        interaction:discord.Interaction,
        name:str
    )->None:
        name,d_id,fc = tool.maybe_param(name,interaction.guild)
        player = await API.get_player(name=name,discord_id=d_id,fc=fc)
        if player is None:
            await interaction.response.send_message('Not Found',ephemeral=True)
            return
        msg = f"[{player['name']}]({DETAIL_URL}{player['id']})"
        user = self.bot.get_user(int(d_id or player['discordId']))
        if user is not None:
            msg += f'   ({str(user)})'
        await interaction.response.send_message(msg,ephemeral=True)
        return

    @common.is_allowed_guild()
    @commands.hybrid_command(aliases=['fm','mkc'])
    async def from_fc(
        self,
        ctx: commands.Context,
        text: str
    ) -> None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking = True)
        fc_list: list[str] = _RE.findall(text)
        if not fc_list:
            await ctx.send('Not Found')
            return
        tasks = [asyncio.create_task(lapi.get_player(fc=fc)) for fc in fc_list]
        players = await asyncio.gather(*tasks, return_exceptions=False)
        df = pd.DataFrame([p for p in players if p is not None])
        if len(df) == 0:
            await ctx.send('Not Found')
            return

        ave = df['mmr'].mean()

        rank = common.getRank(int(ave))
        txt = f'**Average MMR: {ave:.1f}**\n\n'
        for i,player in enumerate(players):
            if player is None:
                txt +=f"N/A ({fc_list[i]})\n"
            else:
                txt +=f'[{player["name"]}]({MKC_URL}{player["registryId"]}) (MMR: {player["mmr"]})\n'
        txt += f'\n**Rank** {rank}'
        await ctx.send(txt)



async def setup(bot)->None:
    await bot.add_cog(Lounge(bot))
