#!/usr/bin/python3
import os, sys
utilpath = sys.path[0] + "/../util/"
sys.path.append(utilpath)
utilpath = sys.path[0] + "/../Go4/"
sys.path.append(utilpath)

from gtp_connection import GtpConnection  
from board_util_go4 import GoBoardUtilGo4
from simple_board import SimpleGoBoard
from mcts import MCTS
import numpy as np
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--num_total_sim', type=int, default=300, help='number of simulations per move, so total playouts=sim*legal_moves')
parser.add_argument('--simulations', type=str, default='random', help='type of simulation policy: random or rulebased or probabilistic')
parser.add_argument('--movefilter', action='store_true', default=False, help='whether use move filter or not')
parser.add_argument('--in_tree_knowledge', type=str, default='None', help='whether use move knowledge to initial a new node or not')

args = parser.parse_args()
num_simulation = args.num_total_sim
simulations = args.simulations
move_filter = args.movefilter
in_tree_knowledge = args.in_tree_knowledge

def count_at_depth(node, depth, nodesAtDepth):
    if not node._expanded:
        return
    nodesAtDepth[depth] += 1
    for _,child in node._children.items():
        count_at_depth(child, depth+1, nodesAtDepth)

class Go5Player():
    def __init__(self, num_simulation, limit=100, exploration = 0.4):
        """
        Player that selects a move based on MCTS from the set of legal moves

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """
        self.name = "Go5"
        self.version = 0.22
        self.MCTS = MCTS()
        self.num_simulation = num_simulation
        self.limit = limit
        self.exploration = exploration 
        self.simulation_policy = simulations
        self.use_pattern = True
        self.check_selfatari = move_filter
        self.in_tree_knowledge = in_tree_knowledge
        self.parent = None

    def sample_run(self, board, toplay, print_info=False):
        self.MCTS.exploration = self.exploration
        self.MCTS.limit = self.limit
        self.MCTS.toplay = toplay
        self.MCTS.use_pattern = True
        self.MCTS.check_selfatari = True

        for n in range(self.num_simulation):
            board_copy = board.copy()
            self.MCTS._playout(board_copy, toplay)

        if print_info:
            self.MCTS.good_print(board, self.MCTS._root, toplay,self.num_nodes)

    def reset(self):
        self.MCTS = MCTS()

    def update(self, move):
        self.parent = self.MCTS._root 
        self.MCTS.update_with_move(move)

    def get_move(self, board, toplay):
        move = self.MCTS.get_move(board,
                toplay,
                komi=self.komi,
                limit=self.limit,
                check_selfatari=self.check_selfatari,
                use_pattern=self.use_pattern,
                num_simulation = self.num_simulation,
                exploration = self.exploration,
                simulation_policy = self.simulation_policy,
                in_tree_knowledge = self.in_tree_knowledge)
        self.update(move)
        return move
    
    def get_node_depth(self, root):
        MAX_DEPTH = 100
        nodesAtDepth = [0] * MAX_DEPTH
        count_at_depth(root, 0, nodesAtDepth)
        prev_nodes = 1
        return nodesAtDepth
    
    def get_properties(self):
        return dict(
            version=self.version,
            name=self.__class__.__name__,
        )

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(Go5Player(num_simulation), board)
    con.start_connection()

if __name__=='__main__':
    if simulations != "random" and simulations != "rulebased" and simulations != "probabilistic":
        sys.stderr.write('simulations must be random or rulebased or probabilistic \n')
        sys.stderr.flush()
        sys.exit(0)
    run()

