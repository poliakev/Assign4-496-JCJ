"""
Module for playing games of Go using GoTextProtocol

This code is based off of the gtp module in the Deep-Go project
by Isaac Henrion and Aamos Storkey at the University of Edinburgh.
"""
import traceback
import sys
import os
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, FLOODFILL
import numpy as np
import re

class GtpConnection():

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
        mode='w'
        self.stdout = sys.stdout
        #sys.stdout = outfile
        self._debug_mode = debug_mode
        self.file = open(outfile, mode)
        #self.stderr = sys.stderr
        sys.stdout = self
        self.go_engine = go_engine 
        self.go_engine.komi = 0.5
        self.board = board
        self.in_tree_knowledge_options = ["probabilistic" ]
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "set_free_handicap": self.set_free_handicap,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "score": self.score_cmd,
            "final_score": self.score_cmd,
            "legal_moves": self.legal_moves_cmd,
            "legal_moves_for_toPlay": self.legal_moves_for_toPlay_cmd,
            "policy_moves": self.policy_moves_cmd,
            "random_moves": self.random_moves_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd,
            "selfatari": self.selfatari_cmd,
            "use_pattern": self.use_pattern_cmd,            
            "random_simulation": self.random_simulation_cmd,
            "use_ucb": self.use_ucb_cmd,
            "num_total_sim": self.num_sim_cmd,
            "in_tree_knowledge": self.int_tree_knowledge_cmd,
            "mcts_info": self.mcts_info_cmd
        }

        # used for argument checking
        # values: (required number or arguments, error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "set_free_handicap": (1, 'Usage: set_free_handicap MOVE (e.g. A4)'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            "play": (2, 'Usage: play {b,w} MOVE'),
            "legal_moves": (1, 'Usage: legal_moves {w,b}'),
            "selfatari":(1, 'Usage: selfatari INT'),
            "use_pattern":(1, 'Usage: use_pattern INT'),
            "random_simulation":(1, 'Usage: random_simulation INT'),
            "use_ucb":(1, 'Usage: use_ucb INT'),
            "num_total_sim":(1,'Usage: num_total_sim #(e.g. num_total_sim 100 )'),            
            "in_tree_knowledge": (1,'Usage: in_tree_knowledge {0}'.format(' '.join(*self.in_tree_knowledge_options))),

        }
    
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data) 

    def flush(self,):
        self.stdout.flush()
        self.file.flush()

    def start_connection(self):
        """
        start a GTP connection. This function is what continuously monitors the user's
        input of commands.
        """
        self.debug_msg("Start up successful...\n\n")
        line = sys.stdin.readline()
        while line:
            self.get_cmd(line)
            line = sys.stdin.readline()

    def get_cmd(self, command):
        """
        parse the command and execute it

        Arguments
        ---------
        command : str
            the raw command to parse/execute
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]; args = elements[1:]
        if self.arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            sys.stdout.flush()

    def arg_error(self, cmd, argnum):
        """
        checker function for the number of arguments given to a command

        Arguments
        ---------
        cmd : str
            the command name
        argnum : int
            number of parsed argument

        Returns
        -------
        True if there was an argument error
        False otherwise
        """
        if cmd in self.argmap and self.argmap[cmd][0] > argnum:
                self.error(self.argmap[cmd][1])
                return True
        return False

    def debug_msg(self, msg=''):
        """ Write a msg to the debug stream """
        if self._debug_mode:
            sys.stderr.write(msg); sys.stderr.flush()

    def error(self, error_msg=''):
        """ Send error msg to stdout and through the GTP connection. """
        sys.stdout.write('? {}\n\n'.format(error_msg)); sys.stdout.flush()

    def respond(self, response=''):
        """ Send msg to stdout """
        sys.stdout.write('= {}\n\n'.format(response)); sys.stdout.flush()

    def reset(self, size):
        """
        Resets the state of the GTP to a starting board

        Arguments
        ---------
        size : int
            the boardsize to reinitialize the state to
        """
        self.board.reset(size)
        if self.go_engine.name == 'Go5':
            self.go_engine.reset() 

    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the player """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the player """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game and initialize with a new boardsize

        Arguments
        ---------
        args[0] : int
            size of reinitialized board
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args):
        self.respond('\n' + str(self.board.get_twoD_board()))

    def komi_cmd(self, args):
        """
        Set the komi for the game

        Arguments
        ---------
        args[0] : float
            komi value
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if a command is known to the GTP interface

        Arguments
        ---------
        args[0] : str
            the command name to check for
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    def set_free_handicap(self, args):
        """
        clear the board and set free handicap for the game

        Arguments
        ---------
        args[0] : str
            the move to handicap (e.g. B2)
        """
        self.board.reset(self.board.size)
        for point in args:
            move = GoBoardUtil.move_to_coord(point, self.board.size)
            point = self.board._coord_to_point(*move)
            if not self.board.move(point, BLACK):
                self.debug_msg("Illegal Move: {}\nBoard:\n{}\n".format(move, str(self.board.get_twoD_board())))
        self.respond()

    def legal_moves_for_toPlay_cmd(self, args):
        try:
            color= self.board.current_player
            moves=GoBoardUtil.generate_legal_moves(self.board,color)
            self.respond(moves)
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

    def legal_moves_cmd(self, args):
        """
        list legal moves for the given color
        Arguments
        ---------
        args[0] : {'b','w'}
            the color to play the move as
            it gets converted to  Black --> 1 White --> 2
            color : {0,1}
            board_color : {'b','w'}
        """
        try:
            board_color = args[0].lower()
            color= GoBoardUtil.color_to_int(board_color)
            moves=GoBoardUtil.generate_legal_moves(self.board,color)
            self.respond(moves)
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

    def score_cmd(self, args):
        komi = self.go_engine.komi
        winner, score = self.board.score(komi)
        if winner == BLACK:
            result = "B+{}".format(score)
        if winner == WHITE:
            result = "W+{}".format(score)
        if winner is None:
            result="0"
        self.respond(result)

    def selfatari_cmd(self, args):
        valid_values = [0,1]
        value = int(args[0])
        if value not in valid_values:
            self.error('Argument ({}) must be 0 or 1'.format(value))
        else:
            self.go_engine.check_selfatari = value 
        self.respond()

    def use_pattern_cmd(self, args):
        valid_values = [0,1]
        value = int(args[0])
        if value not in valid_values:
            self.error('Argument ({}) must be 0 or 1'.format(value))
        else:
            self.go_engine.use_pattern = value 
        self.respond()

    def use_ucb_cmd(self, args):
        valid_values = [0,1]
        value = int(args[0])
        if value not in valid_values:
            self.error('Argument ({}) must be 0 or 1'.format(value))
        else:
            self.go_engine.use_ucb = value 
        self.respond()

    def random_simulation_cmd(self, args):
        valid_values = [0,1]
        value = int(args[0])
        if value not in valid_values:
            self.error('Argument ({}) must be 0 or 1'.format(value))
        else:
            self.go_engine.random_simulation = value 
        self.respond()

    def num_sim_cmd(self, args):
        self.go_engine.num_simulation = int(args[0])
        self.respond()

    def play_cmd(self, args):
        """
        play a move as the given color

        Arguments
        ---------
        args[0] : {'b','w'}
            the color to play the move as
            it gets converted to  Black --> 1 White --> 2
            color : {0,1}
            board_color : {'b','w'}
        args[1] : str
            the move to play (e.g. A5)
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            color= GoBoardUtil.color_to_int(board_color)
            if args[1].lower()=='pass':
                self.debug_msg("Player {} is passing\n".format(args[0]))
                self.board.move(None, color)
                self.board.current_player = GoBoardUtil.opponent(color)
                self.respond()
                return
            move = GoBoardUtil.move_to_coord(args[1], self.board.size)
            if move:
                move = self.board._coord_to_point(move[0],move[1])
            # move == None on pass
            else:
                self.error("Error in executing the move %s, check given move: %s"%(move,args[1]))
                return
            if not self.board.move(move, color):
                self.respond("Illegal Move: {}".format(board_move))
                return
            else:
                self.debug_msg("Move: {}\nBoard:\n{}\n".format(board_move, str(self.board.get_twoD_board())))
            self.respond()
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

    def genmove_cmd(self, args):
        """
        generate a move for the specified color

        Arguments
        ---------
        args[0] : {'b','w'}
            the color to generate a move for
            it gets converted to  Black --> 1 White --> 2
            color : {0,1}
            board_color : {'b','w'}
        """
        try:
            board_color = args[0].lower()
            color = GoBoardUtil.color_to_int(board_color)
            self.debug_msg("Board:\n{}\nko: {}\n".format(str(self.board.get_twoD_board()),
                                                          self.board.ko_constraint))
            move = self.go_engine.get_move(self.board, color)
            if move is None:
                self.respond("pass")
                return

            if not self.board.check_legal(move, color):
                move = self.board._point_to_coord(move)
                board_move = GoBoardUtil.format_point(move)
                self.respond("Illegal move: {}".format(board_move))
                raise RuntimeError("Illegal move given by engine")

            # move is legal; play it
            self.board.move(move,color)

            self.debug_msg("Move: {}\nBoard: \n{}\n".format(move, str(self.board.get_twoD_board())))
            move = self.board._point_to_coord(move)
            board_move = GoBoardUtil.format_point(move)
            self.respond(board_move)
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))
            raise

    def policy_moves_cmd(self, args):
        """
        Return list of policy moves for the current_player of the board
        """
        policy_moves, type_of_move = GoBoardUtil.generate_all_policy_moves(self.board,
                                                        self.go_engine.use_pattern,
                                                        self.go_engine.check_selfatari)
        if len(policy_moves) == 0:
            self.respond("Pass")
        else:
            response = type_of_move + " " + GoBoardUtil.sorted_point_string(policy_moves, self.board.NS)
            self.respond(response)

    def random_moves_cmd(self, args):
        """
        Return list of random moves (legal, but not eye-filling)
        """
        moves = GoBoardUtil.generate_random_moves(self.board, True)
        if len(moves) == 0:
            self.respond("Pass")
        else:
            self.respond(GoBoardUtil.sorted_point_string(moves, self.board.NS))

    def gogui_analyze_cmd(self, args):
        try:
            self.respond("pstring/Legal Moves For ToPlay/legal_moves_for_toPlay\n"
                         "pstring/Policy Moves/policy_moves\n"
                         "pstring/Random Moves/random_moves\n"
                         )
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))
    
    def int_tree_knowledge_cmd(self, args):
        value = args[0]
        if (value not in self.in_tree_knowledge_options):
            self.error('Argument ({0}) value must be in: {1} '.format(value,' '.join(*self.in_tree_knowledge_options)))
        else:
            self.go_engine.in_tree_knowledge = value
        self.respond()

    def mcts_info_cmd(self, args):
        try:
            root = self.go_engine.parent
            if not root:
                self.respond("No avaiable MCTS tree")
                return
            nodesAtDepth = self.go_engine.get_node_depth(root)
            output="\n"
            prev_nodes = 1
            for i, count in enumerate(nodesAtDepth):
                if count == 0:
                    break
                output += "Nodes at depth {}: {}, effective branching factor: {:.2}\n".format(i, count, count / prev_nodes)
                prev_nodes = count
            sys.stderr.write('{}\n'.format(output))
            sys.stderr.flush()
            self.respond()
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

