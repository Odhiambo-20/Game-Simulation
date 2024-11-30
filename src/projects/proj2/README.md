# Project 2: Minimax, Alpha-Beta, Monte Carlo Game Tree Search and Reinforcement Learning

In this project, you will complete an agent and an evaluation function
to play a discretized version of soccer.

## Usage

From the root directory, run

    python3 evaluate.py proj2

This will run a version of the game where both players choose actions
randomly.

The `main.py` file also allows you to play against the agent you
create. To do so, run

    python3 evaluate.py proj2 --interactive

For any help on additional commands such as specifying search depth,
run

    python3 evaluate.py proj2 --help

## Implementation notes

### The agent

You will be extending the abstract [`Agent`](/src/lib/game/_game.py#L10)
class specified in the game code. You will need to extend the `decide`
method so that it returns the correct action given a GameState.

Because we want our `MinimaxAgent` and `MonteCarloAgent`to be used for
many kinds of games, you can only use the most general information about
a game. Each game extends the [`GameState`](/src/lib/game/_game.py#L135)
class; in particular, we are given the following information:

1. `state.num_players` The number of players in the game
2. `state.current_player` The numeric ID of the player whose turn it
   is at the given state
3. `state.actions` The list of actions available at the moment
4. `state.is_terminal` Whether the current game state is terminal (that is, the game has ended)
5. `state.reward(player_id)` The reward that `player_id` receives, assuming that this is at the end of the game.
6. `state.act(action)` The corresponding GameState that would happen if `action` is performed at `state`

Note that the `GameState` class is immutable -- that is, *updates* to
the game happen by creating an entirely new `GameState` object rather
than destructively updating the existing `GameState`. For example, if
you run

    old_state = copy(state)
    state.act(action)
    old_state != state ## This will evaluate to False

since `state.act` is not destructive, `state` is not changed by
`state.act`. The following code will work:

    new_state = state.act(action)
    new_state != state ## This will evaluate to True

The `GameState` class is implemented as a persistent data structure
using [pyrsistent](https://github.com/tobgu/pyrsistent). That is,
updates to immutable data structures (as copies) are faster than
simple copies, but still relatively slower than mutable updates. For
the purpose of this assignment, you should not have to be too
concerned about the performance of immutable updates.

### The evaluation function

While our Minimax and Monte Carlo agents are domain-independent, the
evaluation function should be heavily domain-dependent. That is, you
should use the special methods from
the [`SoccerState`](/src/lib/game/discrete_soccer.py#L91) class when
implementing the evaluation function. In particular, you should pay
attention to:

1. `state.ball` Information about the location and state of the soccer ball
2. `state.players` Information about the location and state of each
   player on the field (indexed by the numeric player ID)

There are many helper functions provided in the `SoccerState` class,
so it is worth reading their documentation.

## Game Description

For constructing the evaluation function, you will need to understand
how the Discrete Soccer game works. We will describe the basic rules
of the game below.

The game runs until a single goal is made. There are no time
restrictions on a single game.

You may notice that some games will end without either player shooting
a goal. Since minimax is a deterministic algorithm, if a state in the
game is repeated, then that implies that the game will loop infinitely
with those players. We reset the game when this scenario happens.

### Initialization

Each player begins at a random position on their side of the
field. The ball starts directly in the center of the field for every
game.

### Movement

Players without the ball can move either up, down, left, right, or
diagonally towards their opponent's goal. When a player cannot move
further left or right at the edge of the field, they are given the
additional option to move diagonally away from that edge. Players
without the ball are not allowed to move out of bounds.

Players with the ball can move out of bounds (OOB), but it results in a
penalty. When a player moves OOB in the y-direction, or when a player
moves OOB near their goal, the game is reset with the opponent having
the ball. If the player leaves OOB near the opponent's goal, the
opponent receives the ball at the corner of the field and the player
is placed between the opponent and their own goal.

If a player with the ball moves into the goal area, then it is a score
for the inverse team's goal. This means that if a player moves into
their own goal, it counts as a score for the opponent's team.

### Kicking

Players with the ball have an additional `KICK` action. A kick action
succeeds when the player is within a certain region of their
opponent's goal (shown in the game as an area with lighter grass) and
when there is no opponent whose midpoint is within the ragion between
the ball and the goal (shown below).

![Intersection Example](/doc/images/discrete_soccer_intersection.png)

In the above example, the opponent would intersect the ball because
their midpoint is in the "intersection region."

If an opponent does intercept the ball, they receive the ball at where
they were standing and the player is placed between the opponent and
their goal.

You can check whether or not it is possible to shoot from a position
using `state.can_shoot_from` or `state.check_kick`.

### Some considerations when constructing the evaluation function

In our experiments, we found that an evaluation function that simply
considers the player's distance from the ball or the ball's distance
to the opponent's goal were not enough to make a good player.

The evaluation function should take into account steps into the
future. For example, if the opponent has the ball, a player that is
behind their opponent should have a lower evaluation than one whose is
in-between their opponent and their goal.
