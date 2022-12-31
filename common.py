from typing import Any,Optional,Union

from discord.ext import commands
import discord

import os
import json
import datetime

config = json.loads(os.environ['CONFIG'])

def is_allowed_guild():
    def predicate(ctx:commands.Context)->bool:
        try:
            if ctx.guild.id not in config['ignore_guild']:
                return True
        except AttributeError:
            return True
    return commands.check(predicate)


def getRankData(season:int=config['season'])->dict[str,dict[str,Any]]:
    if season <= 2:
        return {
            "Master": {
                "color": 0x0E0B0B,
                "url": "https://images-ext-2.discordapp.net/external/818NjPBjrnnWfyerw_2aEneujaXvbx8FqpFVDJb7QFo/%3Fv%3D1568666322577/https/cdn.glitch.com/3daabc84-e598-4559-b112-0a2f1ad29d80%252Fmaster.png"},
            "Diamond": {
                "color": 0xB6F2FF,
                "url": "https://images-ext-1.discordapp.net/external/vFN0gVHQfKiuibLwGiXLU1AyNakAvDW1Y6qAJz9OpIU/%3Fv%3D1568666334772/https/cdn.glitch.com/3daabc84-e598-4559-b112-0a2f1ad29d80%252Fdiamond.png"},
            "Platinum": {
                "color": 0xfABB8,
                "url": "https://images-ext-2.discordapp.net/external/BOV2_4s_hHzyc_k86CmwRmBlCiWATO1_hhgMEocDD8w/%3Fv%3D1568666339226/https/cdn.glitch.com/3daabc84-e598-4559-b112-0a2f1ad29d80%252Fplatinum.png"},
            "Gold": {
                "color": 0xFFD700,
                "url": "https://images-ext-1.discordapp.net/external/TNePvgcc2x0r1XVCc7YvW6ESZHD6EhyipuD8tVXddl4/%3Fv%3D1568666343936/https/cdn.glitch.com/3daabc84-e598-4559-b112-0a2f1ad29d80%252Fgold.png"},
            "Silver": {
                "color": 0x7D8396,
                "url": "https://images-ext-2.discordapp.net/external/UY9xNJ5dHt09Er_ZNqPtt5KF6FHqZbxkQrt0k6JgrrU/%3Fv%3D1568666348185/https/cdn.glitch.com/3daabc84-e598-4559-b112-0a2f1ad29d80%252Fsilver.png"},
            "Bronze": {
                "color": 0xCD7F32,
                "url": "https://images-ext-2.discordapp.net/external/lyRHPXnzii9wSXhgffi8ugSrGSQCWEYc7Bo-YVUYGc8/%3Fv%3D1568666353508/https/cdn.glitch.com/3daabc84-e598-4559-b112-0a2f1ad29d80%252Fbronze.png"},
        }
    else:
        return {
            "Grandmaster": {
                "color": 0xA3022C,
                "url": "https://i.imgur.com/EWXzu2U.png"},
            "Master": {
                "color": 0xD9E1F2,
                "url": "https://i.imgur.com/3yBab63.png"},
            "Diamond": {
                "color": 0xBDD7EE,
                "url": "https://i.imgur.com/RDlvdvA.png"},
            "Ruby":{
                "color":0xD51C5E,
                "url": "https://i.imgur.com/WU2NlJQ.png"},
            "Sapphire": {
                "color": 0x286CD3,
                "url": "https://i.imgur.com/bXEfUSV.png"},
            "Platinum": {
                "color": 0x3FABB8,
                "url": "https://i.imgur.com/8v8IjHE.png"},
            "Gold": {
                "color": 0xFFD966,
                "url": "https://i.imgur.com/6yAatOq.png"},
            "Silver": {
                "color": 0xD9D9D9,
                "url": "https://i.imgur.com/xgFyiYa.png"},
            "Bronze": {
                "color": 0xC65911,
                "url": "https://i.imgur.com/DxFLvtO.png"},
            "Iron": {
                "color": 0x817876,
                "url": "https://i.imgur.com/AYRMVEu.png"},
        }



