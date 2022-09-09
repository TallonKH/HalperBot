import discord
import coup
import types
import owo
import re

client = discord.Client()
class HalperBot():
    def __init__(self, client):
        self.client = client
        self.activeContexts = dict() # map of channels to contexts
        self.userContexts = dict() # map of users to contexts

    async def handleMsg(self, msgData):
        isCommand = msgData.content.startswith("^")
        isDM = isinstance(msgData.channel, discord.DMChannel)

        if(not (isDM or isCommand)):
            return

        if(isDM):
            print(f"[{msgData.author.name}] sent DM [{msgData.content}].")
            ctx = self.userContexts.get(msgData.author, None)
            if(ctx == None):
                print("\tNo active context")
            else:
                print(f"\tPassing to context: [{ctx.name}]")

            if(ctx == None):
                # no active context: check for new contexts starting
                msg = msgData.content
            else:
                # active context: try running the command through it
                understood = await ctx.handleMsg(msgData, True)
                if(understood):
                    return
            
            # nothing else succeeded: check context-agnostic commands here
            #
            #
        else:
            print(f"[{msgData.author.name}] sent command [{msgData.content}] in channel [{msgData.channel.name}].")
        
            ctx = self.activeContexts.get(msgData.channel, None)
            if(ctx == None):
                print("\tNo active context")
            else:
                print(f"\tPassing to context: [{ctx.name}]")

            if(ctx == None):
                # no active context: check for new contexts starting
                msg = msgData.content

                # if(msg.startswith("^@#")):
                #     msgData.content = "^play coup"
                #     await self.handleMsg(msgData)
                #     msgData.content = "^start"
                #     await self.handleMsg(msgData)
                #     return

                if(msg.startswith("^play coup")):
                    self.activeContexts[msgData.channel] = await coup.newContext(self, msgData)
                    return
                if(msg.startswith("^owo")):
                    num = 1
                    try:
                        num = int(msg[4:].strip())
                        if num < 1 or num > 50:
                            return
                    except:
                        pass
                    owos = ""
                    for i in range(num):
                        owos += owo.getOwO() + " "
                    await msgData.channel.send(owos)
                    return
            else:
                # active context: try running the command through it
                understood = await ctx.handleMsg(msgData, False)
                if(understood):
                    return
            
            # nothing else succeeded: check context-agnostic commands here
            #
            #

    async def handleAddReact(self, reaction, user):
        isDM = isinstance(reaction.message.channel, discord.DMChannel)

        if(isDM):
            print(f"[{user.name}] reacted to DM [{reaction.message.content}].")
            ctx = self.userContexts.get(user, None)
            if(ctx == None):
                print("\tNo active context")
            else:
                print(f"\tPassing to context: [{ctx.name}]")

            if(ctx == None):
                # no active context: check for new contexts starting
                pass
            else:
                # active context: try running the command through it
                understood = await ctx.handleAddReact(reaction, user, True)
                if(understood):
                    return
        else:
            print(f"[{user.name}] reacted [{reaction.emoji}] in channel [{reaction.message.channel.name}].")

            ctx = self.activeContexts.get(reaction.message.channel, None)
            if(ctx == None):
                print("\tNo active context")
            else:
                print(f"\tPassing to context: [{ctx.name}]")

            if(ctx == None):
                # no active context: check for new contexts starting
                pass
            else:
                # active context: try running the command through it
                understood = await ctx.handleAddReact(reaction, user, False)
                if(understood):
                    return

    async def handleRemoveReact(self, reaction, user):
        isDM = isinstance(reaction.message.channel, discord.DMChannel)

        if(isDM):
            print(f"[{user.name}] unreacted to DM [{reaction.message.content}].")
            ctx = self.userContexts.get(user, None)
            if(ctx == None):
                print("\tNo active context")
            else:
                print(f"\tPassing to context: [{ctx.name}]")

            if(ctx == None):
                # no active context: check for new contexts starting
                pass
            else:
                # active context: try running the command through it
                understood = await ctx.handleRemoveReact(reaction, user, True)
                if(understood):
                    return
        else:
            print(f"[{user.name}] unreacted [{reaction.emoji}] in channel [{reaction.message.channel.name}].")

            ctx = self.activeContexts.get(reaction.message.channel, None)
            if(ctx == None):
                print("\tNo active context")
            else:
                print(f"\tPassing to context: [{ctx.name}]")

            if(ctx == None):
                # no active context: check for new contexts starting
                pass
            else:
                # active context: try running the command through it
                understood = await ctx.handleRemoveReact(reaction, user, False)
                if(understood):
                    return

bot = HalperBot(client)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(msgData):
    if msgData.author == client.user:
        return
    understood = await bot.handleMsg(msgData)

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return

    await bot.handleAddReact(reaction, user)
    
@client.event
async def on_reaction_remove(reaction, user):
    if user == client.user:
        return

    await bot.handleRemoveReact(reaction, user)

with open("./token.txt", "r") as tokenFile:
    client.run(tokenFile.read().strip())
