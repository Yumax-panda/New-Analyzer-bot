from typing import Optional,Any,Union

from discord import (
    ButtonStyle,
    Role,
    Interaction,
    Member,
    Message,
    User,
    WebhookMessage
)
import discord

from datetime import datetime,timedelta
from zoneinfo import ZoneInfo

import re

C_EMOJI = '\N{REGIONAL INDICATOR SYMBOL LETTER C}'
S_EMOJI = '\N{REGIONAL INDICATOR SYMBOL LETTER S}'
D_EMOJI = '\N{REGIONAL INDICATOR SYMBOL LETTER D}'

def get(l:list[Any],i:int)->Optional[Any]:
    if len(l) <= i: return None
    return l[i]



def to_datetime(txt:str)->datetime:
    """change txt into datetime (JST)

    Args:
        txt (str): String with numbers

    Returns:
        datetime: JST datetime (aware)
    """
    now = datetime.now(ZoneInfo('Asia/Tokyo'))
    nums = list(map(int,re.findall(r'[0-9]+',txt)))[:3][::-1]
    return datetime(
        year= get(nums,2) or now.year,
        month= get(nums,1) or now.month,
        day= get(nums,0) or now.day,
        tzinfo=ZoneInfo('Asia/Tokyo')
    )


async def get_reacted_user(
    message:Message,
    role:Role,
    )->tuple[list[Union[Member,User]],dict[str,list[Union[Member,User]]]]:
    """get reacted user (member)

    Args:
        message (Message):

        Role    (Role):

    Returns:
        list[Union[Member,User]]           : Reacted users

        dict[str,list[Union[Member,User]]] : {Emoji:[Reacted users]}
    """
    ret = {}
    reacted = []
    reactions = message.reactions
    for reaction in reactions:
        temp = [user async for user in reaction.users()]
        ret[str(reaction)] = list(set(temp.copy()) & set(role.members))
        reacted += temp
    return list(set(reacted) & set(role.members)),ret



class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Result',style=ButtonStyle.green,custom_id='result')
    async def tally(self,interaction:Interaction,button:discord.ui.button):
        await interaction.response.defer(thinking=True)
        msg  = await interaction.message.fetch()
        role_ids = msg.raw_role_mentions
        role = None
        if role_ids:
            role = interaction.guild.get_role(role_ids[0])
        if role is None:
            await interaction.followup.send('This role is not available.')
            return
        voted,react_dict = await get_reacted_user(msg,role)
        can = react_dict[C_EMOJI]
        sub = react_dict[S_EMOJI]
        not_voted = list(set(role.members) - set(voted))
        txt = '\n'.join(msg.content.split('\n')[:2]) + '\n'
        c_name = [member.name for member in can]
        s_name = [f'({member.name})' for member in sub]
        txt += f"\n> **@{6-len(c_name)} {f'({len(s_name)})' if s_name else ''}**\n"
        txt += ', '.join(c_name + s_name) + '\n'
        if not_voted:
            txt += '\n> **Unanswered**\n'+', '.join([member.name for member in not_voted])
        await interaction.followup.send(txt)
        return

    @discord.ui.button(label='Mention',style=ButtonStyle.red,custom_id='mention')
    async def mention_members(self,interaction:Interaction,button:discord.ui.button):
        await interaction.response.defer(thinking=True)
        msg  = await interaction.message.fetch()
        role_ids = msg.raw_role_mentions
        role = None
        if role_ids:
            role = interaction.guild.get_role(role_ids[0])
        if role is None:
            await interaction.followup.send('This role is not available.')
            return
        voted_member,_ = await get_reacted_user(msg,role)
        not_voted_member = list(set(role.members) - set(voted_member))
        if not_voted_member:
            await interaction.followup.send(', '.join([member.mention for member in not_voted_member]))
            return
        await interaction.followup.send('Everybody has already voted.')

    @discord.ui.button(label='Stop',style=ButtonStyle.grey,custom_id='stop')
    async def stop(self,interaction:Interaction,button:discord.ui.button):
        await interaction.response.defer(thinking=True)
        await interaction.message.delete()
        await interaction.followup.send('Finished')
        return



async def vote_message(
    interaction:Interaction,
    target:Role,
    enemy:str,
    time:int,
    date:str = ''
)->None:
    await interaction.response.defer(thinking=True)
    dt = to_datetime(date) + timedelta(days=time//24,hours=time%24)
    txt = f'**vs.{enemy}**   <t:{int(dt.timestamp())}:F>\n'
    txt += f'Voters  {target.mention}\n'
    txt += f'can:{C_EMOJI}  sub:{S_EMOJI}  drop:{D_EMOJI}'
    msg :WebhookMessage = await interaction.followup.send(txt,view=VoteView())
    for emoji in [C_EMOJI,S_EMOJI,D_EMOJI]:
        await msg.add_reaction(emoji)
    return