def getRank(
    mmr:int,
    season:int = config['season'],
)->str:
    if season <= 2:
        if mmr >=9000: return "Master"
        elif mmr >= 7000: return "Diamond"
        elif mmr >= 5500: return "Platinum"
        elif mmr >= 4000: return "Gold"
        elif mmr >= 2500: return "Silver"
        else: return "Bronze"

    elif season == 3:
        if mmr >= 12500: return "Grandmaster"
        elif mmr >= 11000: return "Master"
        elif mmr >= 9500: return "Diamond"
        elif mmr >= 8000: return "Sapphire"
        elif mmr >= 6500: return "Platinum"
        elif mmr >= 5000: return "Gold"
        elif mmr >= 3500: return "Silver"
        elif mmr >= 2000: return "Bronze"
        else: return "Iron"

    elif season == 4:
        if mmr >= 14500: return "Grandmaster"
        elif mmr >= 13000: return "Master"
        elif mmr >= 11500: return "Diamond"
        elif mmr >= 10000: return "Sapphire"
        elif mmr >= 8500: return "Platinum"
        elif mmr >= 7000: return "Gold"
        elif mmr >= 5500: return "Silver"
        elif mmr >= 4000: return "Bronze"
        else: return "Iron"

    elif season == 5:
        if mmr >= 14000: return "Grandmaster"
        elif mmr >= 13000: return "Master"
        elif mmr >= 12000: return "Diamond 2"
        elif mmr >= 11000: return "Diamond 1"
        elif mmr >= 10000: return "Sapphire"
        elif mmr >= 9000: return "Platinum 2"
        elif mmr >= 8000: return "Platinum 1"
        elif mmr >= 7000: return "Gold 2"
        elif mmr >= 6000: return "Gold 1"
        elif mmr >= 5000: return "Silver 2"
        elif mmr >= 4000: return "Silver 1"
        elif mmr >= 3000: return "Bronze 2"
        elif mmr >= 2000: return "Bronze 1"
        elif mmr >= 1000: return "Iron 2"
        else: return "Iron 1"

    elif season <= 7:
        if mmr >= 15000: return "Grandmaster"
        elif mmr >= 14000: return "Master"
        elif mmr >= 13000: return "Diamond 2"
        elif mmr >= 12000: return "Diamond 1"
        elif mmr >= 11000: return "Sapphire 2"
        elif mmr >= 10000: return "Sapphire 1"
        elif mmr >= 9000: return "Platinum 2"
        elif mmr >= 8000: return "Platinum 1"
        elif mmr >= 7000: return "Gold 2"
        elif mmr >= 6000: return "Gold 1"
        elif mmr >= 5000: return "Silver 2"
        elif mmr >= 4000: return "Silver 1"
        elif mmr >= 3000:return "Bronze 2"
        elif mmr >= 2000: return "Bronze 1"
        elif mmr >= 1000:return "Iron 2"
        else:return "Iron 1"

    elif season == 8:
        if mmr >= 17000: return "Grandmaster"
        elif mmr >= 16000: return "Master"
        elif mmr >= 15000: return "Diamond 2"
        elif mmr >= 14000: return "Diamond 1"
        elif mmr >= 13000: return "Ruby 2"
        elif mmr >= 12000: return "Ruby 1"
        elif mmr >= 11000: return "Sapphire 2"
        elif mmr >= 10000: return "Sapphire 1"
        elif mmr >= 9000: return "Platinum 2"
        elif mmr >= 8000: return "Platinum 1"
        elif mmr >= 7000: return "Gold 2"
        elif mmr >= 6000: return "Gold 1"
        elif mmr >= 5000: return "Silver 2"
        elif mmr >= 4000: return "Silver 1"
        elif mmr >= 3000:return "Bronze 2"
        elif mmr >= 2000: return "Bronze 1"
        elif mmr >= 1000:return "Iron 2"
        else:return "Iron 1"



# This class is mainly used to create lounge-related embed.
class ColoredEmbed(discord.Embed):
    def __init__(
        self,
        mmr:int,
        set_rank_image:bool = True,
        season:Optional[int] = config['season'],
        color:Optional[Union[discord.Colour,int]] = None,
        title:Optional[str] = None,
        type:Optional[str] = 'rich',
        url:Optional[str] = None,
        description:Optional[str] = None,
        timestamp:Optional[datetime.datetime] = None
    )->None:
        design = getRankData(season)[getRank(mmr,season).split(' ')[0]]
        super().__init__(
            color = color or design['color'],
            title = title,
            type= type,
            url= url,
            description= description,
            timestamp= timestamp
        )
        if set_rank_image:
            self.set_thumbnail(url=design['url'])