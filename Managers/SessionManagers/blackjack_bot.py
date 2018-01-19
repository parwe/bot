from Blackjack.move_checker import BlackjackMoveChecker
from Blackjack.blackjack_executor import BlackjackExecutor
from Blackjack.join_timer import BlackjackJoinTimer
from Core.core_game_class import GameCore
from Core.time_limit import TimeLimit
from Core.constants import GAME_ID
from Managers.SessionManagers.game_initializer import GameInitializer, SessionOptions


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
        self.initializer.initialize_game(ctx)

    async def make_move(self, ctx, action):
        game = self._get_game(ctx)
        if self._game_is_blackjack(game):
            move_checker = BlackjackMoveChecker(self.bot, game)
            await move_checker.perform_action(ctx, action)
        else:
            await self.bot.say("You aren't in a Blackjack game. Join the next one?")

    def _get_game(self, ctx):
        user = ctx.message.author
        channel = ctx.message.channel
        game = self.channel_manager.get_game(channel)
        if channel and self._is_in_game(game, user):
            return game
        return False

    def _game_is_blackjack(self, game: GameCore):
        if game:
            return self.id == game.id

    @staticmethod
    def _is_in_game(game, user) -> bool:
        return any(in_game_user for in_game_user in game.users if in_game_user is user)


class BlackjackInitializer(GameInitializer):

    """
    Handles blackjack sessions.
    TODO instead of a single time limit, should be on a per-player basis
    """

    def __init__(self, options: SessionOptions):
        super().__init__(options)

    async def initialize_game(self, ctx):
        if self._can_create_game(ctx):
            blackjack = BlackjackExecutor(self.bot, ctx)
            await self._create_session(blackjack)

    async def _create_session(self, ctx):
        blackjack = self._get_game_to_create(ctx)
        self._add_game(ctx, blackjack)
        await self._run_join_timer(blackjack)
        await self._run_time_limit(blackjack)
        self._remove_game(ctx)

    async def _run_join_timer(self, blackjack):
        join_timer = BlackjackJoinTimer(self.bot, blackjack)
        self.channel_manager.add_join_timer(blackjack.host, join_timer)
        await join_timer.run()
        self.channel_manager.remove_join_timer(blackjack.host)

    async def _run_time_limit(self, game):
        time_limit = TimeLimit(self.bot, game)
        await time_limit.run()

    def _get_game_to_create(self, ctx) -> GameCore:
        return BlackjackExecutor(self.bot, ctx)