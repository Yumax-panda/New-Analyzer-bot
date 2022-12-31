from typing import Optional

from discord.ext import commands
import discord

import re
import numpy as np
import pandas as pd

from common import ColoredEmbed
import common
import API.api as API
import API.lounge_api as lounge_api
import plotting


DETAIL_URL = 'https://www.mk8dx-lounge.com/PlayerDetails/'
TABLE_URL = 'https://www.mk8dx-lounge.com/TableDetails/'


def get_fc(txt:str)->Optional[str]:
    d_txt = re.sub(r'\D','',txt)
    if len(d_txt) != 12:
        return None
    return f'{d_txt[:4]}-{d_txt[4:8]}-{d_txt[8:]}'



def get_discord_id(txt:str)->Optional[int]:
    d_txt = re.sub(r'\D','',txt)
    if len(d_txt) >= 17 and len(d_txt) <=19:
        return int(d_txt)
    return None



def maybe_param(
    txt:str,
    guild:Optional[discord.Guild] = None,
    )->tuple[Optional[str],Optional[int],Optional[str]]:
    """
    return 3 params
    name,discord_id,fc
    only 1 parameter is not None.
    """
    if guild is not None:
        member = guild.get_member_named(txt)
        if member is not None:
            return None,member.id,None
    d_id = get_discord_id(txt)
    fc = get_fc(txt)
    if d_id is not None:
        return None,d_id,None
    if fc is not None:
        return None,None,fc
    return txt,None,None



async def current_stats(
    name:str,
    season:int,
)->tuple[Optional[str],Optional[ColoredEmbed],Optional[discord.File]]:
    """
    name:Lounge-name
    only for season >=4
    """
    details = await lounge_api.get_player_info(
        name= name,
        season=season,
    )
    if details is None:
        return 'Not Found',None,None
    mmr_history = [m['newMmr'] for m in details['mmrChanges'][::-1]]
    if len(mmr_history) <= 1:
        return f'No match in season {season}', None, None
    buffer = await plotting.create_plot(mmr_history,season)
    file = discord.File(fp=buffer,filename='stats.png')
    embed = ColoredEmbed(
        title = f'S{season} Stats',
        description = f'[{details["name"]}]({DETAIL_URL}{details["playerId"]}?season={season})',
        mmr = details['mmr'],
        season= season
    )
    wins = [table for table in details['mmrChanges'] if table['mmrDelta'] >0]
    loses = [table for table in details['mmrChanges'] if table['mmrDelta'] < 0]
    scores = list(filter(lambda x: x.get('score') is not None, details['mmrChanges']))
    top_score_match = max(scores,key=lambda x: x['score'])
    embed.add_field(name='Rank',value=details['overallRank'])
    embed.add_field(name='MMR',value=details['mmr'])
    if 'maxMmr' in details.keys():
        embed.add_field(name='Peak MMR',value=details['maxMmr'])
    else:
        embed.add_field(name='Peak MMR',value = 'N/A')
    embed.add_field(name='Win Rate',value=f'{100*details["winRate"]:.1f}')
    embed.add_field(name='W-L',value=f'{len(wins)} - {len(loses)}')
    embed.add_field(name='+/-',value=mmr_history[-1]-mmr_history[0])
    embed.add_field(name='Avg. Score',value=f'{details["averageScore"]:.1f}')
    embed.add_field(name='Top Score',value=f'[{top_score_match["score"]}]({TABLE_URL}{top_score_match["changeId"]})')
    embed.add_field(name='Partner Avg.',value=f'{details["partnerAverage"]:.1f}')
    embed.add_field(name='Events Played',value=details["eventsPlayed"])
    embed.add_field(name='Largest Gain',value=f'[{details["largestGain"]}]({TABLE_URL}{details["largestGainTableId"]})')
    embed.add_field(name='Largest Loss',value=f'[{details["largestLoss"]}]({TABLE_URL}{details["largestLossTableId"]})')
    embed.add_field(name='Average MMR',value=f'{sum(mmr_history)/len(mmr_history):.1f}')
    embed.add_field(name='Base MMR',value=mmr_history[0])
    embed.set_image(url='attachment://stats.png')
    return None,embed,file



async def prev_stats(
    name:str,
    season:int,
    )->tuple[Optional[str],Optional[ColoredEmbed]]:
    """
    for season 1~4 stats
    """
    prev_detail = API.get_prev_player(season,name)
    if prev_detail is None:
        return 'Not Found',None
    embed = ColoredEmbed(
        title = f'Season {season} Stats',
        description = name,
        mmr= prev_detail['mmr'],
        season= season
    )
    embed.add_field(name='Rank',value=prev_detail['overallRank'])
    embed.add_field(name='MMR',value=prev_detail['mmr'])
    if np.isnan(prev_detail['maxMmr']):
        embed.add_field(name='Peak MMR',value='N/A')
    else:
        embed.add_field(name='Peak MMR',value=int(prev_detail['maxMmr']))
    embed.add_field(name='Win Rate',value=prev_detail['winRate'])
    embed.add_field(name='W-L(Last 10)',value=prev_detail['winLossLastTen'])
    embed.add_field(name='Gain/Loss(Last 10)',value=int(prev_detail['gainLossLastTen']))
    embed.add_field(name='Events Played',value=int(prev_detail['eventsPlayed']))
    if prev_detail['largestGain'] == '-':
        embed.add_field(name='Largest Gain',value='N/A')
    else:
        embed.add_field(name='Largest Gain',value=prev_detail['largestGain'])
    if prev_detail['largestLoss'] == '-':
        embed.add_field(name='Largest Loss',value='N/A')
    else:
        embed.add_field(name='Largest Loss',value=prev_detail['largestLoss'])
    return None,embed



async def calc_team_mmr(
    roles:list[discord.Role],
    member_ids:list[int],
    season:int
    )->str:
    players = await API.get_players(
        discord_ids= member_ids,
        season = season,
        search_linked_id= True,
        remove_None= True
    )
    if len(players) == 0:
        return 'No player found'
    df = pd.DataFrame(players).drop_duplicates(subset='name').sort_values('mmr',ascending=False)
    ave_mmr = df['mmr'].mean()
    new_list = df.to_dict('records')
    rank = common.getRank(int(ave_mmr),season)
    txt = f'**Team MMR: {ave_mmr:.1f}**   (Season {season})\n\n'
    txt += f"**Role**   {' '.join([role.mention for role in roles])}\n"
    for i,player in enumerate(new_list):
        txt +=f'{str(i+1).rjust(3)}: {player["name"]} (MMR: {player["mmr"]})\n'
    txt += f'\n**Rank** {rank}'
    return txt



async def get_mmr(
    ctx:commands.Context,
    season:int,
    name:Optional[str] = None
    )->tuple[Optional[str],Optional[ColoredEmbed]]:
    if name is None:
        player = await API.get_player(
            discord_id=ctx.author.id,
            search_linked_id=True,
            season =season,
        )
    else:
        name,d_id,fc = maybe_param(name,ctx.guild)
        player = await API.get_player(name=name,discord_id=d_id,fc=fc,season=season)
    if player is None:
        return 'Not Found',None
    mmr = player.get('mmr')
    if mmr is None:
        return 'Not Found',None
    embed = ColoredEmbed(
        mmr = mmr,
        season= season,
        set_rank_image=False,
        title = f'Season {season}',
        description= f'{player["name"]}  (MMR: {mmr})',
        url = f'{DETAIL_URL}{player["id"]}?season={season}',
    )
    return None,embed


