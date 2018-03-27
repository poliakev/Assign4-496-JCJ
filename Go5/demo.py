#!/usr/bin/python3
import os, sys
utilpath = sys.path[0] + "/../util/"
sys.path.append(utilpath)
utilpath = sys.path[0] + "/../Go4/"
sys.path.append(utilpath)
from simple_board import SimpleGoBoard 
import numpy as np
from Go5 import Go5Player
import time 
from board_util_go4 import  BLACK, WHITE


board=SimpleGoBoard(4)
player=Go5Player(num_simulation = 200, limit=100, exploration = np.sqrt(2))
player.MCTS.komi = 6.5
player.num_nodes = 5
player.MCTS.simulation_policy = 'random'
cboard = board.copy()
print("\nrunning playout 200 times\n")
player.sample_run( cboard, BLACK,print_info=True)


time.sleep(30) # sleeping
player.num_simulation = 300
print("\nrunning it 300 more times\n")
cboard = board.copy()
player.sample_run( cboard, BLACK,print_info=True)


time.sleep(30)
print("\nrunning it 300 more times\n")
cboard = board.copy()
player.sample_run( cboard, BLACK, print_info=True)


time.sleep(30)
print("\nrunning it 300 more times\n")
cboard = board.copy()
player.sample_run( cboard, BLACK, print_info=True)
