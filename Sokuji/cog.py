from typing import Optional

from discord.ext import commands
from discord import app_commands, Message, Role, Interaction, WebhookMessage
from discord.app_commands import Group, Choice, AppCommandError

from Sokuji.errors import *
from Sokuji.lang import Lang
from Sokuji.point import Point
from Sokuji.status import Status
from Sokuji.track import Track
from Sokuji.components import Race, SokujiMessage, get_ranks

import common

from API.api import get_team_name


@common.is_allowed_guild()
class Sokuji(commands.GroupCog, group_name = 'sokuji',description = 'Sokuji'):

    def __init__(self,bot) -> None:
        self.bot: commands.Bot = bot


    @app_commands.command(description='Start Sokuji')
    @app_commands.choices( language = [
        Choice(name = '日本語', value = 'ja'),
        Choice(name = 'English', value = 'en')])
    async def start(
        self,
        interaction: Interaction,
        tag: str,
        language: Optional[str] = 'ja',
        role: Optional[Role] = None
        ) -> None:

        await interaction.response.defer(thinking=True)

        team_name = get_team_name(interaction.guild_id) or interaction.guild.name
        lang: Lang = {'ja':Lang.JA, 'en':Lang.EN}[language]
        members: list[str] = []

        if role is not None:
            members = [m.name for m in role.members if not m.bot]

        await interaction.followup.send(embed = SokujiMessage(
            tags = [team_name,tag.replace(' ','_')],
            lang = lang,
            members = members
        ).embed)

        return


    @app_commands.command(description='Change language')
    @app_commands.choices(lang=[
        Choice(name='日本語',value='ja'),
        Choice(name='English',value='en')])
    @app_commands.rename(lang='language')
    async def language(
        self,
        interaction: Interaction,
        lang: Optional[str] = 'ja'
    ) -> None:
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(
            channel = interaction.channel,
            ignore_archive = False
        )

        sokuji.change_lang(lang={'ja':Lang.JA, 'en':Lang.EN}[lang])
        await sokuji.message.edit(embed=sokuji.embed)
        await interaction.followup.send(
            {'ja':'日本語へ変更しました。','en':'Changed to English.'}[lang]
        )
        return


    @app_commands.command(description='Finish Sokuji')
    async def end(self, interaction: Interaction) -> None:
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(interaction.channel)
        sokuji.change_status(status=Status.ARCHIVE)
        await sokuji.message.edit(embed=sokuji.embed)
        await interaction.followup.send(
            {Lang.JA:'即時を終了しました。', Lang.EN:'Finished Sokuji.'}[sokuji.lang],
        )
        return


    @app_commands.command(description='Resume Sokuji')
    async def resume(self, interaction: Interaction) -> None:
        await interaction.response.defer(thinking=True)

        sokuji, _ = await SokujiMessage.get(
            channel= interaction.channel,
            ignore_archive = False
        )

        if sokuji.status != Status.ARCHIVE:
            await interaction.followup.send(
                {Lang.JA:'既に即時は開始されています。', Lang.EN:'Sokuji has already started.'}[sokuji.lang],
            )
            return

        if len(sokuji.races) >= 12:
            status = Status.FINISHED
        else:
            status = Status.ONGOING

        sokuji.change_status(status)
        await sokuji.message.edit(embed = sokuji.embed)
        await interaction.followup.send(
            {Lang.JA:'即時を再開しました。', Lang.EN:'Resume Sokuji.'}[sokuji.lang]
        )
        return


    @app_commands.command(description='Edit Sokuji')
    async def edit(
        self,
        interaction: Interaction,
        tag: Optional[str] = None,
        role: Optional[Role] = None
    ) -> None:
        await interaction.response.defer(thinking=True)

        sokuji, _ = await SokujiMessage.get(interaction.channel)

        if role is not None:
            sokuji._members = [m.name for m in role.members if not m.bot]

        if tag is not None:
            sokuji._tags[-1] = tag

        await sokuji.message.edit(embed = sokuji.embed)
        await interaction.followup.send(
            {Lang.JA:'即時を編集しました。', Lang.EN:'Edited Sokuji.'}[sokuji.lang]
        )
        return


    penalty = Group(name='penalty',description='Penalty')


    @penalty.command(description='Add penalty')
    @app_commands.describe(tag='ex: AA', amount='ex: -15')
    @app_commands.choices(reason=[
        Choice(name='Repick',value='repick'),
        Choice(name='Penalty',value='penalty')])
    async def add(
        self,
        interaction: Interaction,
        reason: Optional[str] = 'repick',
        tag: Optional[str] = None,
        amount: Optional[int] = None
    ) -> None:
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(interaction.channel)

        if tag is None:
            tag = sokuji.tags[0]

        if tag not in sokuji.tags:
            raise InvalidTags

        p = Point(0,amount or -15) if tag == sokuji.tags[-1] else Point(amount or -15, 0)

        if reason == 'repick':
            sokuji.add_repick(p)
        elif reason == 'penalty':
            sokuji.add_penalty(p)

        await sokuji.message.delete()
        await interaction.followup.send(
            {Lang.JA:'ペナルティを登録しました。', Lang.EN:'Added penalty.'}[sokuji.lang],
            embed = sokuji.embed
        )


    @penalty.command(description='Clear penalty')
    @app_commands.choices(reason=[
        Choice(name='Repick',value='repick'),
        Choice(name='Penalty',value='penalty')])
    async def clear(
        self,
        interaction: Interaction,
        reason: Optional[str] = None
        ) -> None:
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(interaction.channel)

        if reason != 'repick':
            sokuji._penalty = Point(0,0)
        if reason != 'penalty':
            sokuji._repick = Point(0,0)

        await sokuji.message.edit(embed = sokuji.embed)
        await interaction.followup.send(
            {Lang.JA:'ペナルティを消去しました。', Lang.EN:'Cleared penalty.'}[sokuji.lang]
        )
        return


    race = Group(name='race',description='Race')


    @race.command(description='Add race')
    async def add(
        self,
        interaction: Interaction,
        ranks: str,
        track: str = '',
    ):
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(interaction.channel)
        ranks: Optional[list[int]] = get_ranks(ranks)

        if ranks is None:
            raise InvalidRanks(sokuji.lang)

        view = sokuji.add_race(Race(ranks,Track.get_track(track)))
        await sokuji.message.delete()
        msg: WebhookMessage = await interaction.followup.send(
            {Lang.JA:'順位を追加しました。', Lang.EN:'Race added.'}[sokuji.lang],
            embed = sokuji.embed
        )

        if view is not None:
            sokuji._message = msg
            await msg.edit(view=view)
            await view.wait()

        return


    @race.command(description='Edit race')
    @app_commands.rename(num='race_num')
    async def edit(
        self,
        interaction: Interaction,
        ranks: str,
        num: int,
        track: Optional[str] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(interaction.channel)
        ranks: Optional[list[int]] = get_ranks(ranks)

        if ranks is None:
            raise InvalidRanks

        try:
            sokuji.edit(num-1,Race(ranks, Track.get_track(track)))
        except IndexError:
            raise InvalidRaceNumber(sokuji.lang)

        await sokuji.message.edit(embed = sokuji.embed)
        await interaction.followup.send({Lang.JA:'レースを編集しました。', Lang.EN:'Edited race.'}[sokuji.lang])
        return


    @race.command(description='Delete race')
    @app_commands.rename(num='race_num')
    async def delete(
        self,
        interaction: Interaction,
        num: Optional[int] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        sokuji, _ = await SokujiMessage.get(interaction.channel)

        try:
            sokuji._races.pop(num-1 if num is not None else -1)
        except IndexError:
            raise InvalidRaceNumber(sokuji.lang)

        await sokuji.message.edit(embed=sokuji.embed)
        await interaction.followup.send(
            {Lang.JA:'レースを削除しました。', Lang.EN:'Deleted race.'}[sokuji.lang]
        )
        return




    @commands.Cog.listener('on_message')
    async def refresh_sokuji(self, message: Message) -> None:
        if message.author.bot:
            return

        sokuji, track = await SokujiMessage.get(message.channel, ignore_exception=True)

        if sokuji is None:
            return

        if message.content.lower() == 'back' and sokuji.status != Status.ARCHIVE:
            sokuji.back()
            await sokuji.send(message.channel)
            return

        if sokuji.status != Status.ONGOING:
            return

        ranks = get_ranks(message.content)

        if ranks is None:
            return

        view = sokuji.add_race(race=Race(ranks,track))
        await sokuji.send(message.channel, view=view)

        if view is not None:
            await view.wait()

        return


    async def cog_app_command_error(
        self,
        interaction: Interaction,
        error: AppCommandError
        ) -> None:

        if isinstance(error, LocalizedError):
            await interaction.followup.send(error.content)
            return

        if isinstance(error, SokujiNotFound):
            await interaction.followup.send('Sokuji not found.')
            return

        raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sokuji(bot))
