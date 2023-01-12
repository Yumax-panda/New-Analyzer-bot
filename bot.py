from typing import Optional

from discord.ext import commands
import discord

import os
import json
import logging
import asyncio

from Vote.tool import VoteView


config = json.loads(os.environ['CONFIG'])


logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

initial_extensions =[
    'Help.cog',
    'Lounge.cog',
    'HandsUp.cog',
    'Result.cog',
    'Setting.cog',
    'Vote.cog'
]


class AnalyzerBot(commands.Bot):
    def __init__(
        self,
        config:dict= config,
        command_prefix=commands.when_mentioned_or('!'),
        intents: discord.Intents = intents,
        case_insensitive: bool = True,
        owner_ids:Optional[set] = set(config['owner_ids'])
    )-> None:
        super().__init__(
            command_prefix,
            intents=intents,
            case_insensitive=case_insensitive,
            owner_ids=owner_ids
            )
        self.config = config
        self.remove_command('help')


    async def setup_hook(self)-> None:
        self.add_view(VoteView())
        await bot.tree.sync()



bot = AnalyzerBot()


async def update_activity():

    activity = discord.Activity(
        status = discord.Status.online,
        type = discord.ActivityType.watching,
        name = f'{len(bot.guilds)} servers'
    )

    await bot.change_presence(activity=activity)




@bot.event
async def on_ready():
    logging.info('Successfully logged in')
    await update_activity()


@bot.event
async def on_guild_join(guild):
    logging.info(f'join "{guild}" (id: {guild.id})')
    await update_activity()



@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.CommandNotFound):
        return
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send(f'Error: missing required argument "{error.param}"')
        return
    if isinstance(error,commands.CommandOnCooldown):
        await ctx.send('Error: This command is on cool down. Retry in %.0fs'% error.retry_after)
        return
    if isinstance(error,commands.BadArgument):
        await ctx.send(f'Error: BadArgument "{error.args}"')
        return
    if isinstance(error,commands.BotMissingPermissions):
        await ctx.send(f'Error: This command needs the following permissions "{error.missing_permissions}"')
        return
    if isinstance(error,commands.NotOwner):
        await ctx.send('Error: Only owners can use this command.')
    if isinstance(error,commands.CheckFailure):
        return
    if isinstance(error,commands.MissingPermissions):
        await ctx.send(f'Error: This command needs the following permissions "{error.missing_permissions}"')
        return
    raise error


async def main():
    async with bot:
        for extension in initial_extensions:
            await bot.load_extension(extension)
        await bot.start(config['token'])

asyncio.run(main())
