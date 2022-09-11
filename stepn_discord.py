import asyncio
import platform

import discord

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class StepnClient(discord.Client):

    def __init__(self, messages_dict):
        super(StepnClient, self).__init__()
        self.messages_dict = messages_dict

    async def on_ready(self):
        print('Logged in as {0.user}'.format(self))

        g_roles: dict = {}

        for guild in self.guilds:
            for role in guild.roles:
                g_roles[role.name] = role

            for channel in guild.channels:
                if channel.name == 'stepn-marketplace':
                    messages = self.messages_dict["messages"]

                    if messages:
                        if self.messages_dict.get('mention'):
                            mention = f"{g_roles[self.messages_dict.get('mention')].mention}\n"
                            await channel.send(mention)

                        for message, image in messages:
                            embed = discord.Embed()
                            embed.set_image(url=image)
                            await channel.send(message, embed=embed)

        await self.close()
