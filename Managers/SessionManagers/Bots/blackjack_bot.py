import asyncio

from Blackjack.blackjack import Blackjack
from Blackjack.join_timer import BlackjackJoinTimer
from Core.constants import GAME_ID
from Core.time_limit import TimeLimit
from Managers.SessionManagers.game_initializer import GameInitializer, SessionOptions
from Managers.SessionManagers.move_checker import MoveChecker


class BlackjackBot:

    """
    Funnel for user inputs.
    """

    def __init__(self, options: SessionOptions):
        self.channel_manager = options.channel_manager
        self.bot = options.bot
        self.initializer = BlackjackInitializer(options)
        self.id = GAME_ID["BLACKJACK"]

    async def create_game(self, ctx):
        await self.initializer.initialize_game(ctx)

    async def make_move(self, ctx, action):
        game = self._get_game(ctx)
        if await self._game_is_blackjack(game):
            move_checker = BlackjackMoveChecker(self.bot, game)
            await move_checker.perform_action(ctx, action)

    def _get_game(self, ctx):
        user = ctx.message.author
        channel = ctx.message.channel
        game = self.channel_manager.get_game(channel)
        if game and self._is_in_game(game, user):
            return game

    async def _game_is_blackjack(self, game):
        if game and self.id == game.id:
            return True
        else:
            temp_message = await self.bot.say("You aren't in a Blackjack game. Join the next one?")
            self._auto_delete_message(temp_message)

    @staticmethod
    def _is_in_game(game, user) -> bool:
        return any(in_game_user for in_game_user in game.users if in_game_user is user)

    async def _auto_delete_message(self, message):
        await asyncio.sleep(5.0)
        await self.bot.delete_message(message)


class BlackjackInitializer(GameInitializer):

    """
    Handles blackjack sessions.
    TODO instead of a single time limit, should be on a per-player basis
    """

    def __init__(self, options: SessionOptions):
        super().__init__(options)

    async def initialize_game(self, ctx):
        if await self._can_create_game(ctx):
            blackjack = Blackjack(self.bot, ctx)
            await self._create_session(blackjack)

    async def _create_session(self, blackjack: Blackjack):
        self._add_game(blackjack.ctx, blackjack)
        await self._run_join_timer(blackjack)
        await blackjack.start_game()
        self._remove_game(blackjack.ctx)
        self.data_manager.batch_transfer(blackjack.get_payouts())

    async def _run_join_timer(self, blackjack):
        join_timer = BlackjackJoinTimer(self.bot, blackjack)
        await self.channel_manager.add_join_timer(blackjack.host, join_timer)

    async def _run_time_limit(self, game):
        time_limit = TimeLimit(self.bot, game)
        await time_limit.run()


class BlackjackMoveChecker:

    """
    Checks if your Blackjack move is legal.
    """

    def __init__(self, bot, game):
        self.bot = bot
        self.game = game
        self.move_checker = MoveChecker(bot, game)

    async def perform_action(self, ctx, action_to_perform: str):
        user = ctx.message.author
        can_make_move = await self.move_checker.can_make_move(user)
        if can_make_move:
            action_list = self.get_actions()
            await action_list[action_to_perform]()

    def get_actions(self):
        return {
                "hit": self.game.hit,
                "stand": self.game.stand_current_hand,
                "split": self.game.attempt_split,
                "doubledown": self.game.attempt_double_down
                }