from typing import Optional
from discord.app_commands import AppCommandError
from Sokuji.lang import Lang


class SokujiError(AppCommandError):
    pass


class SokujiNotFound(SokujiError):
    pass


class LocalizedError(SokujiError):
    def __init__(
        self,
        lang: Lang,
        content: dict[Lang,str]
    ):
        self.lang: Lang = lang
        self.content: dict[Lang,str] = content[lang]


class InvalidRaceNumber(LocalizedError):
    def __init__(self, lang: Optional[Lang] = None):
        super().__init__(
            lang = lang or Lang.JA,
            content = {
                Lang.JA: 'レース番号が不正です。',
                Lang.EN: 'Invalid race number.'
            }
        )


class InvalidRanks(LocalizedError):
    def __init__(self, lang: Optional[Lang] = None):
        super().__init__(
            lang = lang or Lang.JA,
            content = {
                Lang.JA: '順位の入力が不正です。',
                Lang.EN: 'Invalid ranks number.'
            }
        )


class InvalidTags(LocalizedError):
    def __init__(self, lang: Optional[Lang] = None):
        super().__init__(
            lang = lang or Lang.JA,
            content = {
                Lang.JA: '無効なタグです。',
                Lang.EN: 'Invalid tag.'
            }
        )
