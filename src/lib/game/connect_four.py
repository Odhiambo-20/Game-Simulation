#!/usr/bin/env python3

from ._game import *
import pygame
from pyrsistent import m, v, PMap, PVector, field, pvector_field, pmap_field
from enum import Enum, IntEnum
import math
import random

class InteractiveAgent(Agent):
    def decide(self, state):
        if state.width > 10:
            raise ValueError("InteractivePlayer can only play games on Connect 4 boards of width <= 10.")
        actions = state.actions
        keymap = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
            pygame.K_6: 5,
            pygame.K_7: 6,
            pygame.K_8: 7,
            pygame.K_9: 8,
            pygame.K_0: 9
        }
        while True:
            pygame.event.clear()
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN and event.key in keymap:
                action = keymap[event.key]
                if action in actions:
                    return action


class generator(GameType):
    def __init__(self, width=7, height=6, connect_length=4):
        self.width = width
        self.height = height
        self.connect_length = connect_length

    def init(self, agents):
        if len(agents) != 2:
            return ValueError("Connect 4 only accepts games with 2 agents.")
        board = v(*[v() for _ in range(self.width)])
        state = Connect4State(
            current_player_id=0,
            width=self.width,
            height=self.height,
            connect_length=self.connect_length,
            board=board,
            winner=None
        )
        return state


class Connect4State(GameState):
    current_player_id = field(int)
    width = field(int)
    height = field(int)
    connect_length = field(int)
    board = pvector_field(PVector)
    winner = field((int, type(None)))

    @property
    def num_players(self):
        return 2

    @property
    def current_player(self):
        return self.current_player_id

    @property
    def is_terminal(self):
        return self.winner != None

    @property
    def actions(self):
        actions = [x for x in list(range(self.width))
                   if not self.column_filled(x)]
        return actions

    def reward(self, player_id):
        if self.winner == None:
            return None
        ## Draw
        if self.winner < 0:
            return 0
        return 10 if player_id == self.winner else -10

    def act(self, action):
        self._action_is_valid(action)

        state = self
        state = state._update_place_chip(action)
        if state:
            state = state.set(current_player_id=(self.current_player + 1) % 2)

        return state

    def draw(self):
        surf = pygame.Surface((672, 480))
        padding_x = 30
        padding_y = 20
        block_size_x = (surf.get_width() - padding_x * (self.width+1)) / self.width
        block_size_y = (surf.get_height() - padding_y * (self.height+1) - 30) / self.height

        BOARD_COLOR = (200, 200, 0)
        EMPTY_COLOR = (255, 255, 255)
        P1_COLOR = (255, 0, 0)
        P2_COLOR = (0, 0, 0)

        surf.fill(BOARD_COLOR)

        font = pygame.font.SysFont("monospace", 24)
        font.set_bold(True)
        for i in range(self.width):
            x = (block_size_x + padding_x) * i + padding_x
            label = font.render(str((i+1) % 10), 1, (0, 0, 0))
            surf.blit(label, (x+int(block_size_x/4)+5, 7))
            for j in range(self.height):
                y = (block_size_y + padding_y) * (self.height - j - 1) + padding_y + 30
                chip = self.at(i, j)
                color = EMPTY_COLOR
                if chip == 0:
                    color = P1_COLOR
                elif chip == 1:
                    color = P2_COLOR
                pygame.draw.ellipse(surf, color, (x, y, block_size_x, block_size_y))

        if self.winner != None:
            winner_rect = (int(surf.get_width()/2)-100, int(surf.get_height()/2)+50,
                           200, 50)
            border_rect = (winner_rect[0]-4, winner_rect[1]-4, winner_rect[2]+8, winner_rect[3]+8)
            label = None
            if self.winner == 0:
                label = font.render(" RED  wins!", 1, (255, 255, 255))
                pygame.draw.rect(surf, (200, 100, 100), border_rect)
                pygame.draw.rect(surf, (255, 0, 0), winner_rect)
            elif self.winner == 1:
                label = font.render("BLACK wins!", 1, (255, 255, 255))
                pygame.draw.rect(surf, (50, 50, 50), border_rect)
                pygame.draw.rect(surf, (0, 0, 0), winner_rect)
            else:
                label = font.render("  DRAW     ", 1, (255, 255, 255))
                pygame.draw.rect(surf, (150, 150, 150), border_rect)
                pygame.draw.rect(surf, (100, 100, 100), winner_rect)
            surf.blit(label, (winner_rect[0]+8, winner_rect[1]+10))

        return surf

    def at(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= len(self.board[x]):
            return None
        else:
            return self.board[x][y]

    def column_filled(self, x):
        return len(self.board[x]) == self.height

    def get_range(self, x1, y1, x2, y2):
        if x1 == x2 and y1 != y2:
            return [self.at(x1, y) for y in range(y1, y2+1)]
        elif y1 == y2 and x1 != x2:
            return [self.at(x, y1) for x in range(x1, x2+1)]
        elif abs(x1-x2) == abs(y1-y2):
            dx = 1 if x1 < x2 else -1
            dy = 1 if y1 < y2 else -1
            x = x1; y = y1
            items = [self.at(x, y)]
            while x != x2: # and y != y2
                x += dx; y += dy
                items += [self.at(x,y)]
            return items
        else:
            raise ValueError("get_range can only return horizontal, vertical and diagonal ranges.")

    def chain_length(self, check, x1, y1, x2, y2):
        lst = self.get_range(x1, y1, x2, y2)
        max_length = 0
        current_length = 0
        in_chain = True
        for c in lst:
            if c == check:
                current_length += 1
                max_length = max(current_length, max_length)
            else:
                current_length = 0
        return max_length

    def _update_place_chip(self, x):
        state = self
        state = state.transform(('board', x), self.board[x] + [self.current_player])
        state = state._update_check_win(x)
        state = state._update_check_draw()
        return state

    def _update_check_win(self, x):
        state = self
        y = len(state.board[x])-1
        player = state.board[x][y]
        if self.chain_length(player, x, y-3, x, y) >= self.connect_length \
           or self.chain_length(player, x-3, y, x+3, y) >= self.connect_length \
           or self.chain_length(player, x-3, y-3, x+3, y+3) >= self.connect_length \
           or self.chain_length(player, x+3, y-3, x-3, y+3) >= self.connect_length:
            state = state.set(winner=player)
        return state

    def _update_check_draw(self):
        state = self
        if self.winner == None \
             and all([state.column_filled(x) for x in range(self.width)]):
            state = state.set(winner=-1)
        return state
