from typing import Optional,Literal,Union

from discord.ext import commands
import discord

from math import floor
import pandas as pd

from common import ColoredEmbed
import common
import API.api as API




async def set_hours(
    ctx:commands.Context,
    hours:list[Union[int,str]],
    members:list[discord.Member]
)->None:
    for hour in hours:
        role = discord.utils.get(ctx.guild.roles,name = str(hour))
        if role is None:
            role = await ctx.guild.create_role(name=str(hour),mentionable= True)
        for member in members:
            await member.add_roles(role)
    return


async def drop_hours(
    ctx:commands.Context,
    hours:list[Union[int,str]],
    members:list[discord.Member]
)->None:
    for hour in hours:
        role = discord.utils.get(ctx.guild.roles,name=str(hour))
        if role is None:
            continue
        for member in members:
            await member.remove_roles(role)
    return



async def clear_hours(
    ctx:commands.Context,
    hours:list[Union[int,str]],
)->None:
    for hour in hours:
        role = discord.utils.get(ctx.guild.roles,name = str(hour))
        if role is None:
            continue
        await role.delete()
    return


def create_war_embed(params:dict)->Optional[discord.Embed]:
    if len(params) == 0:
        return None
    hours = [str(hour) for hour in params.keys()]
    hours.sort(key=lambda x:int(x))
    embed = discord.Embed(
        title = '**6v6 War List**',
        color = discord.Colour.blue()
    )
    embed.set_footer(text="仮 = Tentative")
    for hour in hours:
        member_msg = '-'
        time_name = f"{hour}@{6-len(params[hour]['c'])}"
        if len(params[hour]['c']) != 0:
            mention_list = [f'<@{id}>'for id in params[hour]['c']]
            member_msg = ','.join(mention_list)
        if len(params[hour]['t']) !=0:
            time_name += f"({len(params[hour]['t'])})"
            t_mention = [f'<@{id}>'for id in params[hour]['t']]
            member_msg += f"({','.join(t_mention)})"
        embed.add_field(
            name=time_name,
            value = f'> {member_msg}',
            inline=False
        )
    return embed



def participate(
    ctx:commands.Context,
    hours:list[Union[int,str]],
    members:list[discord.Member],
    action:Literal['c','t']
)->tuple[str,Optional[str],discord.Embed]:
    """
    expected len(hours) > 0
    action: 'c'-> can, 't'->tentatively
    """
    hours:list[str] = list({str(h)for h in hours})
    hours.sort(key=lambda x:int(x))
    x,y = 'c','t'
    if action == 't':
        x,y = 't','c'
    details = API.get_details(ctx.guild.id)
    recruit = details['recruit'].copy()
    ids = [member.id for member in members]
    filled_hours:list[str] = []
    for hour in hours:
        recruit_hour = recruit.get(hour)
        if recruit_hour is None:
            recruit[hour] = {x:ids.copy(),y:[]}
        else:
            recruit_hour[x] = list(set(recruit_hour[x])|set(ids))
            recruit_hour[y] = list(set(recruit_hour[y])-set(ids))
        if len(recruit[hour]['c']) >=6 and action=='c':
            filled_hours.append(hour)
    details['recruit'] = recruit.copy()
    API.post_details(ctx.guild.id,details)
    call = None
    msg = f"{', '.join(member.name for member in members)} have {'tentatively ' if action=='t' else ''}joined **{', '.join(hours)}**"
    if len(filled_hours) >0:
        call_ids:set = set([])
        for hour in filled_hours:
            call_ids = call_ids | set(recruit[hour]['c'])
        members = [ctx.guild.get_member(id) for id in list(call_ids) if ctx.guild.get_member(id) is not None]
        call = f"**{', '.join(filled_hours)}**{', '.join([member.mention for member in members])}"
    return msg, call,create_war_embed(recruit)



def drop_mogi(
    ctx:commands.Context,
    hours:list[Union[int,str]],
    members:list[discord.Member],
)->tuple[str,Optional[discord.Embed]]:
    """
    expected len(hours) > 0
    """
    hours:list[str] = list({str(h)for h in hours})
    hours.sort(key=lambda x:int(x))
    dropped_hours:list[str] = []
    details = API.get_details(ctx.guild.id)
    recruit:dict = details['recruit'].copy()
    ids = [member.id for member in members]
    for hour in hours:
        d_hour = recruit.get(hour)
        if d_hour is None:
            continue
        d_hour['c'] = list(set(d_hour['c'])-set(ids))
        d_hour['t'] = list(set(d_hour['t'])-set(ids))
        dropped_hours.append(hour)
    if len(dropped_hours) == 0:
        return 'You don\'t join at the time.',None
    details['recruit'] = recruit.copy()
    API.post_details(ctx.guild.id,details)
    embed = create_war_embed(recruit)
    msg = f"{', '.join([member.name for member in members])} has dropped from **{', '.join(dropped_hours)}**"
    return msg,embed



class Host(commands.Converter):
    async def convert(self,ctx,argument)->bool:
        return argument.lower() in ['host', 'h']



async def mkmg_template(
    ctx:commands.Context,
    hour:Optional[str] = None,
    host:bool = False,
)->tuple[str,Optional[ColoredEmbed]]:
    name = API.get_team_name(ctx.guild.id) or ctx.guild.name
    players = []
    recruit = API.get_details(ctx.guild.id)['recruit']
    if hour is not None:
        if hour in recruit.keys():
            players = await API.get_players(
                discord_ids=recruit[hour]['c'],
                remove_None= True,
            )
    ave_mmr = None
    rank = None
    if len(players) > 0:
        df = pd.DataFrame(players).drop_duplicates(subset='name').sort_values('mmr',ascending=False)
        ave_mmr = df['mmr'].mean()
        players = df.to_dict('records')
        rank = common.getRank(int(ave_mmr))
    ave_txt = ''
    if ave_mmr is not None:
        ave_txt = f'平均MMR {floor(ave_mmr/500)*500}程度\n'
    msg = f'{hour if hour is not None else ""} 交流戦お相手募集します\n'
    msg += f'こちら{name}\n' + ave_txt
    msg += f'{"主催持てます" if host else "主催持っていただきたいです"}\n'
    msg +=  'Sorry, Japanese clan only\n#mkmg'
    embed = None
    if ave_mmr is not None:
        embed = ColoredEmbed(int(ave_mmr))
        embed.title = f'@{hour} Lineup'
        description = f'**Avg.MMR: {ave_mmr:.1f}**\n\n'
        for i,player in enumerate(players):
            description +=f'{str(i+1)}. {player["name"]} (MMR: {player["mmr"]})\n'
        description += f'\n**Rank** {rank}'
        embed.description = description
    return msg,embed



async def fetch_war_msg(
    channel:discord.TextChannel,
    limit:int = 15
    )->Optional[discord.Message]:
    async for message in channel.history(limit=limit):
        if len(message.embeds) == 0:
            continue
        if message.embeds[0].title != '**6v6 War List**':
            continue
        else:
            return message
    return None
