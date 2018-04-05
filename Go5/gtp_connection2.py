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
        move_stats = []
        self.respond("Statistics: " + str(move_stats))

