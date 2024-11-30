#!/usr/bin/env python3

import _game, discrete_soccer

game_type = discrete_soccer.DiscreteSoccer()
agents = [discrete_soccer.DummyAgent(), discrete_soccer.PlayerAgent()]

game = _game.Game(game_type, agents)

game.run()
