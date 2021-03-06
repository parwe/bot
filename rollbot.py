import discord
from discord.ext import commands
from time import localtime, time, sleep, asctime
from aiohttp.errors import ClientOSError, ClientError

from Core.constants import *
from Managers.SessionManagers.Bots.blackjack_bot import BlackjackBot
from Managers.SessionManagers.Bots.bombtile_bot import BombtileBot
from Managers.SessionManagers.Bots.hammer_race_bot import HammerRaceBot
from Managers.SessionManagers.Bots.meso_plz_bot import MesoPlzBot
from Managers.SessionManagers.Bots.roll_game_bot import RollGameBot
from Managers.SessionManagers.Bots.scratch_card_bot import ScratchCardBot
from Managers.SessionManagers.Bots.slot_machine_bot import SlotMachineBot
from Managers.SessionManagers.game_initializer import SessionOptions
from Managers.channel_manager import ChannelManager
from Managers.local_data_manager import LocalDataManager
from Managers.remote_data_manager import RemoteDataManager
from Managers.statistics import StatisticsBot
from MesoPlz.meso_plz import MesoPlz
from RollGames.roll import Roll
from Slots.modes import *
from discordtoken import TOKEN

description = '''A bot to roll for users and provide rolling games.'''
bot = commands.Bot(command_prefix='/', description=description)
client = discord.Client()
blackjack_bot = None
channel_manager = None
hammer_race_bot = None
slot_machine_bot = None
scratchcard_bot = None
rollgame_bot = None
bombtile_bot = None
mesoplz_bot = None
stats_bot = None


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-' * len(bot.user.id))
    initialize_modules()


def get_data_manager():
    try:
        return RemoteDataManager(bot)
    except:
        print("No connection to the database. Falling back to local data.")
        return LocalDataManager(bot)


def initialize_modules():
    global blackjack_bot
    global channel_manager
    global hammer_race_bot
    global slot_machine_bot
    global scratchcard_bot
    global rollgame_bot
    global bombtile_bot
    global mesoplz_bot
    global stats_bot

    data_manager = get_data_manager()
    channel_manager = ChannelManager(bot)
    session_options = SessionOptions(bot, channel_manager, data_manager)

    blackjack_bot = BlackjackBot(session_options)
    hammer_race_bot = HammerRaceBot(session_options)
    slot_machine_bot = SlotMachineBot(session_options)
    scratchcard_bot = ScratchCardBot(session_options)
    rollgame_bot = RollGameBot(session_options)
    bombtile_bot = BombtileBot(session_options)
    mesoplz_bot = MesoPlzBot(session_options)
    stats_bot = StatisticsBot(bot, data_manager)


@bot.command(pass_context=True)
async def roll(ctx, max=100):
    """Rolls a random integer between 1 and max. 100 is the default max if another is not given."""
    roller = ctx.message.author

    if max < 1:
        await bot.say('1 is the minimum for rolls.')
        return

    roll = random.randint(1, max)

    try:
        channel = ctx.message.channel
        game = channel_manager.get_game(channel)
        await game.add_roll(Roll(roll, roller, max))
    except AttributeError:
        print("Existing game is not accepting rolls.")

    await bot.say(f"{roller.display_name} rolled {roll} (1-{max})")


@bot.group(pass_context=True)
async def rollgame(ctx):
    if ctx.invoked_subcommand is None:
        await bot.say("You must specify a type of roll game. Try `/rollgame normal`")


@rollgame.command(pass_context=True)
async def normal(ctx, bet=100):
    await rollgame_bot.create_normal_roll(ctx, bet)


@rollgame.command(pass_context=True)
async def difference(ctx, bet=100):
    await rollgame_bot.create_difference_roll(ctx, bet)


@rollgame.command(pass_context=True)
async def countdown(ctx, bet=100):
    await rollgame_bot.create_countdown_roll(ctx, bet)


