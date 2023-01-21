from __future__ import annotations
from typing import Optional, Union
from datetime import datetime,timedelta
import re

from discord.ui import Button, View
from discord import (
    Interaction,
    Embed,
    Message,
    Colour,
    TextChannel,
    ButtonStyle
)

from zoneinfo import ZoneInfo

from Result.tool import register_result, WorL
from Sokuji.errors import SokujiNotFound
from Sokuji.lang import Lang
from Sokuji.point import Point
from Sokuji.status import Status
from Sokuji.track import Track

BOT_ID = 1038322985146273853


async def button_callback(
    cls: Union[ButtonJA,ButtonEN],
    interaction: Interaction,
    language: Lang
    )->None:
    await interaction.response.defer(thinking=True)
    data = {
            'score':cls.sokuji.total.ally,
            'enemyScore':cls.sokuji.total.enemy,
            'enemy':cls.sokuji.tags[1],
            'date': cls.sokuji.message.created_at.astimezone(tz=ZoneInfo(key='Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
        }
    register_result(interaction.guild_id, **data)
    txt = f'vs.{data["enemy"]}  {data["score"]}-{data["enemyScore"]}  **{WorL(data["score"]-data["enemyScore"])}**'
    await interaction.followup.send(
        {Lang.JA:f'戦績を登録しました。\n{txt}', Lang.EN:f'Registered\n{txt}'}[language]
    )
    cls.view.stop()
    cls.sokuji.change_status(Status.ARCHIVE)
    await cls.sokuji.message.edit(view=None,embed=cls.sokuji.embed)
    return


class ButtonJA(Button):
    def __init__(self,sokuji: SokujiMessage):
        super().__init__(label='登録',style=ButtonStyle.green)
        self.sokuji = sokuji

    async def callback(self, interaction: Interaction) -> None:
        await button_callback(self, interaction, Lang.JA)


class ButtonEN(Button):
    def __init__(self,sokuji: SokujiMessage):
        super().__init__(label='Register',style=ButtonStyle.green)
        self.sokuji = sokuji

    async def callback(self, interaction: Interaction) -> None:
        await button_callback(self, interaction, Lang.EN)


class RegisterView(View):
    def __init__(self, sokuji: SokujiMessage):
        super().__init__(timeout=180)
        self.sokuji = sokuji

        if sokuji.lang == Lang.EN:
            self.add_item(ButtonEN(sokuji=sokuji))
        else:
            self.add_item(ButtonJA(sokuji=sokuji))


def get_ranks(text: str) -> Optional[list[int]]:
    if not text.startswith(tuple(['-']+[str(i) for i in range(0,10)])):
        return None

    _RE = re.compile(r'([0-9]|\-|\ )+')
    m = _RE.search(text)

    if m is None:
        return None

    rs = m.group().replace(' ','')
    data: list[int] = []
    prev: Optional[int] = None
    next_list: list[int] = []
    flag: bool = False

    while rs:
        next_list = []

        if rs.startswith('-'):
            flag = True
            rs = rs[1:]

        if data:
            prev = data[-1]
        else:
            prev = 0

        if rs.startswith('10'):
            next_list = [10]
            rs = rs[2:]
        elif rs.startswith('110'):
            next_list = [1,10]
            rs = rs[3:]
        elif rs.startswith('1112'):
            next_list = [11, 12]
            rs = rs[4:]
        elif rs.startswith('111'):
            next_list = [1, 11]
            rs = rs[3:]
        elif rs.startswith('112'):
            next_list = [1, 12]
            rs = rs[3:]
        elif rs.startswith('11'):
            next_list = [11]
            rs = rs[2:]
        elif rs.startswith('12'):
            if data:
                next_list = [12]
            else:
                next_list = [1, 2]
            rs = rs[2:]
        elif rs:
            next_list = [int(rs[0])]
            rs = rs[1:]

        if flag:
            if not next_list:
                next_list = [12]
            next = next_list[0]
            while next - prev > 1:
                data.append(prev+1)
                prev += 1
            flag = False

        data += next_list

    ranks = [r for r in sorted(set(data)) if 0 < r < 13]

    if len(ranks) > 6:
        return None

    for k in range(12,0,-1):
        if len(ranks) >= 6:
            return ranks
        if k not in ranks:
            ranks.append(k)


class Race:

    def __init__(
        self,
        ranks: list[int],
        track: Optional[Track] = None
    ):
        self.ranks = sorted(ranks)
        self.track = track

    @property
    def point(self) -> Point:
        return Race.calc_points(self.ranks)

    @staticmethod
    def calc_points(ranks: list[int]) -> Point:
        if len(ranks) == 0:
            return Point(0,0)
        p = [15,12,10,9,8,7,6,5,4,3,2,1]
        ally = sum([p[i-1] for i in ranks])
        return Point(ally,82-ally)


class SokujiMessage:

    def __init__(
        self,
        tags: list[str],
        lang: Optional[Lang] = None,
        status: Optional[Status] = None,
        races: list[Race] = [],
        penalty: Optional[Point] = None,
        repick: Optional[Point] = None,
        message: Optional[Message] = None,
        members: list[str] = [],
    ) -> None:
        self._tags: list[str] = tags
        self._lang: Lang = lang or Lang.JA
        self._status: Status = status or Status.ONGOING
        self._races: list[Race] = races
        self._penalty: Point = penalty or Point(0,0)
        self._repick: Point = repick or Point(0,0)
        self._message: Optional[Message] = message
        self._members: list[str] = members[:10]

    @property
    def embed(self) -> Embed:
        title = '即時集計 ' if self.lang == Lang.JA else 'Sokuji '
        title += f'6v6\n{self.tags[0]} - {self.tags[1]}'
        e = Embed(
            title = title,
            color = Colour.blurple()
        )

        for i,race in enumerate(self.races):
            txt = f'{i+1} '
            if race.track is not None:
                txt += '- '+ (race.track.nick_ja if self.lang == Lang.JA else race.track.nick_en)
            e.add_field(
                name = txt,
                value = f'`{race.point}`|`{",".join([str(r) for r in race.ranks])}`',
                inline = False
            )

        if self.penalty:
            e.add_field(name = 'Penalty', value = f'`{self.penalty}`',inline = False)

        if self.repick:
            e.add_field(name = 'Repick', value = f'`{self.repick}`', inline = False)

        if self.members:
            e.add_field(name = 'Members', value = f'> {", ".join(self.members)}')

        e.description = f'`{self.total.ally} : {self.total.enemy} @{12-len(self.races)}`'

        if self.status != Status.ONGOING:
            e.set_author(name = f'{self.status.en if self.lang == Lang.EN else self.status.ja}')

        return e

    @staticmethod
    def convert(message: Message) -> SokujiMessage:
        embed = message.embeds[0].copy()
        lang = Lang.JA if '即時集計' in embed.title else Lang.EN
        tags = embed.title.replace('\n',' ').replace('-','').split(' ')[-3:]
        int_filter = re.compile(r'[0-9]+')
        races: list[Race] = []
        penalty = Point(0,0)
        repick = Point(0,0)
        members: list[str] =[]
        status: Status = Status.ONGOING

        if embed.author is not None:
            status = Status.from_string(embed.author.name)

        for field in embed.fields:
            if 'Repick' in field.name:
                temp = list(map(int,re.findall(r'(-?[0-9]+)', field.value)))
                repick = repick + Point(temp[0],temp[1])
                continue

            if 'Penalty' in field.name:
                temp = list(map(int,re.findall(r'(-?[0-9]+)', field.value)))
                penalty = penalty + Point(temp[0],temp[1])
                continue

            if 'Members' in field.name:
                members = field.value[1:].replace(',',' ').split()
                continue

            nums = list(map(int,int_filter.findall(field.value)[-6:]))
            ranks = nums[-6:]
            track: Optional[track] = None

            if '-' in field.name:
                txt = field.name
                track = Track.get_track(txt[txt.find('-')+2:])

            races.append(Race(ranks,track))

        if status == Status.FINISHED and len(races) != 12:
            status = Status.ONGOING

        return SokujiMessage(
            tags = [tags[0],tags[-1]],
            lang = lang,
            status = status,
            races = races,
            penalty = penalty,
            repick = repick,
            message = message,
            members = members[:10]
        )

    @staticmethod
    def sum_points(races: list[Race]) -> Point:
        al,en = 0,0
        for race in races:
            al += race.point.ally
            en += race.point.enemy
        return Point(al,en)

    @property
    def tags(self) -> list[str]:
        return self._tags

    @tags.setter
    def tags(self,values: list[str]) -> None:
        if len(values) < 2:
            return
        self._tags = [str(t) for t in values[:2]]
        return

    @property
    def lang(self) -> Lang:
        return self._lang

    @lang.setter
    def lang(self,lang: Lang) -> None:
        self._lang = lang
        return

    @property
    def races(self) -> list[Race]:
        return self._races

    @property
    def penalty(self) -> Point:
        return self._penalty

    @property
    def repick(self) -> Point:
        return self._repick

    @property
    def message(self) -> Optional[Message]:
        return self._message

    @property
    def members(self) -> list[str]:
        return self._members

    @property
    def total(self) -> Point:
        return (SokujiMessage.sum_points(self._races)
                + self.penalty
                + self.repick)

    @property
    def status(self) -> Status:
        return self._status

    def edit(self, index:int, race: Race) -> None:
        self._races[index] = race
        return

    def add_race(self, race: Race) -> Optional[RegisterView]:
        if self.status != Status.ONGOING:
            return None

        self._races.append(race)

        if len(self._races) == 12:
            self._status = Status.FINISHED
            return RegisterView(self)

        return None

    def back(self) -> Optional[Race]:
        if len(self.races) == 0:
            return None
        if self.status == Status.ARCHIVE:
            return None
        self.change_status(Status.ONGOING)
        return self._races.pop()



    def add_penalty(self, penalty: Point) -> None:
        self._penalty = self._penalty + penalty
        return

    def add_repick(self, repick: Point) -> None:
        self._repick = self._repick + repick
        return

    def change_lang(self, lang: Lang) -> None:
        self._lang = lang
        return

    def change_status(self, status: Status) -> None:
        self._status = status
        return

    def change_members(self, members: list[str]) -> None:
        self._members = members[:10]
        return

    @staticmethod
    async def get(
        channel: TextChannel,
        *,
        minutes: int = 60,
        limit: int = 15,
        ignore_archive: bool = True,
        ignore_exception: bool = False
    ) -> tuple[Optional[SokujiMessage],Optional[Track]]:
        """get SokujiMessage and Track from TextChannel

        Args:
            channel (`TextChannel`): Messageable class (TextChannel expected)
            minutes (`int`, `optional`):  Defaults to 60.
            limit (`int`, `optional`):  Defaults to 15.
            ignore_archive (`bool`): Defaults `True`
            ignore_exception (`bool`): If `True`, the exception will be ignored and this function will return `(None, None)` instead.

        Returns:
            tuple[Optional[`SokujiMessage`],Optional[`Track`]]:

        Exception:
            `SokujiNotFound`: If sokuji message is not found, this exception will be raised.
        """

        track: Optional[Track] = None

        async for message in channel.history(
            after = datetime.now() - timedelta(minutes=minutes),
            oldest_first = False
        ):
            if track is None:
                track = Track.get_track(message.content)

            if not (message.author.id == BOT_ID and message.embeds):
                continue

            embed = message.embeds[0].copy()

            if not embed.title.startswith(('Sokuji','即時集計')):
                continue

            if embed.author is not None:
                if (ignore_archive
                    and Status.from_string(embed.author.name) == Status.ARCHIVE):
                    continue
            return SokujiMessage.convert(message = message), track

        async for message in channel.history(
            limit = limit,
            oldest_first = False
        ):
            if track is None:
                track = Track.get_track(message.content)

            if not (message.author.id == BOT_ID and message.embeds):
                continue

            embed = message.embeds[0].copy()

            if not embed.title.startswith(('Sokuji','即時集計')):
                continue

            if embed.author is not None:
                if (ignore_archive
                    and Status.from_string(embed.author.name) == Status.ARCHIVE):
                    continue
            return SokujiMessage.convert(message = message), track

        if not ignore_exception:
            raise SokujiNotFound

        return None, None


    async def send(
        self,
        channel: TextChannel,
        delete_old_message: bool = True,
        view: Optional[View] = None,
        ) -> None:
        if self.message is not None and delete_old_message:
            await self.message.delete()

        msg = await channel.send(embed=self.embed, view=view)
        self._message = msg
