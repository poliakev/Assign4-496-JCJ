"""
Module for playing games of Go using GoTextProtocol

This code is based off of the gtp module in the Deep-Go project
by Isaac Henrion and Aamos Storkey at the University of Edinburgh.
"""
import traceback
import sys
import os
from board_util_go4 import GoBoardUtilGo4
import gtp_connection
import numpy as np
import re
from mcts import MCTS

class GtpConnection2(gtp_connection.GtpConnection):

    def __init__(self, go_engine, board, outfile = 'gtp_log', debug_mode = False):
        """
        object that plays Go using GTP

        Parameters
        ----------
        go_engine : GoPlayer
            a program that is capable of playing go by reading GTP commands
        komi : float
            komi used for the current game
        board: GoBoard
            SIZExSIZE array representing the current board state
        """
        gtp_connection.GtpConnection.__init__(self, go_engine, board, outfile, debug_mode)
        self.commands["prior_knowledge"] = self.prior_knowledge_cmd
    

    def prior_knowledge_cmd(self, args):
        """
        Return list of policy moves for the current_player of the board
        """
        policy_moves, _ = GoBoardUtilGo4.generate_all_policy_moves(self.board,
                                                        self.go_engine.use_pattern,
                                                        self.go_engine.check_selfatari)

        #policy_list.append("Pass")
        self.MCTS = MCTS()
        move_set =self.get_move(self.board,self.MCTS.toplay)
        #lst=self.MCTS.prior_knowledge_stat(self.board, self.MCTS._root, self.MCTS.toplay)
        move_string = ""
        for m_set in move_set:
            for m in m_set:
                move_string += str(m) + " "
        #print(move_string) 
        move_stats = []
        self.respond("gtpStatistics: " + str(move_string))
    def prior_knowledge_stat(self, board, root, color):
        s_color = GoBoardUtilGo4.int_to_color(color)

        stats=[]
        for move,node in root._children.items():
            if color == BLACK:
                wins = node._black_wins
            else:
                wins = node._n_visits - node._black_wins
            visits = node._n_visits
            if visits:
                win_rate = round(float(wins)/visits,2)    
            else:
                win_rate = 0
            if move==PASS:
                move = None
            pointString = board.point_to_string(move)
            stats.append((pointString,wins,visits,win_rate))
        lst= sorted(stats,key=lambda i:i[3],reverse=True)
        for stuff in lst:
            print(stuff)
            # del
        #sys.stderr.write("Sstatistics: {} \n".format(lst))
        sys.stderr.flush()
        return lst
    def get_move(self, board, toplay):

        move = self.MCTS.prior_knowledge_move(board,
                toplay,
                komi=self.go_engine.komi,
                limit=self.go_engine.limit,
                check_selfatari=self.go_engine.check_selfatari,
                use_pattern=self.go_engine.use_pattern,
                num_simulation = self.go_engine.num_simulation,
                exploration = self.go_engine.exploration,
                simulation_policy = self.go_engine.simulation_policy,
                in_tree_knowledge = self.go_engine.in_tree_knowledge)
        return move