@bot.command(pass_context=True)
async def join(ctx):
    """ Allows the user to join the channel's active game. """
    await channel_manager.check_valid_join(ctx)


@bot.command(pass_context=True)
async def blackjack(ctx):
    await blackjack_bot.create_game(ctx)


@bot.command(pass_context=True)
async def hit(ctx):
    await blackjack_bot.make_move(ctx, 'hit')


@bot.command(pass_context=True)
async def stand(ctx):
    await blackjack_bot.make_move(ctx, 'stand')


@bot.command(pass_context=True)
async def split(ctx):
    await blackjack_bot.make_move(ctx, 'split')


@bot.command(pass_context=True)
async def doubledown(ctx):
    await blackjack_bot.make_move(ctx, 'doubledown')


# End Blackjack commands

@bot.command(pass_context=True)
async def quit(ctx):
    """ TODO leave the current game """


@bot.command(pass_context=True)
async def askhammer(ctx):
    await hammer_race_bot.create_classic_race(ctx)


@bot.command(pass_context=True)
async def compare(ctx):
    await hammer_race_bot.create_comparison(ctx)


@bot.command(pass_context=True)
async def versushammer(ctx):
    await hammer_race_bot.create_versus(ctx)


@bot.command(pass_context=True)
async def forcestart(ctx):
    await channel_manager.check_valid_forcestart(ctx)


@bot.command(pass_context=True)
async def addai(ctx):
    # Add an AI to the game. The game must implement add_ai() for this to work.
    await channel_manager.check_valid_add_ai(ctx)


@bot.command(pass_context=True)
async def fill(ctx):
    # TODO Fill the remaining player slots with AI players.
    await channel_manager.check_valid_add_ai(ctx)


@bot.command(pass_context=True)
async def butts(ctx):
    num_butts = random.randint(1, 20)
    butts_message = [':peach:' * num_butts]
    stats_bot.update_butts(ctx, num_butts)
    if num_butts > 1:
        butts_message.append(f'```{num_butts} Butts```')
    else:
        butts_message.append(f'```{num_butts} Butt```')
    await bot.say(''.join(butts_message))


@bot.command(pass_context=True)
async def totalbutts(ctx):
    await stats_bot.total_butts(ctx)


@bot.command(pass_context=True)
async def globalbutts():
    await stats_bot.global_butts()


@bot.command(pass_context=True)
async def stats(ctx):
    await stats_bot.stats(ctx)


@bot.command(pass_context=True)
async def melons(ctx):
    num_melons = random.randint(0, 10) * 2
    stats_bot.update_melons(ctx, num_melons)
    if num_melons > 0:
        await bot.say(':melon:' * num_melons + f'```{num_melons} Melons```')
    else:
        await bot.say('```No Melons```')


@bot.command(pass_context=True)
async def eggplants(ctx):
    amount = random.randint(0, 20)
    stats_bot.update_eggplants(ctx, amount)
    if amount > 0:
        await bot.say(':eggplant:' * amount + f'```{amount} Eggplants```')
    else:
        await bot.say('```No dongerinos```')


@bot.command(pass_context=True)
async def fuqs(ctx):
    amount = random.randint(0, 20)
    stats_bot.update_fuqs(ctx, amount)
    if amount > 0:
        await bot.say('<:dafuq:451983622140854277>' * amount + f'```{amount} fuqs given```')
    else:
        await bot.say('```No fuqs given```')


@bot.command(pass_context=True)
async def slots(ctx):
    await slot_machine_bot.initialize_slots(ctx)


@bot.command(pass_context=True)
async def bigslots(ctx):
    await slot_machine_bot.initialize_bigslots(ctx)


@bot.command(pass_context=True)
async def giantslots(ctx):
    await slot_machine_bot.initialize_giantslots(ctx)


@bot.command(pass_context=True)
async def mapleslots(ctx):
    await slot_machine_bot.initialize_mapleslots(ctx)


