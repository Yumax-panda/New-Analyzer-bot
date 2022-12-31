from typing import Optional,Any

import aiohttp

BASE_URL = 'https://www.mk8dx-lounge.com/api'


async def get(path:str,query:dict={})->Optional[dict[str,Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url = BASE_URL + path, params = query) as response:
            if response.status != 200:
                return None
            return await response.json()



async def get_player(
    player_id:Optional[int] = None,
    name:Optional[str] = None,
    mkc_id:Optional[int] = None,
    discord_id:Optional[int] = None,
    fc:Optional[str] = None,
    season:Optional[int] = None
)->Optional[dict[str,Any]]:
    query = {}
    if player_id is not None:
        query['id'] = player_id
    elif name is not None:
        query['name'] = name
    elif mkc_id is not None:
        query['mkcId'] = mkc_id
    elif discord_id is not None:
        query['discordId'] = discord_id
    elif fc is not None:
        query['fc'] = fc
    else:
        return None
    if season is not None:
        query['season'] = season
    return await get(path='/player',query=query)



async def get_player_info(
    player_id:Optional[int]=None,
    name:Optional[str]=None,
    season:Optional[int]=None,
)->Optional[dict[str,Any]]:
    query ={}
    if player_id is not None:
        query['id'] = player_id
    elif name is not None:
        query['name'] = name
    else:
        return None
    if season is not None:
        query['season'] = season
    return await get(path='/player/details',query=query)



async def get_player_list(
    min_mmr :Optional[int]=None,
    max_mmr : Optional[int]=None,
    season:Optional[int]=None
)->Optional[list[dict[str,Any]]]:
    query ={}
    if min_mmr is not None:
        query['minMmr'] = min_mmr
    if max_mmr is not None:
        query['maxMmr'] = max_mmr
    if season is not None:
        query['season'] = season
    data = await get(path='/player/list',query=query)
    if data is None:
        return None
    return data.get('players')



async def get_leaderboard(
    season:int,
    skip:int = 0,
    page_size:int =50,
    name:Optional[str] = None,
    country:Optional[str] = None,
    min_mmr:Optional[int] = None,
    max_mmr:Optional[int] = None,
    min_events_played:Optional[int] = None,
    max_events_played:Optional[int] = None
)->Optional[list[dict[str,Any]]]:
    query = {'season': season, 'skip': skip, 'pageSize': page_size}
    if name is not None:
        query['search'] = name
    if country is not None:
        query['country'] = country
    if min_mmr is not None:
        query['minMmr'] = min_mmr
    if max_mmr is not None:
        query['maxMmr'] = max_mmr
    if min_events_played is not None:
        query['minEventsPlayed'] = min_events_played
    if max_events_played is not None:
        query['maxEventsPlayed'] = max_events_played
    board = await get(path='/player/leaderboard',query=query)
    if board is None:
        return None
    return board.get('data')



async def get_table(table_id:int)->Optional[dict[str,Any]]:
    return await get(
        path = '/table',
        query = {'tableId':table_id}
    )



async def get_table_list(
    start:Optional[str] = None,
    end:Optional[str] = None,
    season:Optional[int] = None
)->Optional[dict[str,Any]]:
    """
    start and end are iso-format datetime on utc.
    """
    query = {}
    if start is not None:
        query['from'] = start
    if end is not None:
        query['to'] = end
    if season is not None:
        query['season'] = season
    return await get(path='/table/list', query=query)