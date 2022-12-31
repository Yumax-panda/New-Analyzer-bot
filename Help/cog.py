import discord
from discord.ext import commands



class CustomHelp(commands.HelpCommand):
    def __init__(self,show_hidden:bool=True)-> None:
        super().__init__(show_hidden = show_hidden)


    async def send_bot_help(self, mapping) -> None:
        embeds = []
        for cog,cmds in mapping.items():
            if cog is None:
                continue
            disp_cmds = [cmd for cmd in cmds if not cmd.hidden]
            for i in range(0,len(disp_cmds),10):
                embed = discord.Embed(
                    title =cog.qualified_name,
                    description= cog.description or None,
                    color = discord.Colour.yellow()
                )
                for cmd in disp_cmds[i:i+10]:
                    if cmd is None:
                        continue
                    embed.add_field(
                        name = f'___{cmd.brief}___',
                        value = f'```{cmd.usage}```',
                        inline =False
                    )
                embed.set_footer(text = '[Optional]   <Required>')
                embeds.append(embed)
        count = 0
        msg = await self.get_destination().send(embed=embeds[0])
        await msg.add_reaction('◀')
        await msg.add_reaction('▶')
        reaction = None
        def check(reaction,user):
            return user == self.context.author

        while True:
            if str(reaction) == '◀':
                count -=1
                await msg.edit(embed=embeds[(count)%len(embeds)])
            if str(reaction) == '▶':
                count +=1
                await msg.edit(embed=embeds[(count)%len(embeds)])
            try:
                reaction,user = await self.context.bot.wait_for(
                    'reaction_add',
                    timeout= 30.0,
                    check=check
                )
                await msg.remove_reaction(reaction,user)
            except:
                break
        await msg.delete(delay=5.0)



async def setup(bot):
    bot._default_help_command = bot.help_command
    bot.help_command = CustomHelp()