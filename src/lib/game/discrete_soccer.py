#!/usr/bin/env python3

from ._game import *
import pygame
from pyrsistent import m, v, PMap, PVector, field, pvector_field, pmap_field
from enum import Enum, IntEnum
import math
import random

MAX_KICK_DIST = 5


class Action(Enum):
    KICK=1
    MOVE=2
    CHANGE_STANCE=3
    def move(x, y):
        return (Action.MOVE, x, y)


class Team(IntEnum):
    RED = 1
    BLUE = 2

    @property
    def inverse(self):
        return Team.RED if self == Team.BLUE else Team.BLUE

    @property
    def name(self):
        return "red" if self == Team.RED else "blue"


class InteractiveAgent(Agent):
    def __init__(self, evaluation_function=None):
        self.evaluate = evaluation_function

    def decide(self, state):
        if self.evaluate:
            self.evaluate(state, state.current_player, True)
        while True:
            pygame.event.clear()
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key in [ pygame.K_w ]:
                    return Action.move(0, 1)
                if event.key in [ pygame.K_x ]:
                    return Action.move(0, -1)
                if event.key in [ pygame.K_a ]:
                    return Action.move(-1, 0)
                if event.key in [ pygame.K_d ]:
                    return Action.move(1, 0)
                if event.key in [ pygame.K_q ]:
                    return Action.move(-1, 1)
                if event.key in [ pygame.K_e ]:
                    return Action.move(1, 1)
                if event.key in [ pygame.K_z ]:
                    return Action.move(-1, -1)
                if event.key in [ pygame.K_c ]:
                    return Action.move(1, -1)
                if event.key in [ pygame.K_s ]:
                    return Action.CHANGE_STANCE
                if event.key == pygame.K_SPACE:
                    return Action.KICK


class generator(GameType):
    def __init__(self, field_width=19, field_height=13, goal_height=5, random_pos=True):
        self.field_width = field_width
        self.field_height = field_height
        self.goal_height = goal_height
        self.random_pos = random_pos

    def init(self, agents):
        players = v(*[m(
            type="player",
            index=i,
            agent=agent,
            team=Team.RED if i % 2 == 0 else Team.BLUE,
            x=0, y=0,
            has_ball=False,
            stance=0
        ) for i, agent in enumerate(agents)])
        teams = m(
            red=v(*[p.index for p in players if p.team == Team.RED]),
            blue=v(*[p.index for p in players if p.team == Team.BLUE])
        )
        ball = m(
            type='ball',
            on_field=True,
            x=int(self.field_width/2)+1,
            y=int(self.field_height/2)+1
        )
        pitch = m(
            width=self.field_width,
            height=self.field_height,
            goal_height=self.goal_height
        )
        state = SoccerState(
            current_player_id=0,
            players=players,
            teams=teams,
            ball=ball,
            pitch=pitch,
            winner=None
        )
        state = state._update_reset(random_pos=self.random_pos)
        return state


