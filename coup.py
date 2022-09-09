import discord
import copy
import random
import re

# TODO add both/bofa to die instantly

emotes = {
    "Duke": "<:duke:688140221992402989>",
    "Contessa": "<:contessa:688143214955331724>",
    "Assassin": "<:assassin:688141335450091698>",
    "Ambassador": "<:ambassador:688142035613646886>",
    "Captain": "<:captain:688142823006273593>"
}

coinParser = re.compile("[+-]?\d+")

def dnam(user):
    # TODO Use real names, prompt on !join, and store in text file for laterf
    return user.display_name.replace('\\', '\\\\')


def cardFormatter(cds):
        if(len(cds) == 1):
            cd = cds[0]
            return f"a{'n' if cd[0] == 'A' else ''} **{cd}**"

        if(len(cds) == 2):
            [c1,c2] = cds
            if(c1 == c2):
                return f"***Double {c1}s***"
            else:
                return f"{cardFormatter([c1])} and {cardFormatter([c2])}"
        elif(len(cds) == 3):
            [c1,c2, c3] = cds
            return f"{cardFormatter([c1])}, {cardFormatter([c2])}, and {cardFormatter([c3])}"
        elif(len(cds) == 4):
            [c1,c2,c3,c4] = cds
            return f"{cardFormatter([c1])}, {cardFormatter([c2])}, {cardFormatter([c3])}, and {cardFormatter([c4])}"


def coinFormatter(cns):
    return f"**{cns} coin{'' if cns == 1 else 's'}**"

async def newContext(bot, msgData):
    print("\tStarting a new game of Coup...")
    await msgData.channel.send("Starting a game of Coup... Type `^join` to join, `^start` to start, or `^help` for a list of all commands!")

    # TODO start a timer, kill the game if no one joins in time.

    inst = CoupInstance(bot, msgData.channel)
    inst.players[msgData.author] = None
    inst.playerOrder.append(msgData.author)
    return inst


