from abc import abstractmethod

from Core.core_game_class import GameCore


class SessionOptions:
    def __init__(self, bot, channel_manager):
        self.bot = bot
        self.channel_manager = channel_manager


class GameInitializer:

    """
    For games that have persistence
    """

    def __init__(self, options: SessionOptions):
        self.bot = options.bot
        self.channel_manager = options.channel_manager
        self.games = {}

    async def initialize_game(self, ctx):
        if await self._can_create_game(ctx):
            self._run_session(ctx)

    def get_games(self):
        return self.games

    def _run_session(self, ctx):
        game = self._get_game_to_create(ctx)
        self._add_game(ctx, game)
        self._remove_game(ctx)

    def _add_game(self, ctx, game):
        channel = ctx.message.channel
        self.channel_manager.occupy_channel(channel, game)
        self.games[channel] = game

    def _remove_game(self, ctx):
        channel = ctx.message.channel
        self.channel_manager.vacate_channel(channel)
        self.games.pop(channel)

    async def _can_create_game(self, ctx) -> bool:
        return await self.channel_manager.is_valid_channel(ctx) and \
               await self._is_valid_new_game(ctx)

    async def _is_valid_new_game(self, ctx) -> bool:
        user = ctx.message.author
        for game in self.games:
            if self._is_in_game(game, user):
                await self.bot.say("Please finish your current game first.")
                return False
        return True

    @staticmethod
    def _is_in_game(game, user) -> bool:
        return any(in_game_user for in_game_user in game.users if in_game_user is user)

    @abstractmethod
    def _get_game_to_create(self, ctx) -> GameCore:
        raise NotImplementedError
