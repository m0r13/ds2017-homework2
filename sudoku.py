#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import copy
import random

SUDOKU_TEMPLATE = [
    [7, 2, 6, 4, 9, 3, 8, 1, 5],
    [3, 1, 5, 7, 2, 8, 9, 4, 6],
    [4, 8, 9, 6, 5, 1, 2, 3, 7],
    [8, 5, 2, 1, 4, 7, 6, 9, 3],
    [6, 7, 3, 9, 8, 5, 1, 2, 4],
    [9, 4, 1, 3, 6, 2, 7, 5, 8],
    [1, 9, 4, 8, 3, 6, 5, 7, 2],
    [5, 6, 7, 2, 1, 4, 3, 8, 9],
    [2, 3, 8, 5, 7, 9, 4, 6, 1],
]

class Sudoku():
    """Represents the sudoku itself, keeps track of the filling
    and check if moves are legal
    """
    
    def __init__(self, num_zeros=20):
        self.__game_grid, self.__finished_grid = Sudoku.generate_grid(num_zeros)
        #...
    
    def insert(self, i, j, number):
        """Insert number into sudoku
        :param number, int from 1-9
        :param coordinate tuple (x, y)
        :returns tuple (point, finish) 
                 point, int from -1 to 1
                 -1 -> False
                 0 -> already full coord.
                 1 -> True
                 
                 finish, boolean
        """
        if self.__game_grid[i][j] == 0:
            if self.check_if_legal(i, j, number):
                self.__game_grid[i][j] = number
                point = 1 
            else:
                point = -1
        else:
            point = 0    
            
        return point, self.check_if_finished()

    def get_grid(self):
        return self.__game_grid
    
    def check_if_legal(self, i, j, number):
        return self.__finished_grid[i][j] == number
    
    def check_if_finished(self):
        return self.__game_grid == self.__finished_grid

    def serialize(self):
        serialized = []
        for i in range(9):
            serialized.extend(self.__game_grid[i])
        return serialized
    
    @staticmethod
    def get_random_sudoku():
        f = open("sudoku.txt", "r")
        f.seek(random.randint(0, 9999) * 83, 0)
        line = f.readline()
        s = [i for i in line]
        s = s[:-2]
        sudoku=[]
        count = 0
        for i in range(0, 9):
            row = []
            for j in range(0, 9):
                row.append(s[count])
                count += 1
            sudoku.append(row)
        f.close()
        return sudoku 
    
    @staticmethod
    def generate_grid(num_zeros):
        """generate a sudoku grid
        :returns tuple (game_grid, finished_grid)
                start_grid, [9][9]
                full_grid, [9][9]
        """
        finished_grid = get_random_sudoku()
        game_grid = copy.deepcopy(finished_grid)
        coords = []
        for i in range(9):
            for j in range(9):
                coords.append((i, j))
        random.shuffle(coords)
        for i, j in coords[:num_zeros]:
            game_grid[i][j] = 0
        return game_grid, finished_grid

