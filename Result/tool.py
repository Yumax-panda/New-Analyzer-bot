from typing import Optional,Union

import discord

from datetime import datetime
from io import BytesIO
import pandas as pd
import re

import API.api as API



def post_df(guild_id:int,df:pd.DataFrame)->None:
    """
    Expected df Parameters
    -------
    score      : int
    enemyScore : int
    enemy      : str
    date       : str
        expected JST time (%Y-%m-%d %H:%M:%S)

    Settings
    -------
    automatically  drop duplicates and
    sort by df['date'] (JST time expected)
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'],infer_datetime_format=True)
    df.sort_values(by='date',ascending=True,inplace=True)
    df = df.copy()
    df['date'] = df['date'].astype(str)
    params = df.drop_duplicates().to_dict('records')
    API.post_results(guild_id,params=params)
    return



def load_data(guild_id:int,buffer:BytesIO)->None:
    """parameter 'date' is regarded as JST timezone."""
    df = pd.read_csv(buffer,skipinitialspace=True,header=None).loc[:,[1,2,3,4]]
    df.columns = ['score','enemyScore','enemy','date']
    post_df(guild_id,df)
    return



def export_data(guild_id:int,team_name:str)->Optional[discord.File]:
    data = API.get_results(guild_id,False)
    if data is None:
        return None
    buffer = BytesIO()
    if data.get('mogi') is not None: # previous data format
        pd.DataFrame(data['mogi']).to_csv(
            buffer,
            encoding= 'utf-8',
            header= None,
            index=False
        )
    else:
        df = pd.DataFrame(data)
        df.insert(0,'team',team_name)
        df.to_csv(
            buffer,
            encoding='utf-8',
            header=False,
            index=False,
            columns=['team','score','enemyScore','enemy','date']
        )
    buffer.seek(0)
    return discord.File(fp=buffer,filename=f'results.csv')



def WorL(diff:int)->str:
    if diff > 0: return 'Win'
    elif diff == 0: return 'Draw'
    else: return 'Lose'


def vs_history(guild_id:int,team_name:str)->str:
    result = API.get_results(guild_id)
    if len(result) == 0:
        return 'No match registered.'
    d = pd.DataFrame(result)
    exp_df = d[d['enemy'].str.startswith((team_name[0].lower(),team_name[0].upper()))].copy()
    df = exp_df.query(f'enemy=="{team_name}"')
    if len(df) == 0:
        if len(exp_df) == 0: return f'No match Found. (vs.{team_name})'
        else: return f"Expected...\n{', '.join(exp_df['enemy'].unique().tolist())}"
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'],infer_datetime_format=True)
    df.sort_values(by='date',ascending=True,inplace=True)
    df['result']=df['score']-df['enemyScore']
    win,lost,draw = len(df[df['result']>0]),len(df[df['result']<0]),len(df[df['result']==0])
    sum_txt = f'__**Win**__:  {win}  __**Lose**__:  {lost}  __**Draw**__:  {draw}'
    df['date']=df['date'].dt.strftime('%Y/%m/%d').copy()
    view_df = df.loc[:,['date','result']]
    view_df.insert(1,'score',' '+df['score'].astype(str)+' - '+df['enemyScore'].astype(str)+' ')
    txt = view_df.to_string(
        formatters={'result':WorL},
        header=False
    )
    return f'{len(df)} matches found;  vs.**{team_name}**```{txt}```{sum_txt}'



def overall_matches(guild_id:int)->list[str]:
    result = API.get_results(guild_id)
    if len(result) == 0:
        return ['No match registered.']
    df = pd.DataFrame(result)
    df['diff'] = df['score'] - df['enemyScore']
    names = df['enemy'].unique().tolist()
    view_df = pd.DataFrame(columns=['Win','Lose','Draw','total'],index=None)
    for name in names:
        temp_df = df[df['enemy']==name].copy()
        w = len(temp_df[temp_df['diff']>0])
        l = len(temp_df[temp_df['diff']<0])
        d = len(temp_df[temp_df['diff']==0])
        view_df.loc[name] =[w,l,d,w+l+d]
        del temp_df
    view_df.sort_values(by='total',ascending=False,inplace=True)
    sums = view_df.sum().to_list()
    win,lose,draw=sums[0],sums[1],sums[2]
    txt = view_df.to_string(
        columns=['Win','Lose','Draw'],
        justify= 'center'
    )
    sum_txt = f'**{len(view_df)} teams**  (__**Win**__:{win}  __**Lose**__:{lose}  __**Draw**__:{draw})'
    return txt.split('\n') + [sum_txt]



def last_match(guild_id:int,num:Optional[int]=None)->list[str]:
    result = API.get_results(guild_id)
    if len(result) == 0:
        return ['No match registered.']
    df = pd.DataFrame(result)
    if num is None:
        num = len(result)
    num = min(len(result),num)
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'],infer_datetime_format=True)
    df.sort_values(by='date',ascending=True,inplace=True)
    df['result']=df['score']-df['enemyScore']
    df = df[-1*num:].copy()
    win,lost,draw = len(df[df['result']>0]),len(df[df['result']<0]),len(df[df['result']==0])
    sum_txt = f'__**Win**__:  {win}  __**Lose**__:  {lost}  __**Draw**__:  {draw}'
    view_df = df.loc[:,['enemy','result']]
    view_df.insert(0,'score',df['score'].astype(str)+'-'+df['enemyScore'].astype(str))
    txt = view_df.to_string(
        formatters={'result':WorL},
        justify= 'center',
        header=['Score','vs','Result']
    )
    return txt.split('\n') + [sum_txt]



def register_result(guild_id:int,**kwargs:dict)->None:
    """
    Parameters
    -----------
    score       : int,
    enemyScore  : int,
    enemy       : str,
    date        : str
        expected JST time (%Y-%m-%d %H:%M:%S)
    """
    result = API.get_results(guild_id)
    result.append(kwargs)
    post_df(guild_id,pd.DataFrame(result))
    return



def get_score(argument:Optional[str])->Optional[list[int]]:
    if argument is None:
        return None
    scores = re.findall(r'[0-9]+',argument)
    if len(scores) ==0:
        return None
    return list(map(int,scores))[:2]



def get_date(argument:Optional[str])->Union[str,bool]:
    if argument is None:
        return None
    try:
        dt = datetime.strptime(argument, "%Y/%m/%d")
    except ValueError:
        return False
    return dt.strftime('%Y-%m-%d %H:%M:%S')