class CoupInstance:
    def __init__(self, bot, channel):
        self.bot = bot
        self.channel = channel
        self.name = "Coup"

        self.playing = False
        self.playerOrder = []  # [member] order or turns
        # {member : {"cards":[str], "coins":int}, "dropped":[str]}
        self.players = dict()
        self.deck = list()
        self.turnNum = 0
        self.discarded = list()
        self.bank = 50
        self.pendingAmbassador = None
        self.ambyMessage = None

    def getTurnOrder(self):
        return ' -> '.join("**" + dnam(member) + "**" for member in self.playerOrder)

    async def handleAddReact(self, reaction, user, dm):
        if(self.pendingAmbassador == user and reaction.message.id == self.ambyMessage.id):
            twos = [react for react in reaction.message.reactions if react.count > 1]
            if(len(twos) == 2):
                numEmotes = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3}
                nums = sorted(numEmotes[two.emoji] for two in twos)
                cds = self.players[user]["cards"]
                ret1 = cds.pop(nums[1])
                ret2 = cds.pop(nums[0])
                
                await user.send(f"You put back {cardFormatter([ret1, ret2])}.\nYou now have {cardFormatter(cds)}.")
                await self.channel.send(f"After deliberation, **{dnam(self.pendingAmbassador)}** puts back 2 cards. They now have {len(cds)}.")

                self.deck.append(ret1)
                self.deck.append(ret2)
                
                self.bot.userContexts[user] = None
                self.ambyMessage = None
                self.pendingAmbassador = None

    async def handleRemoveReact(self, reaction, user, dm):
        pass

    async def handleMsg(self, msgData, dm):
        msg = msgData.content.lower()
        if(dm):
            pass
        else:
            if(msg.startswith("^play")):
                print(
                    f"\t\t[{msg.author.name}] tried to start game when game was already in progress.")
                await self.channel.send(
                    f"Please exit the existing game before starting a new one!")

            if(msg.startswith("^join")):
                await self.tryJoin(msgData)
            elif(msg.startswith("^start") or msg.startswith("^begin")):
                await self.tryStart(msgData)
            elif(msg.startswith("^stop") or msg.startswith("^end")):
                await self.tryStop()
            elif(msg.startswith("^help")):
                await self.tryHelp(msgData)
            elif(msg.startswith("^query") or msg.startswith("^observe")):
                await self.tryQuery()
            elif(msg.startswith("^coin")):
                await self.tryCoin(msgData)
            elif(msg.startswith("^look")):
                await self.tryLook(msgData)
            elif(msg.startswith("^discard")):
                await self.tryDiscard(msgData)
            elif(msg.startswith("^reveal")):
                await self.tryReveal(msgData)
            elif(msg.startswith("^cede")):
                await self.tryCede(msgData)
            elif(msg.startswith("^income")):
                await self.tryIncome(msgData)
            elif(msg.startswith("^ambassador") or msg.startswith("^amby")):
                await self.tryAmbassador(msgData)
            elif(msg.startswith("^trade") or msg.startswith("^exchange") or msg.startswith("^swap")):
                await self.tryTrade(msgData)

    async def tryLook(self, msgData):
        print(f"\t\tAttempted look.")
        member = msgData.author

        if(not self.playing):
            print("\t\t\tFailed look because no game in progress.")
            await self.channel.send(f"{member.mention}, you can't look because there is no game in progress!")
            return

        if(member in self.players):
            if(member == self.pendingAmbassador):
                print(f"\t\t\tFailed to single look because pending ambassador!")
                await self.channel.send(f"{member.mention}, please finish using ambassador before trying to look!")
                return

            print(f"\t\t\tDid single look.")
            pdat = self.players[member]
            await member.send(f"You have {cardFormatter(pdat['cards'])}, with {coinFormatter(pdat['coins'])}.")
        else:
            print(f"\t\t\tDid global look.")
            strs = []
            for player in self.playerOrder:
                pdat = self.players[player]
                strs.append(f"**{dnam(player)}** has {cardFormatter(pdat['cards'])}, with {coinFormatter(pdat['coins'])}.")
            await member.send("\n".join(strs))
            return

    async def tryIncome(self, msgData):
        print("\t\tAttempted income.")

        player = msgData.author

        if(not self.playing):
            print("\t\t\tFailed income because no game in progress.")
            await self.channel.send(f"{mention}, you can't income because there is no game in progress!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to ambassador because not a player.")
            await self.channel.send(f"{mention}, you can't income because you aren't playing!")
            return

        if(self.bank == 0):
            print(f"\t\t\tFailed to income because bank empty.")
            await self.channel.send(f"{mention}, you can't income because the bank is empty!")
            return

        self.bank -= 1
        pdat = self.players[player]
        pdat["coins"] += 1
        await self.channel.send(f"**{dname}** incomes. They now have **{pdat['coins']}**. The bank now has **{self.bank}**.")

    async def tryAmbassador(self, msgData):
        print(f"\t\tAttempted ambassador.")

        player = msgData.author
        mention = player.mention

        if(not self.playing):
            print("\t\t\tFailed ambassador because no game in progress.")
            await self.channel.send(f"{mention}, you can't ambassador because there is no game in progress!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to ambassador because not a player.")
            await self.channel.send(f"{mention}, you can't ambassador because you aren't playing!")
            return

        if(self.pendingAmbassador != None):
            print(f"\t\t\tFailed to ambassador because waiting for ambassador.")
            if(self.pendingAmbassador == player):
                await self.channel.send(f"{mention}, you're already using ambassador! Check your direct messages.")
            else:
                await self.channel.send(f"{mention}, please wait for **{dnam(self.pendingAmbassador)}** to finish using ambassador!")
            return

        self.pendingAmbassador = player
        cds = self.players[player]["cards"]
        
        cds.append(self.deck.pop(random.randrange(len(self.deck))))
        cds.append(self.deck.pop(random.randrange(len(self.deck))))
        await self.channel.send(f"**{dnam(player)}** grabs 2 cards from the deck and considers them...")
        await player.send(f"You now hold the following cards. Please pick **2** to **put back**.")
        self.ambyMessage = await player.send("".join(emotes[card] for card in (self.players[player]["cards"])))
        
        self.bot.userContexts[player] = self
        
        await self.ambyMessage.add_reaction("1️⃣")
        await self.ambyMessage.add_reaction("2️⃣")
        await self.ambyMessage.add_reaction("3️⃣")
        await self.ambyMessage.add_reaction("4️⃣")

        # the rest of this is handled in handleAddReact

    async def tryDiscard(self, msgData):
        player = msgData.author
        mention = player.mention
        dname = dnam(player)

        print(f"\t\tAttempted discard.")

        if(self.pendingAmbassador != None):
            print(f"\t\t\tFailed discard because waiting for ambassador.")
            if(self.pendingAmbassador == player):
                await self.channel.send(f"{mention}, you can't discard becuase you're using ambassador! Check your direct messages.")
            else:
                await self.channel.send(f"{mention}, please wait for **{dnam(self.pendingAmbassador)}** to finish using ambassador!")
            return

        if(not self.playing):
            print("\t\t\tFailed discard because no game in progress.")
            await self.channel.send(f"{mention}, you can't discard because there is no game in progress!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to discard because not a player.")
            await self.channel.send(f"{mention}, you can't discard anything because you aren't playing!")
            return

        args = msgData.content.split(" ")[1:]
        pcards = self.players[player]["cards"]
        if(len(pcards) == 2):
            if(len(args) == 0):
                print(f"\t\t\tFailed to discard because 2 cards with no args.")
                await self.channel.send(f"{mention}, you have 2 cards. Please specify which one to discard! e.g.: `^discard 1` or `^discard 2`")
                return

            arg = args[0]
            if(arg == "1" or arg == "1st"):
                print(f"\t\t\tDiscarded 1st card.")
                disc = pcards.pop(0)
                self.discarded.append(disc)
                await self.channel.send(f"**{dname}** discards {cardFormatter([disc])}, leaving them with 1 card.")
                await player.send(f"You now have {cardFormatter(pcards)}.")
                return
            if(arg == "2" or arg == "2nd"):
                print(f"\t\t\tDiscarded 2nd card.")
                disc = pcards.pop(1)
                self.discarded.append(disc)
                await self.channel.send(f"**{dname}** discards {cardFormatter([disc])}, leaving them with 1 card.")
                await player.send(f"You now have {cardFormatter(pcards)}.")
                return

            print(f"\t\t\tFailed to discard because unknown argument.")
            await self.channel.send(f"{mention}, please enter a valid argument! e.g.: `^discard 1` or `^discard 2`")
            return
        else:
            print(f"\t\t\tDiscarded last card.")
            disc = pcards.pop()
            self.discarded.append(disc)
            self.playerOrder.remove(player)
            self.bank += self.players[player]["coins"]
            del self.players[player]
            await self.channel.send(f"**{dname}** discards {cardFormatter([disc])}. They are now out of the game!")
            
            rem = len(self.players)
            if(rem == 1):
                winner = self.playerOrder[0]
                winnerDat = self.players[winner]
                await self.channel.send(f"\n***{dnam(winner)}*** *has won the game!*\nThey ended with {cardFormatter(winnerDat['cards'])}, and {coinFormatter(winnerDat['coins'])}.")
                await self.stopGame()
            elif(rem == 0):
                await self.channel.send(f"Wait, what?")
                await self.stopGame()
            else:
                await self.channel.send(f"There are now {rem} players remaining.")

    async def tryReveal(self, msgData):
        player = msgData.author
        mention = player.mention
        dname = dnam(player)

        print(f"\t\tAttempted reveal.")
        if(self.pendingAmbassador != None):
            print(f"\t\t\tFailed reveal because waiting for ambassador.")
            if(self.pendingAmbassador == player):
                await self.channel.send(f"{mention}, you can't reveal becuase you're using ambassador! Check your direct messages.")
            else:
                await self.channel.send(f"{mention}, please wait for **{dnam(self.pendingAmbassador)}** to finish using ambassador!")
            return

        if(not self.playing):
            print("\t\t\tFailed reveal because no game in progress.")
            await self.channel.send(f"{mention}, you can't reveal because there is no game in progress!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to reveal because not a player.")
            await self.channel.send(f"{mention}, you can't reveal anything because you aren't playing!")
            return

        args = msgData.content.split(" ")[1:]
        pcards = self.players[player]["cards"]
        if(len(pcards) == 2):
            if(len(args) == 0):
                print(f"\t\t\tFailed to reveal because 2 cards with no args.")
                await self.channel.send(f"{mention}, you have 2 cards. Please specify which one to reveal! e.g.: `^reveal 1` or `^reveal 2`")
                return

            arg = args[0]
            if(arg == "1" or arg == "1st"):
                print(f"\t\t\tRevealed 1st card.")
                await self.channel.send(f"**{dname}** turns over their card to reveal... {cardFormatter([pcards[0]])}!")
                return
            if(arg == "2" or arg == "2nd"):
                print(f"\t\t\tDiscarded 2nd card.")
                await self.channel.send(f"**{dname}** turns over their card to reveal... {cardFormatter([pcards[1]])}!")
                return

            print(f"\t\t\tFailed to reveal because unknown argument.")
            await self.channel.send(f"{mention}, please enter a valid argument! e.g.: `^reveal 1` or `^reveal 2`")
            return
        else:
            print(f"\t\t\tRevealed last card.")
            await self.channel.send(f"**{dname}** turns over their card to reveal... {cardFormatter(pcards)}!")
            return

    async def tryTrade(self, msgData):
        player = msgData.author
        mention = player.mention
        dname = dnam(player)

        print(f"\t\tAttempted trade.")

        if(self.pendingAmbassador != None):
            print(f"\t\t\tFailed trade because waiting for ambassador.")
            if(self.pendingAmbassador == player):
                await self.channel.send(f"{mention}, you can't trade becuase you're using ambassador! Check your direct messages.")
            else:
                await self.channel.send(f"{mention}, please wait for **{dnam(self.pendingAmbassador)}** to finish using ambassador!")
            return

        if(not self.playing):
            print("\t\t\tFailed trade because no game in progress.")
            await self.channel.send(f"{mention}, you can't trade because there is no game in progress!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to trade because not a player.")
            await self.channel.send(f"{mention}, you can't trade in a card because you aren't playing!")
            return

        args = msgData.content.split(" ")[1:]
        pcards = self.players[player]["cards"]
        if(len(pcards) == 2):
            if(len(args) == 0):
                print(f"\t\t\tFailed to trade because 2 cards with no args.")
                await self.channel.send(f"{mention}, you have 2 cards. Please specify which one to trade in! e.g.: `^trade 1` or `^trade 2`")
                return

            arg = args[0]
            if(arg == "1" or arg == "1st"):
                print(f"\t\t\tTraded 1st card.")
                self.deck.append(pcards.pop(0))
                pcards.insert(0, self.deck.pop(random.randrange(len(self.deck))))
                await self.channel.send(f"**{dname}** hands in their card and takes a random one from the deck.")
                await player.send(f"You now have {cardFormatter(pcards)}.")
                return
            if(arg == "2" or arg == "2nd"):
                print(f"\t\t\tTraded 2nd card.")
                self.deck.append(pcards.pop(1))
                pcards.append(self.deck.pop(random.randrange(len(self.deck))))
                await self.channel.send(f"**{dname}** hands in their card and takes a random one from the deck.")
                await player.send(f"You now have {cardFormatter(pcards)}.")
                return

            print(f"\t\t\tFailed to trade because unknown argument.")
            await self.channel.send(f"{mention}, please enter a valid argument! e.g.: `^trade 1` or `^trade 2`")
            return
        else:
            print(f"\t\t\tTraded last card.")
            self.deck.append(pcards.pop(0))
            pcards.append(self.deck.pop(random.randrange(len(self.deck))))
            await self.channel.send(f"**{dname}** hands in their card and takes a random one from the deck.")
            await player.send(f"You now have {cardFormatter(pcards)}.")
            return

    async def tryCede(self, msgData):
        args = msgData.content.split(" ")[1:]
        player = msgData.author
        mention = player.mention
        dname = dnam(player)
        pdat = self.players[player]

        print(f"\t\tAttempted cede.")

        if(not self.playing):
            print("\t\t\tFailed cede because no game in progress.")
            await self.channel.send(f"{mention}, you can't cede because there is no game in progress!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to cede because not a player.")
            await self.channel.send(f"{mention}, you have no money to lose because you aren't playing!")
            return

        if(len(args) == 0):
            print(f"\t\t\tFailed to cede because no arguments.")
            await self.channel.send(f"{mention}, please specify who to cede money to! e.g.: `^cede @thief`")
            return

        mens = msgData.mentions
        if(len(mens) == 0):
            print(f"\t\t\tFailed to cede because no mentions.")
            await self.channel.send(f"{mention}, please use mentions to specify who to cede money to! e.g.: `^cede @thief`")
            return

        if(pdat["coins"] == 0):
            print(f"\t\t\tFailed to use coin because no coins.")
            await self.channel.send(f"Tragically, **{dname}** loses all 0 of their coins and is now double-bankrupt.")
            return
        
        thief = mens[0]

        if(thief == self.bot.client.user):
            print(f"\t\t\tTried to cede to bot.")
            await self.channel.send(f"**{dname}** cedes their entire {coinFormatter(pdat['coins'])} to ***HalperBot***.\nWhat, you didn't know? *The house always wins.*")
            self.bank += pdat["coins"]
            pdat["coins"] = 0
            return

        if(thief not in self.players):
            print(f"\t\t\tFailed to use coin because thief is not playing.")
            await self.channel.send(f"{mention}, you can't cede coins to **{thief.name}** because they aren't playing!")
            return
        
        if(thief == player):
            print(f"\t\t\tTried to cede to self.")
            await self.channel.send(file=discord.File("./thieves.jpg"))
            await self.channel.send(f"***OUTSTANDING PLAY***\n**{dname}** attempts to steal their own money. They successfully fail to succeed.\n")
            return

        dname2 = dnam(thief)
        pdat2 = self.players[thief]
        if(pdat["coins"] == 1):
            print(f"\t\t\tCeded 1 coin.")
            pdat["coins"] -= 1
            pdat2["coins"] += 1
            await self.channel.send(f"**{dname}** gives their last coin to **{dname2}**.\n**{dname}** now has **{pdat['coins']}**, and **{dname2}** now has **{pdat2['coins']}**.")
        else:
            print(f"\t\t\tCeded 2 coin.")
            pdat["coins"] -= 2
            pdat2["coins"] += 2
            await self.channel.send(f"**{dname}** cedes **2 coins** to **{dname2}**.\n**{dname}** now has **{pdat['coins']}**, and **{dname2}** now has **{pdat2['coins']}**.")

    async def tryCoin(self, msgData):
        args = msgData.content.split(" ")[1:]
        player = msgData.author
        mention = player.mention
        dname = dnam(player)

        print(f"\t\tAttempted coin operation.")

        if(not self.playing):
            print("\t\t\tFailed coin operation because no game in progress.")
            await self.channel.send(f"{mention}, you can't use the economy because there is no economy!")
            return

        if(player not in self.players):
            print(f"\t\t\tFailed to use coin because not a player.")
            await self.channel.send(f"{mention}, you can't use the economy because you aren't playing!")
            return
        
        if(len(args) == 0):
            print(f"\t\t\tFailed to use coin because no arguments.")
            await self.channel.send(f"{mention}, please specify an argument! e.g.: `^coin +1` or `^coin -3`")
            return

        arg = args[0]
        if(arg == "+0" or arg == "0"):
            print(f"\t\t\tFailed to use coin because +0 argument.")
            await self.channel.send(f"**{dname}** withdraws a whopping ***0 Coins*** from the bank! Don't spend it all in one place!")
            return

        if(arg == "-0"):
            print(f"\t\t\tFailed to use coin because -0 argument.")
            await self.channel.send(f"Wow! **{dname}** just spent an unprecedented sum of ***Absolutely Nothing***!")
            return

        if(coinParser.match(arg)):
            num = int(arg)
            if(num < 0):
                num = -num
                cns = self.players[player]["coins"]
                if(num > cns):
                    print(f"\t\t\tFailed to spend coins because debt.")
                    await self.channel.send(f"**{mention}**, you can't spend **{num} coin{'' if num == 1 else 's'}** because you only have **{cns}**!")
                else:
                    print(f"\t\t\tSpent {num} coins.")
                    self.bank += num
                    self.players[player]["coins"] -= num
                    await self.channel.send(f"**{dname}** spends **{num} coin{'' if num == 1 else 's'}**. They now have **{self.players[player]['coins']}**. The bank now has **{self.bank}**.")
            else:
                if(num > self.bank):
                    print(f"\t\t\tFailed to get coins because not enough in bank.")
                    await self.channel.send(f"**{mention}**, you can't withdraw **{num} coin{'' if num == 1 else 's'}** because the bank only has **{self.bank}**!")
                else:
                    print(f"\t\t\tGot {num} coins from bank.")
                    self.bank -= num
                    self.players[player]["coins"] += num
                    await self.channel.send(f"**{dname}** withdraws **{num} coin{'' if num == 1 else 's'}**. They now have **{self.players[player]['coins']}**. The bank now has **{self.bank}**.")
            return

        print(f"\t\t\tFailed to use coin because unparseable argument.")
        await self.channel.send(f"**{dname}**, please enter a valid argument! e.g.: `^coin +1` or `^coin -3`")
        return

    async def tryStart(self, msgData):
        if(self.playing):
            print(f"\t\tFailed to start because game already in progress.")
            await self.channel.send(f"{msgData.author.mention}, a game is already in progress!")
            return

        if(len(self.players) < 3):
            print(
                f"\t\tFailed to start because only [{len(self.players)}] players.")
            await self.channel.send(f"You need at least 3 players to start!")
            return

        await self.startGame()

    async def tryHelp(self, msgData):
        print("\t\tHelp requested.")
        await msgData.author.send(
            f"""```Coup Commands:
^play coup          : start a new game
^join               : join the current game
^start, ^begin      : start playing
^stop, ^end         : end the current game

^query, ^observe    : look around, see how many coins and cards people have
^look               : remind yourself of your own cards & coins

^ambassador, !amby  : grab 2 cards from the deck, pick 0 or 1 of them to keep, and return any 2
^cede (name)        : give 2 coins to someone else

^discard (1 or 2)   : discard a card, leaving it face up
^reveal (1 or 2)    : show your card to the table
^trade (1 or 2)     : trade a card for a random one in the deck.

^coin (+n)          : take n coins from the bank
^coin (-n)          : spend n coins```""")
        return

    async def tryQuery(self):
        print("\t\tQuery requested.")

        if(not self.playing):
            await self.channel.send("There is no game in progress!")
            return

        playerInfos = []
        for player in self.playerOrder:
            data = self.players[player]
            st = f"- **{dnam(player)}**"

            cards = len(data["cards"])
            st += f" has **{cards} card{'' if (cards == 1) else 's'}**"
            coins = data["coins"]
            st += f" and **{coins} coin{'' if (coins == 1) else 's'}**."
            playerInfos.append(st)
        playerInfos = '\n'.join(playerInfos)

        killedStr = "No cards have been discarded."
        if(len(self.discarded) > 0):
            killedStr = f"The following cards have been discarded:"

        await self.channel.send(
            f"""There are {len(self.players)} players remaining.
There are {coinFormatter(self.bank)} in the bank, and **{len(self.deck)}** cards in the deck.
The current order of turns is:\n{self.getTurnOrder()}
{playerInfos}
{killedStr}""")
        if(len(self.discarded) > 0):
            await self.channel.send(f"{''.join(emotes[card] for card in sorted(self.discarded))}")
        return

    async def tryJoin(self, msgData):
        player = msgData.author
        name = player.name
        dname = dnam(player)

        print(f"\t\t[{name}] tried to join.")

        if(self.playing):
            print(
                f"\t\t\t[{name}] failed to join because the game is in progress.")
            await self.channel.send(
                f"Sorry, **{dname}**. A game is already in progress!")
            return

        if(len(self.players) >= 6):
            print(
                f"\t\t\t[{name}] failed to join because there are too many players.")
            await self.channel.send(
                f"Sorry, **{dname}**. There are already 6 players!")
            return

        if(player in self.players):
            print(
                f"\t\t\t[{name}] failed to join because they are already playing.")
            await self.channel.send(f"You're already playing, **{dname}**...")
            return

        self.players[player] = None
        self.bank -= 2
        self.playerOrder.append(player)
        print(f"\t\t\t[{name}] joined.")
        await self.channel.send(f"**{dname}** joins the game!")
        return

    async def tryStop(self):
        await self.stopGame()

    async def stopGame(self):
        print(f"\t\tEnding game.")
        del self.bot.activeContexts[self.channel]
        await self.channel.send(f"Ending the game... Type `^play coup` to start a new game!")

    async def startGame(self):
        print(f"\t\tStarting game.")

        self.playing = True

        self.deck = [
            "Duke", "Duke", "Duke",
            "Contessa", "Contessa", "Contessa",
            "Assassin", "Assassin", "Assassin",
            "Ambassador", "Ambassador", "Ambassador",
            "Captain", "Captain", "Captain"
        ]
        random.shuffle(self.deck)

        # shuffle, but keep the initiating player as first
        starter = self.playerOrder.pop(0)
        random.shuffle(self.playerOrder)
        self.playerOrder.insert(0, starter)

        for player in self.playerOrder:
            pdeck = [self.deck.pop(), self.deck.pop()]
            self.players[player] = {
                "cards": pdeck,
                "coins": 2,
                "dropped": []
            }

            await player.send(f"You start with {cardFormatter(pdeck)}. Good luck!")

        await self.channel.send(f"""
===== ***Let the game begin!*** =====
Here is the order of turns:
{self.getTurnOrder()}""")
