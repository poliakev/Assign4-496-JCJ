# Cmput 496 sample code
# UCB algorithm
# Written by Martin Mueller

from math import log,sqrt
import sys

INFINITY = float('inf')

def mean(stats, i):
    return stats[i][0] / stats[i][1]
    
def ucb(stats, C, i, n):
    if stats[i][1] == 0:
        return INFINITY
    return mean(stats, i)  + C * sqrt(log(n) / stats[i][1])

def findBest(stats, C, n):
    best = -1
    bestScore = -INFINITY
    for i in range(len(stats)):
        score = ucb(stats, C, i, n) 
        if score > bestScore:
            bestScore = score
            best = i
    assert best != -1
    return best

def bestArm(stats): # Most-pulled arm
    best = -1
    bestScore = -INFINITY
    for i in range(len(stats)):
        if stats[i][1] > bestScore:
            bestScore = stats[i][1]
            best = i
    assert best != -1
    return best

# tuple = (move, percentage, wins, pulls)
def byPercentage(tuple):
    return tuple[1]

# tuple = (move, percentage, wins, pulls)
def byPulls(tuple):
    return tuple[3]

def writeMoves(board, moves, stats):
    moves_strings = []
    for i in range(len(moves)):
        pointString = board.point_to_string(moves[i])
        if stats[i][1] != 0:
            moves_strings.append((pointString,
                          stats[i][0]/stats[i][1],
                          stats[i][0],
                          stats[i][1]))
        else:
            moves_strings.append((pointString,
              0.0,
              stats[i][0],
              stats[i][1]))
    sys.stderr.write("Statistics: {}\n"
                     .format(sorted(moves_strings, key = byPulls,
                                               reverse = True)))
    sys.stderr.flush()

def runUcb(player, board, cboard, C, moves, toplay):
    stats = [[0,0] for _ in moves]
    num_simulation = len(moves) * player.num_simulation
    for n in range(num_simulation):
        moveIndex = findBest(stats, C, n)
        result = player.simulate(board, cboard, moves[moveIndex], toplay)
        if result == toplay:
            stats[moveIndex][0] += 1 # win
        stats[moveIndex][1] += 1
    bestIndex = bestArm(stats)
    best = moves[bestIndex]
    writeMoves(board, moves, stats)
    return best

