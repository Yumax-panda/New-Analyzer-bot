from typing import Optional,Any

from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account

from oauth2client.service_account import ServiceAccountCredentials
import gspread

import os
import json
import asyncio
import pandas as pd

import API.lounge_api as lounge_api


INITIAL_DETAILS = {
    'recruit':{},
    'poll':{},
    'channel_id':None
}
INITIAL_RESULTS = []

credential_key = json.loads(os.environ['CREDENTIAL_KEY'])
name_key = json.loads(os.environ['NAME_KEY'])

# setup Google Cloud Storage



cloud_credentials = service_account.Credentials.from_service_account_info(credential_key['cloud_credentials'])
storage_client = storage.Client(
    project = name_key['project_id'],
    credentials= cloud_credentials
)
bucket = storage_client.bucket(name_key['bucket_name'])

# setup Google Spreadsheet
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']


sheet_credentials = ServiceAccountCredentials.from_json_keyfile_dict(credential_key['sheet_credentials'],scope)
gc = gspread.authorize(sheet_credentials)
sh = gc.open('Analyzer-bot')



def get(path:str)->dict:
    """
    get data from Google Storage
    """
    blob = bucket.blob(path)
    return json.loads(blob.download_as_string())



def post(path:str,params:dict)->None:
    """
    post data to Google Storage
    """
    blob = bucket.blob(path)
    blob.upload_from_string(
        data=json.dumps(params),
        content_type='application/json'
    )
    return



def get_details(
    guild_id:int,
    fill_no_data:bool = True,
)->Optional[dict]:
    path = f'{guild_id}/details.json'
    try:
        return get(path)
    except NotFound:
        if fill_no_data:
            post(path,INITIAL_DETAILS)
            return INITIAL_DETAILS
        return



def post_details(
    guild_id:int,
    params:dict
)->None:
    path = f'{guild_id}/details.json'
    post(path,params)
    return



def get_results(
    guild_id:int,
    fill_no_data:bool = True,
)->Optional[list[dict]]:
    path = f'{guild_id}/results.json'
    try:
        return get(path)
    except NotFound:
        if fill_no_data:
            post(path,INITIAL_RESULTS)
            return INITIAL_RESULTS
        return



def post_results(
    guild_id:int,
    params:list[dict]
)->None:
    path = f'{guild_id}/results.json'
    post(path,params)
    return



def get_sq_info()->dict:
    return get(path='sq_info.json')



def post_sq_info(params:dict)->None:
    post(path='sq_info.json', params=params)
    return



def get_sheet(sheet_name:str)->dict:
    ret = {}
    worksheet = sh.worksheet(sheet_name)
    user_list=worksheet.get_all_records()
    for user in user_list:
        id = user.get('user_id')
        if id is not None:
            if str(id) != '':
                user.pop('user_id')
                ret[str(id)] = user
    return ret



def overwrite_sheet(
    sheet_name:str,
    values:list[list]
)->None:
    worksheet = sh.worksheet(sheet_name)
    worksheet.clear()
    sh.values_append(
        sheet_name,
        {'valueInputOption':'USER_ENTERED'},
        {'values':values}
    )
    return



def get_team_name(guild_id:int)->Optional[str]:
    worksheet = sh.worksheet('team')
    guild_list = worksheet.get_all_values()
    for record in guild_list:
        if str(guild_id) == str(record[0]):
            if len(record) ==1:
                continue
            if record[1] is not None:
                if str(record[1]) != '':
                    return str(record[1])
    return



def record_team_name(
    guild_id:int,
    team_name: str
)->None:
    is_existing = False
    worksheet = sh.worksheet('team')
    guild_list = worksheet.get_all_values()
    for record in guild_list:
        if len(record) ==1:
            continue
        if str(guild_id) == str(record[0]):
            record[1] = str(team_name)
            is_existing = True
            break
    if not is_existing:
        guild_list.append([str(guild_id),str(team_name)])
    overwrite_sheet('team',guild_list)
    return



def delete_team_name(guild_id:int)->None:
    is_existing = False
    worksheet = sh.worksheet('team')
    guild_list = worksheet.get_all_values()
    for record in guild_list:
        if len(record)==1:
            continue
        if str(guild_id) == str(record[0]):
            record.pop(1)
            is_existing = True
            break
    if not is_existing:
        return
    overwrite_sheet('team',guild_list)
    return



def get_linked_id(
    discord_id:int,
    fill_blank:bool=False
    )->Optional[int]:
    """
    Search for linked Discord ID using main ID
    """
    if discord_id is None:
        return None
    data_dict = get_sheet('link_account')
    user = data_dict.get(str(discord_id))
    if user is not None:
        if user['lounge_disco'] != '':
            return int(user['lounge_disco'])
    if fill_blank:
        return discord_id
    return



def get_linked_ids(
    discord_ids:list[int],
)->list[int]:
    """
    if not linked, then return main_id
    """
    data_dict = get_sheet('link_account')
    ret = []
    for discord_id in discord_ids:
        if discord_id is None:
            ret.append(None)
            continue
        user = data_dict.get(str(discord_id))
        if user is not None:
            ret.append(int(user['lounge_disco']))
        else:
            ret.append(discord_id)
    return ret



def record_lounge_id(
    discord_id:int,
    lounge_id:int
)->None:
    data_dict = get_sheet('link_account')
    data_dict[str(discord_id)] = {'lounge_disco':str(lounge_id)}
    ids = list(data_dict.keys())
    user_ids = [str(id) for id in ids if str(id) !='']
    input_data  =[['user_id','lounge_disco']]
    for user_id in user_ids:
        input_data.append(
            [str(user_id),str(data_dict[user_id]['lounge_disco'])]
        )
    overwrite_sheet('link_account',input_data)
    return


async def get_player(
    name:str = None,
    player_id:int = None,
    discord_id:int=None,
    mkc_id:int = None,
    fc:str = None,
    season:int = None,
    search_linked_id:bool = True
)->Optional[dict[str,Any]]:
    if search_linked_id:
        discord_id = get_linked_id(discord_id,True)
    return await lounge_api.get_player(
        player_id = player_id,
        name = name,
        mkc_id= mkc_id,
        discord_id= discord_id,
        fc= fc,
        season = season
    )




async def get_players(
    discord_ids:list[int],
    season:Optional[int] = None,
    search_linked_id:bool = True,
    remove_None:bool = False,
    return_exceptions:bool = True
    )->list[Optional[dict[str,Any]]]:
    if search_linked_id:
        discord_ids = get_linked_ids(discord_ids)
    tasks = [asyncio.create_task(lounge_api.get_player(
        discord_id = discord_id,
        season = season
    ))for discord_id in discord_ids]
    players = await asyncio.gather(
        *tasks,
        return_exceptions=return_exceptions
    )
    if remove_None:
        return [player for player in players if player is not None]
    return players



def get_previous_data(
    season:int,
    min_mmr:Optional[int] = None,
    max_mmr:Optional[int] = None,
)->dict[str,Any]:
    """
    season : 1~4
    """
    df = pd.read_csv(
        f'leaderboards/season{season}.csv',
        encoding= 'cp932'
    )
    if min_mmr is None:
        min_mmr = 0
    if max_mmr is None:
        max_mmr = 100000
    extracted_df = df[(min_mmr<=df['mmr']) & (df['mmr']<=max_mmr)].copy()
    return list(extracted_df.to_dict('index').values())



def get_prev_player(
    season:int,
    name:str,
)->Optional[dict]:
    """
    only for s1~s4 available
    """
    players = get_previous_data(season)
    for player in players:
        if player['name'] == name:
            return player
    return None
