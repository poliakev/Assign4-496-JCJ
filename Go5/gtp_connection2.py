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

        policy_moves.append("PASS")

        moves, prob = generate_moves_with_feature_based_probs(self.board)
        max_prob = prob[max(prob, key=prob.get)]
        sim = {}
        winrate = {}
        wins = {}
        for move in policy_moves:
        # number of simulation per move
            sim[move] = 10*prob[move]/max_prob

            # winrate with linear scaling forumla
            winrate[move] = (0.5/max_prob)*prob[move] + 0.5

            wins[move] = int(round(winrate[move]*sim[move]))

        #TODO: Put this in winrate AND alphanumeric order 
        stats = ""
        for move in sorted(winrate, key=winrate.get, reverse=True):
            if move != "PASS":
                pointString = self.board.point_to_string(move)
            else:
                pointString = "Pass"
            stats = stats + pointString + " " + str(wins[move]) + " " + str(int(round(sim[move]))) + " "

        stats = stats[:-1]

        self.respond(stats)

def generate_moves_with_feature_based_probs(board):
        from feature import Features_weight
        from feature import Feature
        assert len(Features_weight) != 0
        moves = []
        color = board.current_player
        gamma_sum = 0.0
        empty_points = board.get_empty_points()
        empty_points.append("PASS")
        probs = {}
        all_board_features = Feature.find_all_features(board)
        for move in empty_points:
            if move == "PASS":
                moves.append(move)
                probs[move] = Feature.compute_move_gamma(Features_weight, all_board_features[move])
                gamma_sum += probs[move]
            elif board.check_legal(move, color) and not board.is_eye(move, color):
                moves.append(move)
                probs[move] = Feature.compute_move_gamma(Features_weight, all_board_features[move])
                gamma_sum += probs[move]

        '''
        probs[-1] = Feature.compute_move_gamma(Features_weight,all_board_features["PASS"])
        gamma_sum += probs[-1]
        moves.append("PASS")
        '''
        if len(moves) != 0:
            assert gamma_sum != 0.0
            for m in moves:
                probs[m] = probs[m] / gamma_sum
        return moves, probs
