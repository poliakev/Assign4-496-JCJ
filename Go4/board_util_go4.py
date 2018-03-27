"""
Module for playing games of Go using GoTextProtocol

This code is based off of the gtp module in the Deep-Go project
by Isaac Henrion and Aamos Storkey at the University of Edinburgh.
"""
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, FLOODFILL
import numpy as np

class GoBoardUtilGo4(GoBoardUtil):

    @staticmethod
    def playGame(board, color, **kwargs):
        komi = kwargs.pop('komi', 0)
        limit = kwargs.pop('limit', 1000)
        simulation_policy = kwargs.pop('simulation_policy','random')
        use_pattern = kwargs.pop('use_pattern',True)
        check_selfatari = kwargs.pop('check_selfatari',True)
        if kwargs:
            raise TypeError('Unexpected **kwargs: %r' % kwargs)
        for _ in range(limit):
            if simulation_policy == 'random':
                move = GoBoardUtilGo4.generate_random_move(board,color,True)
            elif simulation_policy == 'rulebased':
                move = GoBoardUtilGo4.generate_move_with_filter(board,use_pattern,check_selfatari)
            else:
                assert simulation_policy == 'probabilistic'
                move = GoBoardUtilGo4.generate_move_with_feature_based_probs(board)
            isLegalMove = board.move(move,color)
            assert isLegalMove
            if board.end_of_game():
                break
            color = GoBoardUtilGo4.opponent(color)
        winner,_ = board.score(komi)
        return winner
            
    @staticmethod
    def generate_moves_with_feature_based_probs(board):
        from feature import Features_weight
        from feature import Feature
        assert len(Features_weight) != 0
        moves = []
        gamma_sum = 0.0
        empty_points = board.get_empty_points()
        color = board.current_player
        probs = np.zeros(board.maxpoint)
        all_board_features = Feature.find_all_features(board)
        for move in empty_points:
            if board.check_legal(move, color) and not board.is_eye(move, color):
                moves.append(move)
                probs[move] = Feature.compute_move_gamma(Features_weight, all_board_features[move])
                gamma_sum += probs[move]
        if len(moves) != 0:
            assert gamma_sum != 0.0
            for m in moves:
                probs[m] = probs[m] / gamma_sum
        return moves, probs
    
    @staticmethod
    def generate_move_with_feature_based_probs(board):
        moves, probs = GoBoardUtilGo4.generate_moves_with_feature_based_probs(board)
        if len(moves) == 0:
            return None
        return np.random.choice(board.maxpoint, 1, p=probs)[0]
    
    @staticmethod
    def generate_move_with_feature_based_probs_max(board):
        moves, probs = GoBoardUtilGo4.generate_moves_with_feature_based_probs(board)
        move_prob_tuple = []
        for m in moves:
            move_prob_tuple.append((m, probs[m]))
        return sorted(move_prob_tuple,key=lambda i:i[1],reverse=True)[0][0]