class SoccerState(GameState):
    ################################################################
    ## PUBLIC METHODS
    ################################################################

    # You may use these methods when implementing the MinimaxAgent
    # and MonteCarloAgent.

    # For information on these methods, see _game.GameState

    @property
    def num_players(self):
        return len(self.players)

    @property
    def current_player(self):
        return self.current_player_id

    @property
    def is_terminal(self):
        return self.winner

    @property
    def actions(self):
        player = self.current_player_obj
        actions = []
        if player.has_ball:
            actions += [Action.KICK]
        # actions += [Action.CHANGE_STANCE]
        dx = 1 if player.team == Team.RED else -1
        actions += [
            Action.move(1, 0), Action.move(-1, 0),
            Action.move(0, 1), Action.move(0, -1)
        ]

        if player.x <= 1:
            dx = 1
        elif player.x >= self.pitch.width:
            dx = -1
        else:
            dx = 1 if player.team == Team.RED else -1

        actions += [
            Action.move(dx, 1), Action.move(dx, -1)
        ]
        return actions

    def reward(self, player_id):
        if not self.is_terminal:
            return None
        return 10 if self.winner == self.players[player_id].team else -10

    def act(self, action):
        player = self.current_player_obj
        state = self

        state = state._action_is_valid(action)
        if not state:
            return None
        if action == Action.KICK:
            state = self._update_kick()
        elif action == Action.CHANGE_STANCE:
            state = state.transform(
                self._cpk('stance'), (player.stance + 1) % 2
            )
        elif isinstance(action, tuple) and action[0] == Action.MOVE:
            (_, dx, dy) = action
            state = self._update_move_to(player.x + dx, player.y + dy)
        else:
            return None

        if state:
            state = state.set(current_player_id=(self.current_player+1) % self.num_players)

        return state

    ################################################################
    ## INTERNAL
    ################################################################

    # These are 'internal' methods and variables to the SoccerState
    # class. You should not use any of these methods in the
    # MinimaxAgent and MonteCarloAgent implementations, but can use
    # them in your soccer evaluation function.

    ## Variables
    # Each of these fields can be directly accessed by calling
    # `state.<variable_name>`.

    # The ID of the current player.
    current_player_id = field(type=int)

    # A persistent list of players. Can be accessed like a normal
    # Python list: players[0] is the first player, etc.
    #
    # Each player object players[i] is a PMap (equivalent to a Python
    # dict) with the following structure:
    #
    # players[i] = {
    #   type="player",  # The type of object
    #   index=i,        # The index of the player in the players list
    #   agent=agent,    # The agent controlling the player
    #   team={Team.RED|Team.BLUE} # The player's team
    #   x=x_pos, y=y_pos, # The current (x,y) position of the player
    #   has_ball={True,False} # True if the player currently has the ball
    # }
    players = pvector_field(PMap)

    # Contains the players of each team. Keys are teams['red'] and
    # teams['blue']. Probably should switch to using the team enum in
    # the future.
    teams = pmap_field(str, PVector)

    # Information about the ball. Has the following information:
    #
    # ball = {
    #   type='ball',          # The type of object
    #   on_field={True,False} # True if nobody has the ball.
    #   x=x_pos, y=y_pos      # The (x,y) position of the ball
    # }
    #
    # Note that the position of the ball is updated even when a player
    # has the ball.
    ball = pmap_field(str, (bool, str, int))

    # The term 'field' was ambiguous, so this is just some
    # information about the soccer field:
    #
    # pitch = {
    #   width=pitch_width       # The width of the soccer field
    #   height=pitch_height     # The height of the soccer field
    #   goal_height=goal_height # The height of the goal (along the y-axis)
    # }
    pitch = pmap_field(str, int)

    # Indicates the winner of the round. When the game hasn't
    # finished, is None; when the game is complete, is the Team that
    # won the game.
    winner = field(type=(Team, type(None)))

    @property
    def objects(self):
        """Returns the list of 'objects' (players + the ball)"""
        return list(self.players) + [self.ball]

    def dist_to_goal(self, pos, team):
        """Returns the distance between an (x, y) position and a team's goal."""
        goal_pos = (self.pitch.width+0.5, self.pitch.height/2) if team == Team.RED \
                   else (0.5, self.pitch.height/2)
        return math.sqrt(sum([(p1+0.51-p2)**2 for p1, p2 in zip(pos, goal_pos)]))

    def at(self, x, y):
        """Returns the object at position (x,y). If no object is there, return
        None.

        """
        for obj in self.objects:
            ## invariant: no two objects occupy the same space
            if obj.x == x and obj.y == y:
                return obj
        return None

    @property
    def current_player_obj(self):
        """Returns the info for the current player in a PMap object."""
        return self.players[self.current_player]

    @property
    def player_with_ball(self):
        return next((p for p in self.players if p.has_ball), [None])

    def goal_pos(self, team):
        """Returns the position of the `teams`'s goal."""
        return self.red_goal_pos if team == Team.RED \
            else self.blue_goal_pos

    @property
    def red_goal_pos(self):
        """The position of the red team's goal."""
        return (self.pitch.width+1, int(self.pitch.height/2)+1)

    @property
    def blue_goal_pos(self):
        """The position of the blue team's goal."""
        return (0, int(self.pitch.height/2)+1)

    @property
    def goal_top(self):
        """Returns the y-position of the top of the goal."""
        return int(self.pitch.height + self.pitch.goal_height) / 2

    @property
    def goal_bottom(self):
        """Returns the y-position of the bottom of the goal."""
        return int(self.pitch.height - self.pitch.goal_height) / 2 + 1

    @property
    def ball_in_red_goal(self):
        """Returns true if the ball is currently in the Red goal."""
        return self.ball.x > self.pitch.width and\
            self.goal_bottom <= self.ball.y and self.ball.y <= self.goal_top

    @property
    def ball_in_blue_goal(self):
        """Returns true if the ball is currently in the Blue goal."""
        return self.ball.x < 1 and\
            self.goal_bottom <= self.ball.y and self.ball.y <= self.goal_top

    def player_in_red_penalty_area(self, player_id):
        """Returns true if the player_id is in the Red penalty area."""
        player = self.players[player_id]
        return player.x >= self.pitch.width-3 and\
            self.goal_bottom-1 <= player.y and player.y <= self.goal_top+1

    def player_in_blue_penalty_area(self, player_id):
        """Returns true if the player_id is in the Blue penalty area."""
        player = self.players[player_id]
        return player.x <= 3 and\
            self.goal_bottom-1 <= player.y and player.y <= self.goal_top+1

    def _cpk(self, *keys):
        """Internal method, returns a tuple for the current player that is
        used for updating the state.

        """
        return ('players', self.current_player, *keys)

    def _update_move_to(self, x, y):
        """State update: Current player moves to pos (x,y)."""
        player = self.current_player_obj
        state = self
        if player.has_ball:
            if y < 1 or y > state.pitch.height: ## sidelines
                state = state._update_reset(prefer_side=player.team.inverse)
            elif x < 1 or x > self.pitch.width:
                if self.goal_bottom <= y and y <= self.goal_top:
                    if x < 1:
                        state = state.set(winner=Team.BLUE)
                    else:
                        state = state.set(winner=Team.RED)
                else:
                    if x < 1 and player.team == Team.RED \
                       or x > self.pitch.width and player.team == Team.BLUE:
                        state = state._update_corner_kick()
                    else:
                        state = state._update_reset(prefer_side=player.team.inverse)
            else:
                ## deal with collision
                (state, do_move) = state._update_check_collide(x, y)
                if do_move:
                    state = state.transform(self._cpk('x'), x, self._cpk('y'), y,
                                            ('ball', 'x'), x, ('ball', 'y'), y)
                    state = state._update_check_goal()
        else:
            if x < 1 or x > self.pitch.width:
                return None
            elif y < 1 or y > self.pitch.height:
                return None
            else:
                ## deal with collision
                (state, do_move) = state._update_check_collide(x, y)
                if do_move:
                    state = state.transform(self._cpk('x'), x, self._cpk('y'), y)
        return state

    def _update_corner_kick(self):
        state = self
        p2 = self.player_with_ball

        if not p2:
            return state

        goal_pos = self.goal_pos(p2.team.inverse)
        p1 = self.players[self.teams[p2.team.inverse.name][0]]
        goal_pos_x = goal_pos[0]
        dx = -1 if goal_pos_x > 1 else 1

        state = state.transform(
            ('players', p1.index, 'x'), goal_pos_x + dx,
            ('players', p1.index, 'y'), 1,
            ('players', p1.index, 'has_ball'), True,
            ('players', p2.index, 'x'), goal_pos_x + 3*dx,
            ('players', p2.index, 'y'), 3,
            ('players', p2.index, 'has_ball'), False
        )

        return state

    def is_goal(self, dist, angle):
        return 20*abs(angle)**2/(dist**2) > 3e-1

    def can_shoot_from(self, x, y, team):
        (x, y) = (x + 0.5, y - 0.5)
        goal_x = self.pitch.width + 2 if team == Team.RED else 0
        goal_y1 = int(self.pitch.height - self.pitch.goal_height) / 2
        goal_y2 = int(self.pitch.height + self.pitch.goal_height) / 2
        dx = goal_x - x
        dy1 = (goal_y1 - y)
        dy2 = (goal_y2 - y)
        norm1 = math.sqrt(dx**2 + dy1**2)
        norm2 = math.sqrt(dx**2 + dy2**2)
        dy = ((goal_y1+goal_y2)/2 - y)

        dist = math.sqrt(dx**2 + dy**2)
        angle = math.acos((dx**2 + dy1*dy2)/(norm1*norm2))

        return self.is_goal(dist, angle)

    def check_kick(self, player):
        (x, y) = (player.x + 0.5, player.y - 0.5)
        goal_x = self.pitch.width + 2 if player.team == Team.RED else 0
        goal_y1 = int(self.pitch.height - self.pitch.goal_height) / 2
        goal_y2 = int(self.pitch.height + self.pitch.goal_height) / 2
        dx = goal_x - x
        dy1 = goal_y1 - y
        dy2 = goal_y2 - y
        norm1 = math.sqrt(dx**2 + dy1**2)
        norm2 = math.sqrt(dx**2 + dy2**2)
        dy = (goal_y1+goal_y2)/2 - y

        dist = math.sqrt(dx**2 + dy**2)
        angle = math.acos((dx**2 + dy1*dy2)/(norm1*norm2))

        (x, y) = (player.x + 0.5, player.y + 0.5)
        goal_x = self.pitch.width + 1 if player.team == Team.RED else 1
        goal_y1 = int(self.pitch.height - self.pitch.goal_height)/2 + 1
        goal_y2 = int(self.pitch.height + self.pitch.goal_height)/2 + 1
        dx = goal_x - x
        dy1 = goal_y1 - y
        dy2 = goal_y2 - y

        f_y1 = lambda obj_x: dy1/dx*(obj_x - x) + y
        f_y2 = lambda obj_x: dy2/dx*(obj_x - x) + y

        # Check for interceptions
        intercept = (None, float("inf"))
        for obj in self.players:
            if obj.index == player.index: continue
            (obj_x, obj_y) = (obj.x + 0.5, obj.y + 0.5)
            if obj_y >= f_y1(obj_x) and obj_y <= f_y2(obj_x) or \
            obj_y+0.25 >= f_y1(obj_x+0.25) and obj_y+0.25 <= f_y2(obj_x+0.25) or \
            obj_y-0.25 >= f_y1(obj_x+0.25) and obj_y-0.25 <= f_y2(obj_x+0.25) or \
            obj_y+0.25 >= f_y1(obj_x-0.25) and obj_y+0.25 <= f_y2(obj_x-0.25) or \
            obj_y-0.25 >= f_y1(obj_x-0.25) and obj_y-0.25 <= f_y2(obj_x-0.25):
                new_i = (obj, math.sqrt((x - obj_x)**2 + (y - obj_y)**2))
                intercept = min([intercept, new_i], key=lambda x: x[1])

        return (dist, angle, self.is_goal(dist, angle), intercept[0])

    def _update_kick(self):
        """State update: Current player kicks towards opponent goal."""
        player = self.current_player_obj
        state = self

        (_, _, is_goal, intercept_player) = self.check_kick(player)

        if intercept_player:
            state = state._update_switch_possession(player.index, intercept_player.index)
        elif is_goal:
            goal_pos = self.goal_pos(player.team)
            state = state.transform(
                ('ball', 'x'), goal_pos[0],
                ('ball', 'y'), goal_pos[1],
                ('ball', 'on_field'), True,
                self._cpk('has_ball'), False
            )
            state = state._update_check_goal()
        else:
            state = state._update_reset(prefer_side=player.team.inverse)
        return state

    def _update_switch_possession(self, player_a, player_b):
        """State update: Possession of ball switches between player_a and
        player_b

        """
        state = self
        if self.players[player_a].has_ball:
            p1 = self.players[player_a]
            p2 = self.players[player_b]
        else:
            p1 = self.players[player_b]
            p2 = self.players[player_a]
        goal_pos = self.goal_pos(p1.team.inverse)
        state = state.transform(
            ('players', p1.index, 'has_ball'), False,
            ('players', p2.index, 'has_ball'), True,
            ('ball', 'x'), p2.x,
            ('ball', 'y'), p2.y
        )
        state = state._update_place_between(p1.index, p2.x, p2.y, goal_pos[0], goal_pos[1])
        return state

    def _update_place_between(self, player_id, x1, y1, x2, y2):
        """State update: player_id is placed in between position (x1, y1) and
        (x2, y2)

        """
        x = int((x1+x2)/2)
        y = int((y1+y2)/2)
        state = self
        if state.at(x, y):
            if not state.at(x+1, y) and x+1 <= self.pitch.width:
                x += 1
            elif not state.at(x-1, y) and x-1 >= 1:
                x -= 1
            elif not state.at(x, y+1) and y+1 <= self.pitch.height:
                y += 1
            elif not state.at(x, y-1) and y-1 >= 1:
                y -= 1
        state = state.transform(
            ('players', player_id, 'x'), x,
            ('players', player_id, 'y'), y
        )
        return state

    def _update_reset(self, prefer_side=None, random_pos=False):
        """State update: Players and ball are reset to original position.

        :param Team prefer_side: If set to a Team, that team will
            receive the ball when the game is reset.
        :param bool random_pos: If True, players will be randomly
            placed on their side of the field.
        """
        state = self
        mid_x = int(self.pitch.width / 2) + 1
        mid_y = int(self.pitch.height / 2) + 1
        ball_offset = 0 if not prefer_side \
                      else (-1 if prefer_side == 'red' else 1)
        if not prefer_side:
            state = state.transform(
                ('ball', 'x'), mid_x + ball_offset,
                ('ball', 'y'), mid_y,
                ('ball', 'on_field'), True
            )
        else:
            state = state.transform(('ball', 'on_field'), False)
        for team_name in ('red', 'blue'):
            team = self.teams[team_name]
            i = 0
            for dx in range(4):
                done = False
                for dy in range(5):
                    if not random_pos:
                        x = mid_x + (-dx-5 if team_name == 'red' else dx+5)
                        y = mid_y + (2 * int(dy / 2) * (-1 if dy % 2 else 1))
                        state = state\
                                .transform(('players', team[i], 'x'), x)\
                                .transform(('players', team[i], 'y'), y)\
                                .transform(('players', team[i], 'has_ball'), False)
                        if i == 0 and prefer_side == self.players[team[i]].team:
                            state = state.transform(
                                ('players', team[i], 'has_ball'), True,
                                ('ball', 'x'), x, ('ball', 'y'), y
                            )
                        i += 1
                    else:
                        x_range = range(1,mid_x) if team_name == 'red' \
                                  else range(mid_x+1,self.pitch.width)
                        y_range = range(1,self.pitch.height)
                        state = state\
                                .transform(('players', team[i], 'x'), random.choice(x_range))\
                                .transform(('players', team[i], 'y'), random.choice(y_range))
                    if i >= len(team):
                        done = True
                        break
                if done:
                    break
        return state

    def _update_check_collide(self, x, y):
        """State update: Check if there will be a collision between the
        current player and whatever is at position (x,y).

        """
        state = self
        do_move = True
        obj = state.at(x, y)
        if not obj:
            do_move = True
        elif obj.type == 'ball': ## If we collide with the ball...
            ## Pick up the ball
            state = state.transform(
                ('ball', 'x'), x, ('ball', 'y'), y, ('ball', 'on_field'), False,
                self._cpk('has_ball'), True
            )
            do_move = True
        elif obj.type == 'player':
            # state = state.transform(
            #     ('ball', 'x'), x, ('ball', 'y'), y,
            #     self._cpk('has_ball'), False,
            #     ('players', obj.index, 'has_ball'), True
            # )
            if self.current_player_obj.has_ball or obj.has_ball:
                state = state._update_switch_possession(self.current_player, obj.index)
            do_move = False
        else:
            state = None
            do_move = False
        return (state, do_move)

    def _update_check_goal(self):
        """State update: Check if the ball is in a goal, and, if so, update
        the winner of the game.

        """
        state = self
        if self.ball_in_red_goal:
            state = state.set(winner=Team.RED)
        elif self.ball_in_blue_goal:
            state = state.set(winner=Team.BLUE)
        return state

    def draw(self):
        """Internal method, draws the current game configuration."""
        BLOCK_SIZE = B = 32
        PITCH_COLOR = (0, 200, 0)
        PLAYER_RED_COLOR = (255, 0, 0)
        PLAYER_BLUE_COLOR = (0, 0, 255)
        BALL_COLOR = (255, 255, 255)
        surf = pygame.Surface(((self.pitch.width+2)*B, (self.pitch.height+2)*B))

        (W, H) = (surf.get_width(), surf.get_height())
        (W_p, H_p) = (self.pitch.width, self.pitch.height)
        H_g = self.pitch.goal_height
        surf.fill(PITCH_COLOR)

        # Draw grid
        for i in range(self.pitch.width+2):
            for j in range(self.pitch.height+2):
                s1 = surf.subsurface((i * B, (self.pitch.height-j+1) * B, B, B))
                if 1 <= i and i <= self.pitch.width and\
                   1 <= j and j <= self.pitch.height:
                    if self.can_shoot_from(i, j, Team.RED) or self.can_shoot_from(i, j, Team.BLUE):
                        s1.fill((100, 255, 100), (1, 1, B-2, B-2))
                    else:
                        s1.fill((0, 255, 0), (1, 1, B-2, B-2))

        # Draw field lines
        pygame.draw.lines(surf, (255, 255, 255), True,
                          [(B, B), (W-B,B), (W-B,H-B), (B, H-B)], 3)
        pygame.draw.line(surf, (255, 255, 255), (int(W/2), B), (int(W/2), H-B), 3)
        pygame.draw.line(surf, (255, 255, 255), (int(W/2), B), (int(W/2), H-B), 3)
        pygame.draw.line(surf, (255, 255, 255), (int(W/2), B), (int(W/2), H-B), 3)
        pygame.draw.circle(surf, (255, 255, 255), (int(W/2), int(H/2)), int(B*2.5), 3)
        pygame.draw.lines(surf, (255, 255, 255), False,
                          [(B, B*(int((H_p+H_g)/2)+2)),
                           (4*B, B*(int((H_p+H_g)/2)+2)),
                           (4*B, B*(int((H_p-H_g)/2))),
                           (B, B*(int((H_p-H_g)/2)))], 3)
        pygame.draw.lines(surf, (255, 255, 255), False,
                          [(W-B, B*(int((H_p+H_g)/2)+2)),
                           (W-4*B, B*(int((H_p+H_g)/2)+2)),
                           (W-4*B, B*(int((H_p-H_g)/2))),
                           (W-B, B*(int((H_p-H_g)/2)))], 3)
        # pygame.draw.circle(surf, (255, 255, 255), (W-B, int(H/2)), B*3, 3)
        # surf.fill(PITCH_COLOR, (0, 0, B-1, H))
        # surf.fill(PITCH_COLOR, (W-B+2, 0, B, H))
        font = pygame.font.SysFont("monospace", 18)
        font.set_bold(True)

        for i in range(self.pitch.width+2):
            for j in range(self.pitch.height+2):
                obj = self.at(i, j)
                s1 = surf.subsurface((i * B, (self.pitch.height-j+1) * B, B, B))
                if obj and obj.type == 'ball' and obj.on_field:
                    s1.fill(BALL_COLOR, (6, 6, B-12, B-12))
                elif obj and obj.type == 'player':
                    c = PLAYER_RED_COLOR if obj.team == Team.RED else PLAYER_BLUE_COLOR
                    if obj.index == self.current_player:
                        s1.fill((250, 250, 0))
                    s1.fill(c, (2, 2, B-4, B-4))
                    if obj.has_ball:
                        pygame.draw.rect(s1, BALL_COLOR, (6, 6, B-12, B-12))
                    # label = font.render("R" if obj.stance == 0 else "B", 1, (0, 255, 0))
                    # s1.blit(label, (B/4, B/4))

                if (i < 1 or i > self.pitch.width) and \
                     (self.goal_bottom <= j and j <= self.goal_top):
                    for l in range(4, BLOCK_SIZE, 8):
                        pygame.draw.line(s1, (255, 255, 255), (0, l), (B, l))
                        pygame.draw.line(s1, (255, 255, 255), (l, 0), (l, B))

        GOAL_TOP = BLOCK_SIZE * (1 + int((self.pitch.height + self.pitch.goal_height) / 2))
        GOAL_BOTTOM = BLOCK_SIZE * (1 + int((self.pitch.height - self.pitch.goal_height) / 2))
        pygame.draw.lines(surf, (0, 0, 0), False,
                          [(0, GOAL_TOP), (B, GOAL_TOP), (B, GOAL_BOTTOM), (0, GOAL_BOTTOM)], 3)
        pygame.draw.lines(surf, (0, 0, 0), False,
                          [(W, GOAL_TOP), (W-B, GOAL_TOP), (W-B, GOAL_BOTTOM), (W, GOAL_BOTTOM)], 3)
        pygame.draw.rect(surf, PLAYER_RED_COLOR, (0, 0, 6, surf.get_height()))
        pygame.draw.rect(surf, PLAYER_BLUE_COLOR, (surf.get_width()-7, 0, 6, surf.get_height()))

        if self.is_terminal:
            winner_rect = ((1+self.pitch.width/2-3)*B, (self.pitch.height/2+2)*B,
                           6*B, 2*B)
            border_rect = (winner_rect[0]-4, winner_rect[1]-4, winner_rect[2]+8, winner_rect[3]+8)
            label = None
            if self.winner == Team.RED:
                label = font.render("Team  RED wins!", 1, (255, 255, 255))
                pygame.draw.rect(surf, (200, 100, 100), border_rect)
                pygame.draw.rect(surf, (255, 0, 0), winner_rect)
            else:
                label = font.render("Team BLUE wins!", 1, (255, 255, 255))
                pygame.draw.rect(surf, (100, 100, 200), border_rect)
                pygame.draw.rect(surf, (0, 0, 255), winner_rect)
            surf.blit(label, (winner_rect[0]+7, winner_rect[1]+int(B/2)+4))

        return surf

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        key = [self.current_player, (self.ball.x, self.ball.y)] \
              + [(p.x, p.y, p.stance, p.has_ball) for p in self.players]
        return hash(tuple(key))
