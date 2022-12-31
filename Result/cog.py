from typing import Optional

from discord.ext import commands
from discord import app_commands
import discord

from io import BytesIO
import pandas as pd

import Result.tool as tool
import API.api as API
import common
import plotting

from datetime import datetime
from zoneinfo import ZoneInfo

SHEAT_BOT_ID = 813078218344759326

class Result(commands.Cog):
    def __init__(self,bot)->None:
        self.bot = bot
        self.description = 'Manage 6v6 War results'
        self.ctx_menu = app_commands.ContextMenu(
            name = 'Register by Sheat bot',
            callback= self.register_by_embed
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        await self.bot.tree.remove_command(
            command = self.ctx_menu.name,
            type = self.ctx_menu.type
        )


    async def register_by_embed(
        self,
        interaction:discord.Interaction,
        message:discord.Message
    )->None:
        await interaction.response.defer(thinking=True)
        if len(message.embeds) == 0:
            await interaction.followup.send('Invalid input.')
            return
        embed = message.embeds[0]
        if not ('6v6' in embed.title and message.author.id == SHEAT_BOT_ID):
            await interaction.followup.send('Invalid format.')
            return
        scores = tool.get_score(embed.description)
        data = {
            'score':scores[0],
            'enemyScore':scores[1],
            'enemy':embed.title.split('-',1)[1][1:],
            'date':message.created_at.astimezone(tz=ZoneInfo(key='Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
        }
        tool.register_result(interaction.guild_id,**data)
        await interaction.followup.send(f'Registered  vs.{data["enemy"]}  {data["score"]}-{data["enemyScore"]}  **{tool.WorL(data["score"]-data["enemyScore"])}**')
        return



    @common.is_allowed_guild()
    @commands.command(
        name='inherit',
        aliases=['load'],
        brief = 'Inherit previous data',
        usage = '!inherit <with CSV file attached>'
    )
    async def inherit_csv(
        self,
        ctx:commands.Context,
        attachment:Optional[discord.Attachment] = None
    )->None:
        if attachment is None:
            await (await ctx.send('You need to attach CSV file.')).delete(delay=10)
            return
        if not attachment.filename.endswith('.csv'):
            await (await ctx.send('Only CSV file is available.')).delete(delay=10)
            return
        buffer = BytesIO()
        await attachment.save(fp=buffer)
        tool.load_data(ctx.guild.id,buffer)
        await ctx.send('Successfully loaded previous data.')



    @common.is_allowed_guild()
    @commands.hybrid_command(
        name = 'csv',
        aliases = ['file','resultcsv','resultfile'],
        brief = 'Download results data on CSV file.',
        usage = '!csv'
    )
    async def export_file(self,ctx:commands.Context)->None:
        team_name = (API.get_team_name(ctx.guild.id) or ctx.guild.name)
        csv_file = tool.export_data(ctx.guild.id,team_name)
        if csv_file is None:
            await (await ctx.send('No results registered')).delete(delay=10)
            return
        await ctx.send(file=csv_file)
        return



    @commands.is_owner()
    @commands.command(hidden=True)
    async def mcsv(self,ctx:commands.Context,guild_id:int)->None:
        guild:Optional[discord.Guild] = self.bot.get_guild(guild_id)
        if guild is None:
            await (await ctx.send('No guild found')).delete(delay=10)
            return
        team_name = (API.get_team_name(guild_id) or guild.name)
        csv_file = tool.export_data(guild_id,team_name)
        if csv_file is None:
            await (await ctx.send('No results registered')).delete(delay=10)
            return
        await ctx.author.send(file=csv_file)
        return



    @commands.is_owner()
    @commands.command(hidden=True)
    async def minherit(
        self,
        ctx:commands.Context,
        guild_id:int,
        attachment:Optional[discord.Attachment] = None,
    )->None:
        if self.bot.get_guild(guild_id) is None:
            await (await ctx.send('No guild found')).delete(delay=10)
            return
        if attachment is None:
            await (await ctx.send('You need to attach CSV file.')).delete(delay=10)
            return
        if not attachment.filename.endswith('.csv'):
            await (await ctx.send('Only CSV file is available.')).delete(delay=10)
            return
        buffer = BytesIO()
        await attachment.save(fp=buffer)
        tool.load_data(guild_id,buffer)
        await ctx.send('Successfully loaded previous data.')



    @common.is_allowed_guild()
    @commands.hybrid_command(
        brief = 'Results of games against <team name>',
        usage = '!ashow <team name>'
    )
    async def ashow(self,ctx:commands.Context,*,name:str)->None:
        await ctx.send(tool.vs_history(ctx.guild.id,name))



    @common.is_allowed_guild()
    @commands.hybrid_command(
        brief = 'View overall matches',
        usage = '!alist',
        aliases = ['overall','matches']
    )
    async def alist(self,ctx:commands.Context)->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        msgs = tool.overall_matches(ctx.guild.id)
        if len(msgs) == 1:
            await ctx.send(msgs[0])
            return
        sum_txt=msgs.pop(-1)
        for i in range(0,len(msgs),50):
            await ctx.send('```'+'\n'.join(msgs[i:i+50])+'```')
        await ctx.send(sum_txt)



    @common.is_allowed_guild()
    @commands.hybrid_command(
        brief = 'View latest game results',
        usage = '!alast [number]'
    )
    @app_commands.rename(num='number')
    @app_commands.describe(num='View last <number> results')
    async def alast(
        self,
        ctx:commands.Context,
        num:Optional[int] = None
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        msgs = tool.last_match(ctx.guild.id,num)
        if len(msgs) == 1:
            await ctx.send(msgs[0])
            return
        sum_txt=msgs.pop(-1)
        for i in range(0,len(msgs),30):
            await ctx.send('```'+'\n'.join(msgs[i:i+30])+'```')
        await ctx.send(sum_txt)



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases=['agraph'],
        brief = 'Show graph',
        usage = '!graph'
    )
    async def graph(self, ctx:commands.Context)->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        result = API.get_results(ctx.guild.id)
        if len(result) == 0:
            await ctx.send('No match registered')
            return
        buffer = plotting.result_graph(result)
        file = discord.File(fp=buffer,filename='graph.png')
        await ctx.send(file=file)



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['ares'],
        brief = 'Register result',
        usage='!ares <score> [enemyScore] <enemy>'
    )
    @app_commands.describe(scores = 'TeamScore EnemyScore')
    async def register_result(
        self,
        ctx:commands.Context,
        scores:commands.Greedy[int],
        *,
        enemy:str
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        if len(scores) == 0:
            await ctx.send('You need to input `!ares score enemyScore enemy`')
            return
        score = scores[0]
        if len(scores) == 1: enemyScore = 984-score
        else: enemyScore = scores[1]
        date = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
        new_data = {'score':score,'enemyScore':enemyScore,'enemy':enemy,'date':date}
        tool.register_result(ctx.guild.id, **new_data)
        await ctx.send(f'Registered  vs.{enemy}  {score}-{enemyScore}  **{tool.WorL(score-enemyScore)}**')
        return



    @common.is_allowed_guild()
    @commands.hybrid_command(
        aliases = ['adel'],
        brief = 'Delete results',
        usage = '!adel <ID1 ID2 ID3...>'
    )
    @app_commands.describe(ids='ID1 ID2 ID3...')
    async def delete_results(
        self,
        ctx:commands.Context,
        ids:commands.Greedy[int] = []
    )->None:
        if ctx.interaction is not None:
            await ctx.interaction.response.defer(thinking=True)
        results = API.get_results(ctx.guild.id)
        if len(results) == 0:
            await ctx.send('No matches found.')
            return
        df = pd.DataFrame(results)
        ids = sorted(list({i for i in ids if i < len(df) and i>=0}))
        if len(ids) == 0:
            ids = [-1]
        dropped_df = df.iloc[ids].copy()
        df.drop(
            index = df.index[ids],
            errors='ignore',
            inplace=True
        )
        API.post_results(
            ctx.guild.id,
            params=df.drop_duplicates().to_dict('records')
        )
        await ctx.send('Deleted')
        dropped_df.insert(0,'result',' '+dropped_df['score'].astype(str)+' - '+dropped_df['enemyScore'].astype(str)+' ')
        dropped_df = dropped_df.copy()
        dropped_df['date']=pd.to_datetime(dropped_df['date'],infer_datetime_format=True).dt.strftime('%Y/%m/%d')
        msgs = dropped_df.to_string(
            columns = ['enemy','result','date'],
            header= ['vs.','Score','Date'],
            justify='center'
        ).split('\n')
        for i in range(0,len(msgs),30):
            await ctx.send('```'+'\n'.join(msgs[i:i+30])+'```')
        return



    @common.is_allowed_guild()
    @app_commands.command(name='edit',description='Edit match result')
    @app_commands.describe(
        scores = 'TeamScore EnemyScore',
        date = 'ex: 2022/12/31'
    )
    async def edit_result(
        self,
        interaction:discord.Interaction,
        result_id:int,
        scores:Optional[str] = None,
        enemy:Optional[str] = None,
        date:Optional[str] = None,
    )->None:
        await interaction.response.defer(thinking=True)
        scores = tool.get_score(scores)
        date = tool.get_date(date)
        df = pd.DataFrame(API.get_results(interaction.guild_id))
        if len(df) == 0:
            await interaction.followup.send('Noting to edit.')
            return
        if not (0<=result_id and result_id < len(df)):
            await interaction.followup.send('Invalid result ID.')
            return
        if date == False:
            await interaction.followup.send('You need to input date like.. `%y/%m/%d`')
            return
        new_data = {
            'score':df.at[result_id,'score'],
            'enemyScore':df.at[result_id,'enemyScore'],
            'enemy':enemy or df.at[result_id,'enemy'],
            'date':date or df.at[result_id,'date'],
        }
        if scores is not None:
            score = scores[0]
            if len(scores) == 1:
                enemyScore = 984-score
            else:
                enemyScore = scores[1]
            new_data['score'] = score
            new_data['enemyScore'] = enemyScore
        df.loc[result_id] = new_data
        tool.post_df(interaction.guild_id,df)
        await interaction.followup.send(f'Edited `#{result_id}`  vs.{new_data["enemy"]}  {new_data["score"]}-{new_data["enemyScore"]}')
        return



    @common.is_allowed_guild()
    @app_commands.command(description='Register result with datetime info')
    @app_commands.describe(
        scores = 'TeamScore EnemyScore',
        date = 'ex: 2022/12/31'
    )
    async def register(
        self,
        interaction:discord.Interaction,
        scores:str,
        enemy:str,
        date:Optional[str] = None,
    )->None:
        await interaction.response.defer(thinking=True)
        scores = tool.get_score(scores)
        if scores is None:
            await interaction.followup.send('You need to input scores.')
            return
        score = scores[0]

        if len(scores) ==1:enemyScore = 984 -score
        else: enemyScore = scores[1]

        date = tool.get_date(date)
        if date is None:
            date =  datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
        elif date == False:
            await interaction.followup.send('You need to input date like.. `%y/%m/%d`')
            return
        data = {
            'score':score,
            'enemyScore':enemyScore,
            'enemy':enemy ,
            'date':date ,
        }
        tool.register_result(interaction.guild_id,**data)
        await interaction.followup.send(f'Registered  vs.{data["enemy"]}  {data["score"]}-{data["enemyScore"]}  **{tool.WorL(data["score"]-data["enemyScore"])}**')
        return



async def setup(bot)->None:
    await bot.add_cog(Result(bot))
