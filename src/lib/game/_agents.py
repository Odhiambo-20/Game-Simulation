#!/usr/bin/env python3

from ._game import Agent
import random


class RandomAgent(Agent):
    """Choose randomly from available actions."""
    def decide(self, state):
        return random.choice(state.actions)

class GreedyAgent(Agent):
    def __init__(self, evaluate_function):
        super().__init__()
        self.evaluate = evaluate_function

    """Simple agent that chooses the best action based on one level of the evaluation function."""
    def decide(self, state):
        return max([(a, self.evaluate(state.act(a), state.current_player)) for a in state.actions],
                   key=lambda x:x[1])[0]
