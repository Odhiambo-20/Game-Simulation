#!/usr/bin/env python3

import math
from ...lib.game import discrete_soccer, connect_four

def soccer(state, player_id):
    """
    Evaluates the given discrete_soccer game state from the perspective
    of `player_id`. The evaluation function assigns a score based on factors
    such as proximity to the opponent's goal, possession, and the location of
    the ball.
    
    :param state: The current game state of discrete_soccer
    :param player_id: The ID of the player for whom we are evaluating the state
    :return: A score indicating the favorability of the state for the player
    """
    
    if not isinstance(state, discrete_soccer.SoccerState):
        raise ValueError("Evaluation function incompatible with game type.")

    # Heuristic parameters
    goal_reward = 1000
    possession_bonus = 50
    distance_penalty = 5

    # Get goal positions and ball position
    player_goal = state.get_goal_position(player_id)
    opponent_goal = state.get_goal_position(1 - player_id)
    ball_position = state.get_ball_position()
    
    # Check if the player has the ball
    has_possession = (state.get_possession() == player_id)

    # Calculate distance to opponent’s goal
    distance_to_goal = math.sqrt((ball_position[0] - opponent_goal[0])**2 +
                                 (ball_position[1] - opponent_goal[1])**2)

    # Start with a base score for having possession of the ball
    score = possession_bonus if has_possession else -possession_bonus

    # Add/subtract based on proximity to the opponent's goal
    score += goal_reward - distance_penalty * distance_to_goal

    return score


def connect_four(state, player_id):
    """
    Evaluates the given connect_four game state from the perspective
    of `player_id`. The evaluation function rewards alignments of pieces,
    with increasing scores for 2, 3, or 4 in a row.
    
    :param state: The current game state of connect_four
    :param player_id: The ID of the player for whom we are evaluating the state
    :return: A score indicating the favorability of the state for the player
    """

    if not isinstance(state, connect_four.Connect4State):
        raise ValueError("Evaluation function incompatible with game type.")

    def score_alignment(count, opponent_count):
        """
        Returns a score based on the number of aligned pieces for the player
        and opponent blocking status.
        
        :param count: Number of consecutive pieces for player_id
        :param opponent_count: Number of opponent pieces in the same line
        :return: A score based on alignment
        """
        if count == 4:
            return 1000  # Win condition
        elif count == 3 and opponent_count == 0:
            return 50  # Three in a row with no block
        elif count == 2 and opponent_count == 0:
            return 10  # Two in a row with no block
        elif count == 3 and opponent_count == 1:
            return 5  # Three in a row, partially blocked
        elif count == 2 and opponent_count == 1:
            return 1  # Two in a row, partially blocked
        return 0

    score = 0
    opponent_id = 1 - player_id
    
    # Check all lines (rows, columns, diagonals)
    for line in state.get_lines():  # Assume get_lines() returns all possible lines (4-length sequences)
        player_count = sum(1 for cell in line if cell == player_id)
        opponent_count = sum(1 for cell in line if cell == opponent_id)
        
        # Only score lines with either player's pieces (mixed lines are less relevant)
        if player_count > 0 and opponent_count == 0:
            score += score_alignment(player_count, opponent_count)
        elif opponent_count > 0 and player_count == 0:
            score -= score_alignment(opponent_count, player_count)

    return score
