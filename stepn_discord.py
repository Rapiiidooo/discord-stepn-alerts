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

        for guild in self.guilds:

            g_roles: dict = {}
            g_channels: dict = {}

            for role in guild.roles:
                g_roles[role.name] = role

            for channel in guild.channels:
                g_channels[channel.name] = channel

            if 'stepn-marketplace' in g_channels:
                channel = g_channels['stepn-marketplace']
                messages = self.messages_dict["messages"]

                mention = None
                if messages:
                    if self.messages_dict.get('mention'):
                        mention = f"{g_roles[self.messages_dict.get('mention')].mention}\n"

                    for message, image in messages:
                        if image:
                            embed = discord.Embed()
                            embed.set_image(url=image)
                            await channel.send(f"{mention}{message}", embed=embed)
                        else:
                            await channel.send(f"{mention}{message}")

        await self.close()