@bot.command(pass_context=True)
async def bigmapleslots(ctx):
    await slot_machine_bot.initialize_bigmapleslots(ctx)


@bot.command(pass_context=True)
async def giantmapleslots(ctx):
    await slot_machine_bot.initialize_giantmapleslots(ctx)

@bot.command(pass_context=True)
async def pokeslots(ctx):
    await slot_machine_bot.initialize_pokeslots(ctx)


@bot.command(pass_context=True)
async def bigpokeslots(ctx):
    await slot_machine_bot.initialize_bigpokeslots(ctx)


@bot.command(pass_context=True)
async def giantpokeslots(ctx):
    await slot_machine_bot.initialize_giantpokeslots(ctx)


@bot.command(pass_context=True)
async def hammerpot(ctx):
    await scratchcard_bot.create_hammerpot(ctx)


@bot.command(pass_context=True)
async def scratchcard(ctx):
    await scratchcard_bot.create_classic(ctx)


@bot.command(pass_context=True)
async def pick(ctx):
    await scratchcard_bot.pick_line(ctx)


@bot.command(pass_context=True)
async def scratch(ctx):
    await scratchcard_bot.scratch(ctx)


@bot.command()
async def scratchbutts():
    pick_random = random.randint(0, len(SCRATCH_BUTTS) - 1)
    message = ':peach:' + SCRATCH_BUTTS[pick_random]
    await bot.say(message)


@bot.command(pass_context=True)
async def mesoplz(ctx):
    await mesoplz_bot.mesos_plz(ctx)


@bot.command(pass_context=True)
async def gold(ctx, query=None):
    await stats_bot.query_gold(ctx, query)


@bot.command(pass_context=True)
async def gold_stats(ctx, query=None):
    await stats_bot.query_gold_stats(ctx, query)


@bot.command(pass_context=True)
async def winnings(ctx, query=None):
    await stats_bot.query_winnings(ctx, query)


@bot.command(pass_context=True)
async def losses(ctx, query=None):
    await stats_bot.query_losses(ctx, query)


@bot.command(pass_context=True)
async def flip(ctx):
    await bombtile_bot.flip(ctx)


@bot.command(pass_context=True)
async def bombtile(ctx):
    await bombtile_bot.create_bombtile(ctx)


bot.remove_command('help')


@bot.group(pass_context = True)
async def help(ctx):
    if ctx.invoked_subcommand is None:
        await bot.say(BASIC_COMMANDS)


@help.command()
async def slots():
    await bot.say(SLOTS_COMMANDS)


@help.command()
async def blackjack():
    await bot.say(BLACKJACK_COMMANDS)


@help.command()
async def rollgame():
    await bot.say(ROLLGAME_COMMANDS)


@help.command()
async def scratchcard():
    await bot.say(SCRATCHCARD_COMMANDS)


@help.command()
async def hammerrace():
    await bot.say(HAMMERRACE_COMMANDS)


@bot.command(alias='8ball')
async def eightball():
    pick_random = random.randint(0, len(EIGHTBALL_RESPONSES) - 1)
    await bot.say(EIGHTBALL_RESPONSES[pick_random])


try:
    start = time()
    print("Start running at " + asctime(localtime(start)))
    bot.run(TOKEN)
except ClientOSError as ex:
    end = time()
    print("End running at " + asctime(localtime(end)) + ". Ran for " + str(end - start) + " seconds. "
                                           "Caused by ClientOSError (probably no internet).")
except ClientError as ex:
    end = time()
    print("End running at " + asctime(localtime(end)) + ". Ran for " + str(end - start) + " seconds. "
                                                                    "Caused by ClientError.")
except Exception as ex:
    end = time()
    print("End running at " + asctime(localtime(end)) + ". Ran for " + str(end - start) + " seconds. Caused by " +
                                                                           "Unknown reason")

