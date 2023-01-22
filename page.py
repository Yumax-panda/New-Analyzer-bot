from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from discord.ui import View, button
from discord import Interaction, Message, ButtonStyle


if TYPE_CHECKING:
    from discord import Embed
    from discord.ui import Button
    from discord.ext.commands import Context


class EmbedPage(View):
    def __init__(
        self,
        embeds: list[Embed],
        *,
        ctx: Context,
        timeout: Optional[float] = 180.0
    ):
        super().__init__(timeout=timeout)
        self.embeds: list[Embed] = embeds
        self.current_page: int = 0
        self.ctx: Context = ctx
        self.message: Optional[Message] = None
        self.clear_items()
        self.fill_items()

    @property
    def page_num(self) -> int:
        return len(self.embeds)


    def fill_items(self) -> None:
        use_last_and_first: bool = (self.page_num >=2)
        if use_last_and_first:
            self.add_item(self.to_first_page)
        self.add_item(self.to_previous_page)
        self.add_item(self.to_current_page)
        if use_last_and_first:
            self.add_item(self.to_next_page)
        self.add_item(self.to_last_page)
        return


    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user and (interaction.user.id in self.ctx.bot.owner_ids | {self.ctx.author.id}):
            return True
        await interaction.response.send_message('This pagination menu cannot be controlled by you, sorry!', ephemeral=True)
        return False


    async def on_timeout(self) -> None:
        if self.message:
            await self.message.delete()


    def update_labels(self, page_number: int) -> None:
        self.to_first_page.disabled = (page_number == 0)

        self.to_current_page.label = f'{self.current_page + 1}/{self.page_num}'
        self.to_next_page.disabled = False
        self.to_previous_page.disabled = False
        self.to_first_page.disabled = False

        self.to_last_page.disabled = (page_number + 1 >= self.page_num)

        if self.to_last_page.disabled:
            self.to_last_page.disabled = True
            self.to_next_page.disabled = True
        if page_number == 0:
            self.to_previous_page.disabled = True
            self.to_first_page.disabled = True

        return


    async def show_checked_page(self, interaction: Interaction ,page_number: int) -> None:
        if 0 <= page_number < self.page_num:
            try:
                await self.show_page(interaction,page_number)
            except IndexError:
                pass
        return


    async def show_page(self, interaction: Interaction ,page_number: int) -> None:
        self.current_page = page_number
        self.update_labels(page_number)

        if interaction.response.is_done():
            if self.message:
                await self.message.edit(embed=self.embeds[self.current_page],view=self)
        else:
            await interaction.response.edit_message(embed=self.embeds[self.current_page],view=self)

        return


    async def start(self,ephemeral: bool = False) -> None:
        self.update_labels(0)
        self.message = await self.ctx.send(
            view = self,
            embed=self.embeds[0],
            ephemeral=ephemeral
        )


    @button(label='≪', style=ButtonStyle.grey)
    async def to_first_page(self, interaction: Interaction, button: Button):
        await self.show_page(interaction,0)
        return


    @button(label='<', style=ButtonStyle.blurple)
    async def to_previous_page(self, interaction: Interaction, button: Button):
        await self.show_checked_page(interaction,self.current_page-1)
        return


    @button(label='Current', style=ButtonStyle.grey, disabled=True)
    async def to_current_page(self, interaction: Interaction, button: Button):
        pass


    @button(label='>', style=ButtonStyle.blurple)
    async def to_next_page(self, interaction: Interaction, button: Button):
        await self.show_checked_page(interaction,self.current_page+1)
        return


    @button(label='≫',style=ButtonStyle.gray)
    async def to_last_page(self, interaction: Interaction, button: Button):
        await self.show_checked_page(interaction,self.page_num -1)
        return
