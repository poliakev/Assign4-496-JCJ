"""
glossary:
    point : int
        coordinate of point on the board
    color : int
        color code of the point represented in interger, 
        imported from board utility
        EMPTY = 0
        BLACK = 1
        WHITE = 2
        BORDER = 3
        FLOODFILL = 4
"""


import numpy as np
import copy
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, FLOODFILL 
import sys
sys.setrecursionlimit(1000000)

class SimpleGoBoard(object):

    def move(self, point, color):
        """
        Play a move on the board.
        Arguments:
        point
        Return:
        color
        """
        previous_pass=self.num_pass
        move_inspection, msg, caps = self._play_move(point,color)
        if not move_inspection:
            return False
        else:
            self.current_player = GoBoardUtil.opponent(color)
            self.moves.append(point)
            self.ko_constraints.append(self.ko_constraint)
            self.captured_stones.append(caps)
            self.pass_record.append(previous_pass)
            self.last2_move = self.last_move
            self.last_move = point
            # update played and captured positions to the empty positions
            if point:
                self._empty_positions.remove(point)
            if caps is not None:
                self._empty_positions.extend(caps)
            return True
                
    # Undo and restore the full previous board state
    def undo_move(self):
        assert len(self.moves) != 0
        last_point = self.moves.pop()
        self.ko_constraint = self.ko_constraints.pop()
        caps = self.captured_stones.pop()
        self.num_pass=self.pass_record.pop()
        if last_point != None:
            self.board[last_point] = EMPTY
            self.liberty_dp[last_point] = -1
            self._empty_positions.append(last_point)
            c = self.current_player
            for p in caps:
                self.board[p] = c
                self._empty_positions.remove(p)
        self.current_player = GoBoardUtil.opponent(self.current_player);

    @staticmethod
    def showboard(board,bd_size):
        #TODO: would be nice to have a nicer printout of the board
        pass

    def get_color(self, point):
        """
        Return the state of the specified point.
        Arguments:
            point
        Return:
            color
        """
        return self.board[point]

    def check_legal(self,point,color):
        """
        Arguments:
            point, color
        Return:
            bool
            Whether the playing point with the given color is
            legal.
        """
        if point == None: #play a pass move
            return True
        if self.board[point] != EMPTY:
            return False
        if point == self.ko_constraint:
            return False
        # tentatively place the stone and check capture and suicide
        self.board[point] = color
        neighbors = self._neighbors(point)
        opp = GoBoardUtil.opponent(color)
        for n in neighbors:
            assert self.board[n] != BORDER
            if self.board[n] == opp:
                hasLiberty,fboard = self._liberty_flood(n)
                if not hasLiberty:
                    self.board[point] = EMPTY
                    return True
        is_legal = (not self.check_suicide) or self._liberty_flood(point)[0]
        # remove the stone again
        self.board[point] = EMPTY
        return is_legal

    def get_twoD_board(self):
        """
        Return: numpy array
        a two dimensional numpy array with same values as in 
        self.board but without the borders
        """
        board = np.zeros((self.size,self.size),dtype=np.int32)
        for i in range(self.size):
            row = (i+1)*self.NS + 1
            board[i,:] = self.board[row:row+self.size]
        return board

    def __init__(self, size):
        """
        Creates a board that uses 1-dimensional representaion for points
        ----------
        This board has the following functionalities:
            1. move :plays a move at given point
            2. TODO document the rest
        """
        # initialize using reset since it would be the same code as in __init__
        self.reset(size)


    def reset(self, size):
        """
            Creates an initial board position
            reset the board to a new size
            
            Arguments
            ---------
            size : int
            size of board to reset to
            """
        
        self.name = "Board 1D"
        self.version = 0.1
        self.size = size
        self.NS = size + 1
        self.WE=  1
        self.check_suicide = True
        self._is_empty = True
        self.ko_constraint = None
        self.passes_white = 0
        self.passes_black = 0
        self.white_captures = 0
        self.black_captures = 0
        self.current_player= BLACK
        self.winner = None
        self.num_pass = 0
        self.maxpoint = size*size + 3*(size+1)  
        self.liberty_dp = np.ones((self.maxpoint),dtype=np.int16)*-1
        self.moves = [] # stack of moves
        self.ko_constraints = [] # stack of ko constraines
        self.captured_stones = [] # stacke of captured stones
        self.pass_record = []
        self.last_move = None
        self.last2_move = None

        """
        The board array is one-dimensional 
        Conversion from row, col format: see _coord_to_point function
        This is an example point numbering (indices of numpy array)
        on a 3x3 board. Spaces are added for illustration to separate 
        board points from border points.
        There is only a one point buffer between each row (e.g. point 12).
        
        16   17 18 19   20
        
        12   13 14 15   16
        08   09 10 11   12
        04   05 06 07   08
        
        00   01 02 03   04
        
        This is the content of the array after initialization,
        if we copy it into a 2d array with padding.
        Codes are EMPTY = 0, BORDER = 3
        [ 3, 3, 3, 3, 3, 0, 0, 0, 3, 0, 0, 0, 3, 0, 0, 0, 3, 3, 3, 3, 3]
        
        3  3  3  3  3
        3  0  0  0  3
        3  0  0  0  3
        3  0  0  0  3
        3  3  3  3  3
        """
        self.board = np.ones((self.maxpoint),dtype=np.int16)*BORDER
        self._empty_filling(self.board)
        self._empty_positions = list(np.where(self.board == 0)[0])
        # Init neighbors dict
        self.neighbors_dic = {}
        for p in self._empty_positions:
            self.neighbors_dic[p] = []
            for n in self._neighbor_pos(p):
                if self.board[n] == BORDER:
                    continue
                self.neighbors_dic[p].append(n)

    def _neighbors(self,point):
        return self.neighbors_dic[point]
    
    def _neighbor_pos(self, point):
        return [point-1, point+1, point-self.NS, point+self.NS]

    def copy(self):
        """Return an independent copy of this Board."""
        copy_board = SimpleGoBoard(self.size)
        copy_board.__dict__ = copy.deepcopy(self.__dict__)
        assert copy_board.board.all() == self.board.all()
        return copy_board

    def get_empty_points(self):
        """
        Argumnets:
        color
        This function return a list of empty positions
        Return:
        list of empty poisitions
        """
        return self._empty_positions[:]

    def _empty_filling(self,board):
        """
        Fills points inside board with EMPTY
        Arguments
        ---------
        board : numpy array
            receives a numpy array filled with BORDER

        """
        for ind in range(1,self.size+1,1):
            indices = [j for j in range(ind*self.NS + 1,ind*self.NS+self.size+1,1)]
            np.put(board,indices, EMPTY)


    def is_eye(self,point,color):
        """
        Is eyeish can detect diamond shape around a point if that fails we know that is not an eye
        Arguments
        ---------
        point, color

        Return
        ---------
            eye color or None
            whether the point with given color is inside an eye
        This function is based on https://github.com/pasky/michi/blob/master/michi.py --> is_eye
        """
        eye_color = self._is_eyeish(point)
        if eye_color != color:
            return None
        if eye_color == None:
            return None
        # Eye-like shape, but it could be a false eye
        false_color = GoBoardUtil.opponent(eye_color)
        false_count = 0
        at_edge = False
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = True
            elif self.board[d] == false_color:
                false_count += 1
        if at_edge:
            false_count += 1
        if false_count >= 2:
            return None
        return eye_color
    
    """
    ----------------------------------------------------------------------------------------------------------------------
    helper functions for playing a move!
    ----------------------------------------------------------------------------------------------------------------------
    """
    def _is_eyeish(self,point):
        """
        returns whether the position is empty and is surrounded by 
        all stones of the same color.
        Arguments
        ---------
        point

        Return
        ---------
        bool:
             whether the neighbors of the point all have same color
        This is based on https://github.com/pasky/michi/blob/master/michi.py --> is_eyeish
        
        """
        eye_color = None
        for n in self._neighbors(point):
            if self.board[n] == BORDER:
                continue
            if self.board[n] == EMPTY:
                return None
            if eye_color == None:
                eye_color = self.board[n]
            else:
                if self.board[n] != eye_color:
                    return None
        return eye_color
    
    def _single_liberty(self, point, color):
        """
        This functions returns point that is last liberty of a point
        """
        _, point = self._liberty_point(point,color)
        return point

    def _liberty(self, point, color):
        """
        ---------
        Return
        ---------
        liberty: int
             Number of liberty that the given point has
        """
        num_lib, _ = self._liberty_point(point, color)
        return num_lib


    def _liberty_point(self, point, color):
        """
        Helper function for returning number of liberty and 
        last liberty for the point
        """
        group_points = [point]
        liberty = 0
        met_points = [point]
        while group_points:
            p=group_points.pop()
            met_points.append(p)
            neighbors = self._neighbors(p)
            for n in neighbors:
                if n not in met_points:
                    assert self.board[n] != BORDER
                    if self.board[n] == color: 
                        group_points.append(n)
                    elif self.board[n]==EMPTY:
                        liberty += 1
                        single_lib_point = n
                    met_points.append(n)
        if liberty == 1:
            return liberty, single_lib_point
        return liberty, None

    def _liberty_flood_rec(self,fboard,point,color):
        fboard[point] = FLOODFILL
        neighbors = self._neighbors(point)
        for n in neighbors:
            if fboard[n] == EMPTY:
                return True,n
            if fboard[n] == color:
                res,lp=self._liberty_flood_rec(fboard,n,color)
                if res:
                    return True, lp
        return False, None

    def _liberty_flood(self, point):
        """
        This function find the liberties of flood filled board.
        return True if it finds any liberty and False otherwise
        Arguments
        ---------
        board : numpy array

        Return
        ---------
        bool:
             whether the flood filled group in the board has any liberty
        """
        dp_point=self.liberty_dp[point]
        if dp_point != -1 and self.board[dp_point] == EMPTY:
            return True, dp_point
        fboard = np.array(self.board, copy=True)
        color = fboard[point]
        res,lp = self._liberty_flood_rec(fboard,point,color)
        if(res==True):
            return res, lp
        else:
            return res, fboard


    def _flood_fill(self, point):
        """
        Creates a new board and fills the connected groups to the given point
        Arguments
        ---------
        point

        Return
        ---------
         a new board with points in the neighbor of given point 
         with same color replaced with
         FLOODFILL(=4)
         This is based on https://github.com/pasky/michi/blob/master/michi.py --> floodfill
        """
        fboard = np.array(self.board, copy=True)
        pointstack = [point]
        color = fboard[point]
        fboard[point] = FLOODFILL
        while pointstack:
            current_point = pointstack.pop()
            neighbors = self._neighbors(current_point)
            for n in neighbors :
                if fboard[n] == color:
                    fboard[n] = FLOODFILL
                    pointstack.append(n)
        return fboard


    def _play_move(self, point, color):
        """
            This function is for playing the move
            Arguments
            ---------
            point, color
            
            Return
            ---------
            State of move and appropriate message for that move
            """
        
        if point == None: #play a pass move
            msg = "Playing a pass move with %s color is permitted"%(color)
            self.num_pass += 1
            game_ended = self.end_of_game()
            if game_ended:
                return True, "Game has ended!", None
            return True, msg, None
        self.num_pass = 0
        if self.board[point] != EMPTY:
            c = self._point_to_coord(point)
            msg = "Row and Column: %d %d is already filled with a %s stone"%(c[0], c[1], GoBoardUtil.int_to_color(color))
            return False, msg, None
        if point == self.ko_constraint:
            msg ="KO move is not permitted!"
            return False , msg, None
        in_enemy_eye = self._is_eyeish(point) == GoBoardUtil.opponent(color)
        self.board[point] = color
        self._is_empty = False
        caps = []
        single_captures = []
        neighbors = self._neighbors(point)
        cap_inds = None
        for n in neighbors:
            assert self.board[n] != BORDER
            if self.board[n] != color:
                if self.board[n] != EMPTY:
                    hasLiberty, fboard = self._liberty_flood(n)
                    if not hasLiberty:
                        cap_inds = fboard==FLOODFILL
                        caps.extend(list(*np.where(fboard==FLOODFILL)))
                        num_captures = np.sum(cap_inds)
                        if num_captures == self.size*self.size:
                            self._is_empty = True
                        if num_captures == 1:
                            single_captures.append(n)
                        if color == WHITE:
                            self.white_captures += num_captures
                        else :
                            self.black_captures += num_captures
                        self.liberty_dp[cap_inds] = -1
                        self.board[cap_inds] = EMPTY
        self.ko_constraint = single_captures[0] if in_enemy_eye and len(single_captures) == 1 else None
        if (not self.check_suicide):
            #not check suicidal move
            c = self._point_to_coord(point)
            msg = "Playing a move with %s color in the row and column %d %d is permitted"%(color,c[0],c[1])
            return True, msg, caps
        else:
            res,lp=self._liberty_flood(point)
            if res==True:
                #non suicidal move
                self.liberty_dp[point]=lp
                c = self._point_to_coord(point)
                msg = "Playing a move with %s color in the row and column %d %d is permitted"%(color,c[0],c[1])
                return True, msg, caps
            else:
                # undoing the move because of being suicidal
                # think cap_inds must be None?
                self.board[point] = EMPTY
                if cap_inds!= None:
                    self.board[cap_inds] = GoBoardUtil.opponent(color)
                c = self._point_to_coord(point)
                msg = "Suicide move with color %s in the row and column: %d %d "%(color, c[0],c[1])
                return False, msg, None
    
    def _diag_neighbors(self, point):
        """
        All diagonal neighbors of the point
        Arguments
        ---------
        point

        Returns
        -------
        points : list of int
            coordinate of points which are diagnoal neighbors of the given point
        """
        return [point-self.NS-1, point-self.NS+1,
                point+self.NS-1, point+self.NS+1]

    def _border_removal(self, points):
        """
        Removes Border points from a list of points received as Input and Return the result
        as a list
        Arguments
        ---------
        points : list of int
            coordinate of points on the board

        Returns
        -------
        points : list of int
            coordinate of points on the board
        """
        coords = [self._point_to_coord(p) for p in points]
        coords = np.reshape(coords,(-1,2))
        ind = 0
        removal = []
        for c in coords:
            b1 = c==0
            b2 = c==self.size+1
            if b1.any() or b2.any():
                removal.append(ind)
            ind += 1
        removal = np.unique(removal)
        return list(np.delete(points,removal))

    def _on_board(self, point):
        """
        returns True if point is inside the board and not on the borders.
        Arguments
        ---------
        point

        Returns
        -------
         bool
        """
        return self.board[point] != BORDER


    def _points_color(self,point):
        """
        Return the state of the specified point.

        Arguments
        ---------
        point

        Returns
        -------
         color: string
                 color representing the specified point .
        """
        p_int_color = self.board[point]
        return GoBoardUtil.int_to_color(p_int_color)

    def _coord_to_point(self,row,col):
        """
        Transform two dimensional point coordinates to 1d board index.

        Arguments
        ---------
         x , y : int
                 coordinates of the point  1 <= x, y <= size

        Returns
        -------
        point
        """
        if row <0 or col < 0:
            raise ValueError("Wrong coordinates, Coordinates should be larger than 0")
        return self.NS*row + col

    def _point_to_coord(self, point):
        """
        Transform point index to row, col.

        Arguments
        ---------
        point

        Returns
        -------
        x , y : int
            coordination of the board  1<= x <=size, 1<= y <=size .
        """
        if point is None:
            return 'pass'
        row, col = divmod(point, self.NS)
        return row, col

    def end_of_game(self):
        # in the command line one can do multiple pass consecutively, to have the
        # function return correct output we check for greater equal
        return self.num_pass >= 2

    def score(self, komi):
        """ Score """
        black_score = 0
        white_score = komi
        counted = []
        for x in range(1, self.size+1):
            for y in range(1, self.size+1):
                point = self._coord_to_point(x,y)
                if point in counted:
                    continue
                color = self.get_color(point)
                assert color != BORDER
                if color == BLACK:
                    black_score += 1
                    continue
                if color == WHITE:
                    white_score += 1
                    continue
                fboard = self._flood_fill(point)
                empty_block = list(*np.where(fboard == FLOODFILL))
                black_flag = False
                white_flag = False
                for p in empty_block:
                    counted.append(p)
                    p_neighbors = self._neighbors(p)
                    found_black = self.board[p_neighbors]==BLACK
                    found_white = self.board[p_neighbors]==WHITE
                    if found_black.any():
                        black_flag = True
                    if found_white.any():
                        white_flag = True
                    if black_flag and white_flag:
                        break
                if black_flag and not white_flag:
                    black_score += len(empty_block)
                if white_flag and not black_flag:
                    white_score += len(empty_block)
    
        if black_score > white_score:
            return BLACK, black_score-white_score

        if white_score > black_score:
            return WHITE, white_score-black_score
        
        if black_score == white_score:
            return None, 0

    """
    We implement a simplified version of Benson's algorithm 
    to determine which stones are safe.
    Given a board and a color, the algorithm could determine 
    for the input color of player, which
    blocks of stones are safe on the board.
    
    Please refer to https://en.wikipedia.org/wiki/Benson%27s_algorithm_(Go)
    and https://senseis.xmp.net/?BensonsAlgorithm
    
    Let S be the set of all blocks of stones.
    Let E be the set of all one point eyes.
    
    The algorithm has two parts:
    
    1. find S and E (the find_S_and_E function)
    
    2. For each s in S, if it connects to less than 2 one point eyes in E, 
       then remove s from S, as well as its connected one point eye (if any)
       from E. Continue this process until no change can be made
       (the find_safety function)
    
    Note that this is only a simplifed version, since E only contains 
    the one point eyes. You can implement the full version of Benson's 
    algorithm based on the links we provided above.
    """
    def find_S_and_E(self, color):
        """
        This function finds S and E sets for the safety check
        S: set of all blocks
        E: set of all one point eyes
        """
        E = {} # For each one point eye, record the blocks it connects
        S = {} # Each block is indexed by its anchor, which is the 
               # smallest point in the block
        S_eyes = {} # For each block, record one point eyes it connects
        
        # find E
        empty_points = self.get_empty_points()
        for point in empty_points:
            if self.is_eye(point, color):
                E[point] = set()
    
        # find S
        anchor_dic = {}
        for x in range(1, self.size+1):
            for y in range(1, self.size+1):
                point = self._coord_to_point(x,y)
                if self.get_color(point) != color:
                    continue
                if point in anchor_dic:
                    continue
                stack_points = [point]
                block_points = [point]
                min_index = point
                one_point_eyes = set()
                while stack_points:
                    current_point = stack_points.pop()
                    neighbors = self._neighbors(current_point)
                    for n in neighbors :
                        if n not in block_points:
                            if self.get_color(n) == BORDER:
                                continue
                            if self.get_color(n) == color:
                                stack_points.append(n)
                                block_points.append(n)
                                if n < min_index:
                                    min_index = n
                            if n in E:
                                one_point_eyes.add(n)
                for p in block_points:
                    anchor_dic[p] = min_index
                S_eyes[min_index] = one_point_eyes
                for e in one_point_eyes:
                    assert e in E
                    E[e].add(min_index)
                S[min_index] = block_points
        return S, E, S_eyes

    def find_safety(self, color):
        """
        This function implements a simplified version of 
        Benson's algorithm for unconditional safety.
        S: set of all blocks
        E: set of all one point eyes
        For each s in S, if it connects to less than 2 one point eyes in E,
        then remove s from S, as well as its connected one point eye (if any)
        from E. Continue this process until no change can be made.
        """
        safety_list = []
        S, E, S_eyes = self.find_S_and_E(color)
        while True:
            change = False
            for s in S:
                if len(S_eyes[s]) < 2:
                    change = True
                    # Remove s from S, as well as its connected one point eye
                    for e in S_eyes[s]:
                        for block in E[e]:
                            if block != s:
                                S_eyes[block].remove(e)
                        E.pop(e)
                    S.pop(s)
                    S_eyes.pop(s)
                    break
            if not change:
                break
        for s in S:
            safety_list.extend(S[s])
        for e in E:
            safety_list.append(e)
        return safety_list

    def neighborhood_33(self,point):
        """
        Get the pattern around point.
        Returns
        -------
        patterns :
        Set of patterns in the same format of what michi pattern base provides. Please refer to pattern.py to see the format of the pattern.
        """
        positions = [point-self.NS-1, point-self.NS, point-self.NS+1,
                     point-1, point, point+1,
                     point+self.NS-1, point+self.NS, point+self.NS+1]
                     
        pattern = ""
        for d in positions:
            if self.board[d] == self.current_player:
                pattern += 'X'
            elif self.board[d] == GoBoardUtil.opponent(self.current_player):
                pattern += 'x'
            elif self.board[d] == EMPTY:
                pattern += '.'
            elif self.board[d] == BORDER:
                pattern += ' '
        return pattern
    
    def last_moves_empty_neighbors(self):
        """
        Get the neighbors of last_move and second last move. 
        This function is based on code in
        https://github.com/pasky/michi/blob/master/michi.py
        
        Returns
        -------
        points :
        points which are neighbors of last_move and last2_move
        """
        nb_list = []
        for c in self.last_move, self.last2_move:
            if c is None:  continue
            nb_of_c_list = list(self._neighbors(c) + self._diag_neighbors(c))
            nb_list += [d for d in nb_of_c_list if self.board[d] == EMPTY and d not in nb_list]
        return nb_list

    def point_to_string(self, point):
        if point == None:
            return 'Pass'
        x, y = GoBoardUtil.point_to_coord(point, self.NS)
        return GoBoardUtil.format_point((x, y))

