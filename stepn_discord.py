import discord

client = discord.Client()


@client.event
async def on_ready(messages_dict: dict):
    g_roles: dict = {}

    for guild in client.guilds:
        for role in guild.roles:
            g_roles[role.name] = role

        for channel in guild.channels:
            if channel.name == 'stepn-marketplace':
                messages = messages_dict["messages"]

                if messages_dict.get('mention'):
                    final_message = f"{g_roles[messages_dict.get('mention')].mention}\n"
                else:
                    final_message = ''

                for message, image in messages:
                    final_message = f"{final_message}{message}{image}"

                await channel.send(final_message)

    await client.close()
